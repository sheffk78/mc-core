#!/usr/bin/env bash
# atlas-warmup.sh — Keeps all local Ollama models loaded during waking hours.
# Sends a single-token request ('Hi') every 25 minutes between 6 AM and 10 PM Mountain.
# The models unload after 30 min of inactivity (OLLAMA_KEEP_ALIVE=30m), so pinging
# every 25 min keeps them warm. Outside 6 AM–10 PM the script does nothing.
#
# Installed as a launchd agent: com.openclaw.atlas-warmup (StartInterval=1500)
# Logs: /Users/socializerender/.openclaw/workspace/SYSTEM/logs/atlas-warmup.log
#
set -uo pipefail

# --- Paths & config ---
LOG_DIR="/Users/socializerender/.openclaw/workspace/SYSTEM/logs"
LOG_FILE="${LOG_DIR}/atlas-warmup.log"
STATE_DIR="/Users/socializerender/.openclaw/workspace/SYSTEM/state"
FAIL_COUNT_FILE="${STATE_DIR}/atlas-warmup.fail-count"
OLLAMA_URL="http://127.0.0.1:11434"
# Models to keep warm: discovered dynamically from Ollama's /api/tags.
# Dedupe by the underlying MODEL BLOB digest (first layer in the manifest), not by
# the manifest digest — alias names for the same blob should not cause duplicate
# warm attempts that fail when VRAM can't hold two copies of the same blob.
# Only warm our 2 production models — skip duplicates, dead tags, and embedding models.
# This prevents wasting time warming mistral-small3.2:24b (deleted) or qwen3.8:27b
# (duplicate of bedrock:latest).
MODELS=("atlas:latest" "bedrock:latest")
DISCORD_WEBHOOK="https://discord.com/api/webhooks/1494550650481016843/YTUK3iCMG8mmubqVTEObbEYhSJyOUFMTksH_0AnCu_3Q5fSko219Oclk4o9PvFXEe3cu"

mkdir -p "${STATE_DIR}"
mkdir -p "${LOG_DIR}"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')
export TIMESTAMP
log() {
    echo "[${TIMESTAMP}] $1" >> "${LOG_FILE}"
}

# --- Time guard: only run between 6:00 and 21:59 (6 AM–10 PM Mountain) ---
HOUR=$(date +%H)
if [ "${HOUR}" -lt 6 ] || [ "${HOUR}" -ge 22 ]; then
    # Outside waking hours — do nothing (silent, no log spam)
    exit 0
fi

# --- Warm up: verify Ollama is alive and the models respond ---
# Per-model failure tracking (separate from global Ollama liveness)
MODEL_FAIL_DIR="${STATE_DIR}/model-fails"
mkdir -p "${MODEL_FAIL_DIR}"

FAIL_COUNT=0
if [ -f "${FAIL_COUNT_FILE}" ]; then
    FAIL_COUNT=$(cat "${FAIL_COUNT_FILE}" | tr -d '[:space:]' || echo 0)
    if ! [[ "${FAIL_COUNT}" =~ ^[0-9]+$ ]]; then
        FAIL_COUNT=0
    fi
fi

SUCCESS=0
# Track the first failing model's details for alerting
ALERT_MODEL=""
ALERT_HTTP_CODE="000"
ALERT_RESPONSE_BODY=""

# Test Ollama /api/tags first (fast liveness check)
HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 10 "${OLLAMA_URL}/api/tags" 2>/dev/null) || HTTP_CODE="000"
if [ "${HTTP_CODE}" != "200" ]; then
    log "FAIL: Ollama liveness check returned HTTP ${HTTP_CODE}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    ALERT_MODEL="${MODELS[0]}"
    ALERT_HTTP_CODE="${HTTP_CODE}"
    ALERT_RESPONSE_BODY=""
