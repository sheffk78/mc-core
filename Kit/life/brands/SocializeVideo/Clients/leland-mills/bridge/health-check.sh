#!/usr/bin/env bash
#
# health-check.sh — Monitoring script for Leland Mills VPS
#
# Checks:
#   1. PM2 leland-app is online
#   2. bridge.service is active
#   3. App health endpoint returns 200
#   4. Bridge health endpoint returns 200
#   5. Disk space (warn if >80%)
#
# Logs results to /home/cleaningbot/bridge/health-check.log
# Runs every 10 minutes via cron.
#
set -uo pipefail

LOG="/home/cleaningbot/bridge/health-check.log"
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
FAILURES=""

log() {
  echo "[$TIMESTAMP] $*" >> "$LOG"
}

# --- 1. PM2 leland-app online ---
PM2_STATUS=$(pm2 jlist 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for app in data:
        if app.get('name') == 'leland-app':
            print(app.get('pm2_env', {}).get('status', ''))
            break
except:
    pass
" 2>/dev/null || echo "")
if [ "$PM2_STATUS" != "online" ]; then
  FAILURES="${FAILURES}PM2 leland-app is NOT online (status: ${PM2_STATUS:-unknown}); "
fi

# --- 2. bridge.service active ---
BRIDGE_ACTIVE=$(systemctl is-active bridge.service 2>/dev/null || echo "")
if [ "$BRIDGE_ACTIVE" != "active" ]; then
  FAILURES="${FAILURES}bridge.service is NOT active (status: $BRIDGE_ACTIVE); "
fi

# --- 3. App health endpoint ---
APP_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000/api/health 2>/dev/null || echo "000")
if [ "$APP_HTTP_CODE" != "200" ]; then
  FAILURES="${FAILURES}App health endpoint returned HTTP $APP_HTTP_CODE; "
fi

# --- 4. Bridge health endpoint ---
BRIDGE_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -H "X-API-Key: lm-bridge-key-2026" http://localhost:8080/api/health 2>/dev/null || echo "000")
if [ "$BRIDGE_HTTP_CODE" != "200" ]; then
  FAILURES="${FAILURES}Bridge health endpoint returned HTTP $BRIDGE_HTTP_CODE; "
fi

# --- 5. Disk space ---
DISK_USAGE=$(df / | awk 'NR==2 {gsub(/%/,""); print $5}')
if [ -n "${DISK_USAGE:-}" ] && [ "$DISK_USAGE" -gt 80 ]; then
  FAILURES="${FAILURES}Disk usage at ${DISK_USAGE}%; "
fi

# --- Log result ---
if [ -z "$FAILURES" ]; then
  log "All checks passed"
else
  log "CHECK FAILED: $FAILURES"
fi

# --- Trim log to last 100 lines ---
if [ -f "$LOG" ]; then
  LINE_COUNT=$(wc -l < "$LOG")
  if [ "$LINE_COUNT" -gt 100 ]; then
    tail -n 100 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
  fi
fi