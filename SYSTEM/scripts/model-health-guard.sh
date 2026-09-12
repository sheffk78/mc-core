#!/usr/bin/env bash
# model-health-guard.sh — Detects model OOM eviction and auto-reloads.
# Runs as a launchd agent every 10 minutes.
# Checks if atlas:latest or bedrock:latest have been evicted from memory
# and reloads them if so. Also detects model process crashes.
#
# Install: com.openclaw.model-health-guard (StartInterval=600)
# Logs: ~/.openclaw/workspace/SYSTEM/logs/model-health-guard.log

set -uo pipefail

LOG_DIR="/Users/socializerender/.openclaw/workspace/SYSTEM/logs"
LOG_FILE="${LOG_DIR}/model-health-guard.log"
OLLAMA_URL="http://127.0.0.1:11434"
MODELS=("atlas:latest" "bedrock:latest")
DISCORD_WEBHOOK="https://discord.com/api/webhooks/1494550650481016843/YTUK3iCMG8mmubqVTEObbEYhSJyOUFMTksH_0AnCu_3Q5fSko219Oclk4o9PvFXEe3cu"

mkdir -p "${LOG_DIR}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')
log() { echo "[${TIMESTAMP}] $1" >> "${LOG_FILE}"; }

# Time guard: only run 6 AM - 10 PM
HOUR=$(date +%H)
if [ "${HOUR}" -lt 6 ] || [ "${HOUR}" -ge 22 ]; then
    exit 0
fi

# Check Ollama liveness
HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 10 "${OLLAMA_URL}/api/tags" 2>/dev/null) || HTTP_CODE="000"
if [ "${HTTP_CODE}" != "200" ]; then
    log "WARN: Ollama API not responding (HTTP ${HTTP_CODE}) — warmup script will handle restart"
    exit 0
fi

# Get loaded models
LOADED=$(curl -sS --max-time 10 "${OLLAMA_URL}/api/ps" 2>/dev/null | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    for m in data.get("models", []):
        print(m.get("name", ""))
except:
    pass
' 2>/dev/null)

# Check each model
RELOADED=0
for MODEL in "${MODELS[@]}"; do
    if echo "${LOADED}" | grep -q "^${MODEL}$"; then
        # Model is loaded — check it responds via chat API (more reliable than generate)
        if [ "${MODEL}" = "bedrock:latest" ]; then
            RESP_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 30 \
                -X POST "${OLLAMA_URL}/api/chat" \
                -H "Content-Type: application/json" \
                -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"stream\":false,\"options\":{\"num_predict\":50},\"keep_alive\":\"24h\"}" 2>/dev/null) || RESP_HTTP="000"
        else
            RESP_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 30 \
                -X POST "${OLLAMA_URL}/api/chat" \
                -H "Content-Type: application/json" \
                -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"stream\":false,\"options\":{\"num_predict\":20},\"keep_alive\":\"24h\"}" 2>/dev/null) || RESP_HTTP="000"
        fi
        if [ "${RESP_HTTP}" = "200" ]; then
            : # healthy, silent
        else
            log "WARN: ${MODEL} loaded but not responding (HTTP ${RESP_HTTP}) — attempting reload"
            # Unload
            curl -sS --max-time 30 -X POST "${OLLAMA_URL}/api/generate" \
                -H "Content-Type: application/json" \
                -d "{\"model\":\"${MODEL}\",\"prompt\":\"\",\"stream\":false,\"keep_alive\":0}" 2>/dev/null
            sleep 3
            # Reload
            RELOAD_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 120 \
                -X POST "${OLLAMA_URL}/api/generate" \
                -H "Content-Type: application/json" \
                -d "{\"model\":\"${MODEL}\",\"prompt\":\"Hi\",\"stream\":false,\"keep_alive\":\"24h\"}" 2>/dev/null) || RELOAD_HTTP="000"
            if [ "${RELOAD_HTTP}" = "200" ]; then
                log "RECOVER: ${MODEL} reloaded after unresponsive"
                RELOADED=$((RELOADED + 1))
            else
                log "FAIL: ${MODEL} reload failed (HTTP ${RELOAD_HTTP})"
            fi
        fi
    else
        # Model not loaded — was evicted or never loaded
        log "WARN: ${MODEL} not in memory — reloading (was likely evicted by OOM or expired keep_alive)"
        if [ "${MODEL}" = "bedrock:latest" ]; then
            RELOAD_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 120 \
                -X POST "${OLLAMA_URL}/api/chat" \
                -H "Content-Type: application/json" \
                -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"stream\":false,\"options\":{\"num_predict\":50},\"keep_alive\":\"24h\"}" 2>/dev/null) || RELOAD_HTTP="000"
        else
            RELOAD_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 120 \
                -X POST "${OLLAMA_URL}/api/chat" \
                -H "Content-Type: application/json" \
                -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"stream\":false,\"options\":{\"num_predict\":20},\"keep_alive\":\"24h\"}" 2>/dev/null) || RELOAD_HTTP="000"
        fi
        if [ "${RELOAD_HTTP}" = "200" ]; then
            log "RECOVER: ${MODEL} reloaded into memory"
            RELOADED=$((RELOADED + 1))
        else
            log "FAIL: ${MODEL} reload failed (HTTP ${RELOAD_HTTP})"
        fi
    fi
done

# Alert if any model was reloaded (non-silent — tells us something went wrong)
if [ "${RELOADED}" -gt 0 ]; then
    export RELOADED TIMESTAMP
    python3 <<'PYEOF'
import json, os
count = os.environ.get("RELOADED", "0")
ts = os.environ.get("TIMESTAMP", "")
msg = f"🔧 **Model Auto-Recovery** — {ts}\n\n{count} model(s) were evicted/unresponsive and have been reloaded.\nThis is informational — the system self-healed. If this happens frequently, investigate memory pressure."
payload = json.dumps({"content": msg[:2000]})
import urllib.request
req = urllib.request.Request(
    "https://discord.com/api/webhooks/1494550650481016843/YTUK3iCMG8mmubqVTEObbEYhSJyOUFMTksH_0AnCu_3Q5fSko219Oclk4o9PvFXEe3cu",
    data=payload.encode(),
    headers={"Content-Type": "application/json"}
)
try:
    urllib.request.urlopen(req, timeout=10)
except:
    pass
PYEOF
fi

exit 0