else
    # Ollama is up — now verify each model responds
    # Use /api/chat for ALL models — it's more reliable than /api/generate
    # (generate can hang if the model is in a bad state from a prior request)
    #
    # CRITICAL FIX (2026-08-27): Bedrock has only 1 inference slot (-np 1). When it's
    # busy serving a real Hermes request, a warmup ping queues behind it and times
    # out (HTTP 000) — a false positive. Before pinging, check /api/ps: if the model
    # is already loaded in VRAM, it's warm and healthy — skip the inference ping.
    # Only ping if the model is NOT loaded (meaning it was evicted and needs warming).
    is_model_loaded_ps() {
        local model="$1"
        curl -s -m 10 "${OLLAMA_URL}/api/ps" 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for m in data.get('models', []):
        if m.get('name') == '$model':
            sys.exit(0)
    sys.exit(1)
except Exception:
    sys.exit(1)
" 2>/dev/null
    }
    ANY_FAIL=0
    for MODEL_NAME in "${MODELS[@]}"; do
        # If model is already loaded in VRAM, it's warm — skip the ping.
        # This prevents false HTTP 000 when bedrock's single slot is busy.
        if is_model_loaded_ps "${MODEL_NAME}"; then
            log "PASS: Model ${MODEL_NAME} already loaded in VRAM (skipped ping)"
            # Reset per-model failure count on success
            MODEL_FAIL_FILE="${MODEL_FAIL_DIR}/$(echo "${MODEL_NAME}" | tr ':' '_')"
            if [ -f "${MODEL_FAIL_FILE}" ]; then
                rm -f "${MODEL_FAIL_FILE}"
            fi
            continue
        fi

        TMP_RESPONSE=$(mktemp)
        # Bedrock (Qwen 3.8) uses thinking mode and needs 50 tokens (25 thinking + 25 response)
        # and up to 120s (thinking adds ~60s overhead on "Say OK")
        # Atlas (Ministral) works fine with 20 tokens and 60s
        if [ "${MODEL_NAME}" = "bedrock:latest" ]; then
            NUM_PREDICT=50
            PROMPT_TEXT="Say OK"
            HTTP_TIMEOUT=120
        else
            NUM_PREDICT=20
            PROMPT_TEXT="Say OK"
            HTTP_TIMEOUT=60
        fi
        HTTP_CODE=$(curl -sS -o "${TMP_RESPONSE}" -w "%{http_code}" --max-time ${HTTP_TIMEOUT} \
            -X POST "${OLLAMA_URL}/api/chat" \
            -H "Content-Type: application/json" \
            -d "{\"model\":\"${MODEL_NAME}\",\"messages\":[{\"role\":\"user\",\"content\":\"${PROMPT_TEXT}\"}],\"stream\":false,\"options\":{\"num_predict\":${NUM_PREDICT}},\"keep_alive\":\"24h\"}" 2>/dev/null) || HTTP_CODE="000"

        RESPONSE_BODY=$(cat "${TMP_RESPONSE}" 2>/dev/null || echo "")
        rm -f "${TMP_RESPONSE}"

        if [ "${HTTP_CODE}" != "200" ]; then
            log "FAIL: Model ${MODEL_NAME} chat returned HTTP ${HTTP_CODE}"
            # Track per-model failures for targeted recovery
            MODEL_FAIL_FILE="${MODEL_FAIL_DIR}/$(echo "${MODEL_NAME}" | tr ':' '_')"
            MODEL_FAILS=0
            if [ -f "${MODEL_FAIL_FILE}" ]; then
                MODEL_FAILS=$(cat "${MODEL_FAIL_FILE}" | tr -d '[:space:]' || echo 0)
            fi
            MODEL_FAILS=$((MODEL_FAILS + 1))
            echo "${MODEL_FAILS}" > "${MODEL_FAIL_FILE}"
            if [ "${ANY_FAIL}" -eq 0 ]; then
                ALERT_MODEL="${MODEL_NAME}"
                ALERT_HTTP_CODE="${HTTP_CODE}"
                ALERT_RESPONSE_BODY="${RESPONSE_BODY}"
            fi
            ANY_FAIL=1
        elif ! echo "${RESPONSE_BODY}" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    # /api/generate returns {"response": "..."}, /api/chat returns {"message": {"content": "..."}}
    if "response" in data or "message" in data:
        sys.exit(0)
    else:
        print("Missing response/message field")
        sys.exit(1)
