#!/usr/bin/env bash
# ============================================================================= 
# hindsight-health-check.sh — Hindsight daemon health monitor (self-healing)
# Checks: (1) http://localhost:9177/health returns healthy JSON status
#         (2) PostgreSQL on port 5433 is accepting connections
# If either fails, attempts a bounded daemon restart (self-heal) BEFORE
# alerting. If still down after restart, sends a Discord alert via webhook.
# Designed for --no-agent cron mode: stdout is delivered verbatim.
# Empty stdout = all healthy (silent). Non-empty = alert message.
# Logs to /tmp/hindsight-health-check.log
# =============================================================================

set -uo pipefail

LOG_FILE="/tmp/hindsight-health-check.log"
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

# Discord webhook (home/origin channel — same as smtp-health-runner.sh)
DISCORD_WEBHOOK="https://discord.com/api/webhooks/1494550650481016843/YTUK3iCMG8mmubqVTEObbEYhSJyOUFMTksH_0AnCu_3Q5fSko219Oclk4o9PvFXEe3cu"

HEALTH_URL="http://localhost:9177/health"
# FIX (2026-08-18): embedded PG runs on 5433 (was wrongly 5434 — check always failed)
PG_PORT="5433"

ERRORS=""
ALERT_MSG=""
RESTARTED=0

log() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

# ---- Self-heal: bounded daemon recovery (only if daemon is down) -----------
# The daemon is a child of the gateway (plugin-spawned). If it's down, the
# plugin respawns it on next memory use. We wait a short window for that to
# happen before alerting. We do NOT restart the whole gateway here (too heavy).
self_heal() {
    # The daemon takes ~20-30s to boot (loads embeddings/reranker models and
    # binds :9177). A 15s window is too short and causes false alerts during
    # normal config-change restarts. Wait 40s (2x boot time) before alerting.
    log "SELF-HEAL: daemon down — waiting 40s for plugin to respawn..."
    sleep 40
    if curl -s --max-time 5 "$HEALTH_URL" 2>/dev/null | grep -q '"status":"healthy"'; then
        RESTARTED=1
        log "SELF-HEAL: daemon recovered on its own (plugin respawned it)"
        return 0
    fi
    log "SELF-HEAL: daemon still down after 40s — will alert"
    return 1
}

# ---- Check 1: Hindsight daemon health endpoint ----
HEALTH_RESPONSE=$(curl -s --max-time 10 -w "\n%{http_code}" "$HEALTH_URL" 2>&1)
CURL_EXIT=$?
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$CURL_EXIT" -ne 0 ]; then
    ERRORS="${ERRORS}Hindsight daemon unreachable (curl exit $CURL_EXIT) — endpoint $HEALTH_URL not responding.\n"
    log "FAIL: Hindsight daemon unreachable (curl exit $CURL_EXIT)"
    self_heal
elif [ "$HTTP_CODE" != "200" ]; then
    ERRORS="${ERRORS}Hindsight health endpoint returned HTTP $HTTP_CODE (expected 200).\n"
    log "FAIL: Hindsight health endpoint HTTP $HTTP_CODE"
    self_heal
elif ! echo "$RESPONSE_BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    status = data.get('status', '').lower()
    if status in ('healthy', 'ok', 'up', 'running'):
        sys.exit(0)
    else:
        print(f'Unhealthy status: {status}')
        sys.exit(1)
except Exception as e:
    print(f'Failed to parse health response: {e}')
    sys.exit(1)