except Exception as e:
    print(str(e))
    sys.exit(1)
' 2>/dev/null; then
            log "FAIL: Model ${MODEL_NAME} generate returned non-parseable or empty response"
            if [ "${ANY_FAIL}" -eq 0 ]; then
                ALERT_MODEL="${MODEL_NAME}"
                ALERT_HTTP_CODE="${HTTP_CODE}"
                ALERT_RESPONSE_BODY="${RESPONSE_BODY}"
            fi
            ANY_FAIL=1
        else
            # Success for this model
            log "PASS: Model ${MODEL_NAME} warmed up successfully (HTTP ${HTTP_CODE})"
            # Reset per-model failure count on success
            MODEL_FAIL_FILE="${MODEL_FAIL_DIR}/$(echo "${MODEL_NAME}" | tr ':' '_')"
            if [ -f "${MODEL_FAIL_FILE}" ]; then
                rm -f "${MODEL_FAIL_FILE}"
            fi
        fi
    done

    if [ "${ANY_FAIL}" -eq 0 ]; then
        # All models warmed successfully
        if [ "${FAIL_COUNT}" -gt 0 ]; then
            log "RECOVERY: failure count reset from ${FAIL_COUNT} to 0"
        fi
        FAIL_COUNT=0
        SUCCESS=1
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
fi

# Save fail count for next run (persist between invocations)
echo "${FAIL_COUNT}" > "${FAIL_COUNT_FILE}"

# --- Alerting: after 2 consecutive failures, send Discord webhook ---
if [ "${FAIL_COUNT}" -eq 2 ]; then
    RESPONSE_PREVIEW=$(echo "${ALERT_RESPONSE_BODY}" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(json.dumps(d,indent=2)[:800])' 2>/dev/null || echo "${ALERT_RESPONSE_BODY}" | head -c 800)
    export MODEL_NAME="${ALERT_MODEL}"
    export HTTP_CODE="${ALERT_HTTP_CODE}"
    export RESPONSE_PREVIEW
    python3 <<'PYEOF'
import json, os

msg = f"""🚨 **Ollama Warmup Alert** — {os.environ.get('TIMESTAMP','')}

Model **{os.environ.get('MODEL_NAME','')}** on **{os.uname().nodename}** failed 2 consecutive warmup checks.

- Ollama URL: `{os.environ.get('OLLAMA_URL','')}`
- Last HTTP code: `{os.environ.get('HTTP_CODE','000')}`
- Response snippet:
```
{os.environ.get('RESPONSE_PREVIEW','[empty]')}
```

Next failure (3 total) will trigger an Ollama restart attempt."""

payload = json.dumps({'content': msg[:4000]})
with open('/tmp/atlas-discord-payload.json', 'w') as f:
    f.write(payload)
PYEOF

    if [ -f /tmp/atlas-discord-payload.json ]; then
        WEB_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 15 \
            -X POST "${DISCORD_WEBHOOK}" \
            -H "Content-Type: application/json" \
            -d @/tmp/atlas-discord-payload.json 2>/dev/null) || WEB_HTTP="000"
        if [ "${WEB_HTTP}" = "204" ] || [ "${WEB_HTTP}" = "200" ]; then
            log "ALERT: Discord notification sent (HTTP ${WEB_HTTP})"
        else
            log "WARN: Discord webhook returned HTTP ${WEB_HTTP} (expected 204)"
        fi
        rm -f /tmp/atlas-discord-payload.json
    else
        log "WARN: Failed to build Discord payload"
    fi
fi

# --- Per-model recovery: reload individual failed model ---
# Instead of killing ALL of Ollama (which kills both models), target just the
# failed model. This keeps the healthy model running while recovering the other.
if [ "${FAIL_COUNT}" -ge 3 ]; then
    # Determine which model(s) failed
    for MODEL_NAME in "${MODELS[@]}"; do
        MODEL_FAIL_FILE="${MODEL_FAIL_DIR}/$(echo "${MODEL_NAME}" | tr ':' '_')"
        MODEL_FAILS=0
        if [ -f "${MODEL_FAIL_FILE}" ]; then
            MODEL_FAILS=$(cat "${MODEL_FAIL_FILE}" | tr -d '[:space:]' || echo 0)
        fi
        if [ "${MODEL_FAILS}" -ge 2 ]; then
            log "RECOVER: Reloading model ${MODEL_NAME} (${MODEL_FAILS} consecutive failures)"
            # Unload the model by setting keep_alive to 0
            curl -sS --max-time 30 -X POST "${OLLAMA_URL}/api/generate" \
                -H "Content-Type: application/json" \
                -d "{\"model\":\"${MODEL_NAME}\",\"prompt\":\"\",\"stream\":false,\"keep_alive\":0}" 2>/dev/null
            sleep 3
            # Reload with a warmup ping (use chat API for bedrock/thinking models)
            if [ "${MODEL_NAME}" = "bedrock:latest" ]; then
                RELOAD_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 120 \
                    -X POST "${OLLAMA_URL}/api/chat" \
                    -H "Content-Type: application/json" \
                    -d "{\"model\":\"${MODEL_NAME}\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"stream\":false,\"options\":{\"num_predict\":50},\"keep_alive\":\"24h\"}" 2>/dev/null) || RELOAD_HTTP="000"
            else
                RELOAD_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 120 \
                    -X POST "${OLLAMA_URL}/api/generate" \
                    -H "Content-Type: application/json" \
                    -d "{\"model\":\"${MODEL_NAME}\",\"prompt\":\"Hi\",\"stream\":false,\"keep_alive\":\"24h\"}" 2>/dev/null) || RELOAD_HTTP="000"
            fi
            if [ "${RELOAD_HTTP}" = "200" ]; then
                log "RECOVER: Model ${MODEL_NAME} reloaded successfully"
                echo "0" > "${MODEL_FAIL_FILE}"
            else
                log "RECOVER: Model ${MODEL_NAME} reload failed (HTTP ${RELOAD_HTTP})"
            fi
        fi
    done

    # If Ollama itself is completely down (API not responding), do a full restart
    OLLAMA_UP=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 5 "${OLLAMA_URL}/api/tags" 2>/dev/null) || OLLAMA_UP="000"
    if [ "${OLLAMA_UP}" != "200" ]; then
        log "RECOVER: Ollama API down (HTTP ${OLLAMA_UP}) — full restart"
        OLLAMA_APP="/Applications/Ollama.app"
        if [ -d "${OLLAMA_APP}" ]; then
            pgrep -f "ollama serve" | xargs kill -TERM 2>/dev/null || true
            sleep 2
            open -a "Ollama" 2>/dev/null && log "RECOVER: Ollama.app relaunched"
            for _ in $(seq 1 30); do
                sleep 2
                if curl -sS -o /dev/null --max-time 5 "${OLLAMA_URL}/api/tags" 2>/dev/null; then
                    log "RECOVER: Ollama API responsive after restart"
                    break
                fi
            done
        else
            log "WARN: Ollama.app not found; cannot auto-restart"
        fi
    fi

    # Reset failure counts
    echo "0" > "${FAIL_COUNT_FILE}"
    rm -f "${MODEL_FAIL_DIR}"/* 2>/dev/null
fi

if [ "${SUCCESS}" -eq 1 ]; then
    exit 0
else
    exit 1
fi