" 2>/dev/null; then
    PARSE_ERR=$(echo "$RESPONSE_BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    status = data.get('status', '')
    print(f'Unhealthy status: {status}')
except Exception as e:
    print(f'Non-JSON or unparseable response: {e}')
" 2>&1)
    ERRORS="${ERRORS}Hindsight health endpoint returned non-healthy status: ${PARSE_ERR}\n"
    log "FAIL: Hindsight non-healthy status — $PARSE_ERR"
    self_heal
else
    log "OK: Hindsight daemon healthy (HTTP $HTTP_CODE, status=healthy)"
fi

# ---- Check 2: PostgreSQL on port 5434 ----
if command -v pg_isready &>/dev/null; then
    PG_OUTPUT=$(pg_isready -h localhost -p "$PG_PORT" 2>&1)
    PG_EXIT=$?
    if [ "$PG_EXIT" -ne 0 ]; then
        ERRORS="${ERRORS}PostgreSQL on port $PG_PORT not accepting connections: $PG_OUTPUT\n"
        log "FAIL: PostgreSQL port $PG_PORT not accepting connections — $PG_OUTPUT"
    else
        log "OK: PostgreSQL port $PG_PORT accepting connections"
    fi
else
    ERRORS="${ERRORS}pg_isready command not found — cannot verify PostgreSQL on port $PG_PORT.\n"
    log "WARN: pg_isready not available"
fi

# ---- Check 3: Recall-path canary (catches "daemon healthy but memory unusable") ----
# The daemon /health check passes even when the recall API path is broken (e.g.
# plugin config drift, embeddings/reranker down, bank misconfig, codec failure).
# This probes the EXACT endpoint the Hermes plugin uses for auto-recall. If the
# recall returns an error, empty result, or non-200, flag it as an integration
# outage even though the daemon reports healthy.
# (2026-08-21: added after silent Aug-19/20 outage — daemon healthy, plugin loose.)
RECALL_PROBE=$(curl -s --max-time 30 -w "\n%{http_code}" \
    -X POST "http://localhost:9177/v1/default/banks/hermes/memories/recall" \
    -H 'Content-Type: application/json' \
    -d '{"query":"ops-memory-canary recall path verification","budget":"low","max_tokens":800,"types":["observation"]}' 2>&1)
RECALL_CURL_EXIT=$?
RECALL_HTTP=$(echo "$RECALL_PROBE" | tail -1)
RECALL_BODY=$(echo "$RECALL_PROBE" | sed '$d')

if [ "$RECALL_CURL_EXIT" -ne 0 ]; then
    ERRORS="${ERRORS}RECALL CANARY: recall probe curl failed (exit $RECALL_CURL_EXIT) — recall path NOT working despite daemon /health.\n"
    log "FAIL: recall canary curl exit $RECALL_CURL_EXIT"
elif [ "$RECALL_HTTP" != "200" ]; then
    ERRORS="${ERRORS}RECALL CANARY: recall endpoint returned HTTP $RECALL_HTTP (expected 200) — recall path broken.\n"
    log "FAIL: recall canary HTTP $RECALL_HTTP"
else
    RECALL_OK=$(echo "$RECALL_BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    results = data.get('results', [])
    if isinstance(results, list):
        print('ok' if results else 'EMPTY_RESULTS')
    else:
        print('MALFORMED')
except Exception as e:
    print('PARSE_ERROR')
" 2>/dev/null)
    if [ "$RECALL_OK" = "ok" ]; then
        log "OK: recall canary passed ($(echo "$RECALL_BODY" | python3 -c 'import sys,json;print(len(json.load(sys.stdin).get("results",[])))') results)"
    elif [ "$RECALL_OK" = "EMPTY_RESULTS" ]; then
        # Empty results on a generic marker query can signal missing bank/embeddings.
        # Flag as WARNING (not hard fail) — empty recall on unrelated query may be legitimate.
        ERRORS="${ERRORS}RECALL CANARY: recall returned 200 but 0 results — possible embeddings/bank issue.\n"
        log "WARN: recall canary returned empty results"
    else
        ERRORS="${ERRORS}RECALL CANARY: recall response unparseable/malformed — recall path degraded.\n"
        log "FAIL: recall canary malformed response"
    fi
fi

# ---- Liveness: has the hermes bank served ANY recall recently? ----
# If sessions are active but no [RECALL hermes] appears in the daemon log for a
# long window, the gateway plugin may not be firing auto-recall. This is a soft
# signal (quiet periods produce none legitimately), so log as WARN only.
if [ -f "$HOME/.hindsight/profiles/hermes.log" ]; then
    # Match the ACTUAL daemon line: "[RECALL HTTP] bank=hermes ... results=N"
    # (older pattern '\[RECALL hermes' never matched the real line → false WARN)
    LAST_RECALL_TS=$(grep -E '\[RECALL HTTP\] bank=hermes' "$HOME/.hindsight/profiles/hermes.log" | tail -1 | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}' | head -1)
    if [ -n "$LAST_RECALL_TS" ]; then
        log "INFO: last live-session recall for hermes bank: $LAST_RECALL_TS"
    else
        log "WARN: no [RECALL HTTP] bank=hermes entries found in daemon log — auto-recall may not be firing"
    fi
fi

# ---- If no errors, silent exit (empty stdout = healthy, no Discord message) ----
if [ -z "$ERRORS" ]; then
    exit 0
fi

# ---- Build alert message ----
ALERT_MSG="🚨 **Hindsight Health Check FAILED** — $TIMESTAMP\n\n"
if [ "$RESTARTED" -eq 1 ]; then
    ALERT_MSG="⚠️ **Hindsight recovered after self-heal** — $TIMESTAMP\n\n"
fi
ALERT_MSG="${ALERT_MSG}\`\`\`\n"
ALERT_MSG="${ALERT_MSG}$(echo -e "$ERRORS" | sed 's/$//' | head -20)"
ALERT_MSG="${ALERT_MSG}\`\`\`\n"
ALERT_MSG="${ALERT_MSG}\nInvestigate: \\\`curl $HEALTH_URL\\\` and \\\`pg_isready -h localhost -p $PG_PORT\\\`"

# Print to stdout (delivered by cron to Discord/origin)
echo -e "$ALERT_MSG"

# ---- Also send via Discord webhook directly ----
DISCORD_PAYLOAD="/tmp/hindsight-alert-payload-$(date +%s).json"
python3 -c "
import json
msg = '''$(echo -e "$ALERT_MSG")'''
# Truncate to Discord 4000 char limit
if len(msg) > 3900:
    msg = msg[:3900] + '\\n... [truncated]'
print(json.dumps({'content': msg[:4000]}))
" > "$DISCORD_PAYLOAD" 2>/dev/null

if [ -s "$DISCORD_PAYLOAD" ]; then
    HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" -X POST "$DISCORD_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d @"$DISCORD_PAYLOAD" 2>&1) || HTTP_CODE="000"
    
    if [ "$HTTP_CODE" = "204" ]; then
        log "OK: Discord alert delivered (HTTP 204)"
    else
        log "WARN: Discord webhook returned HTTP $HTTP_CODE (expected 204)"
    fi
else
    log "WARN: Failed to build Discord JSON payload"
fi

rm -f "$DISCORD_PAYLOAD"

exit 1