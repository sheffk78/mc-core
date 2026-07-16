#!/usr/bin/env bash
#
# port-guard.sh — Kill stale processes on port 8080 and restart bridge.service
#
# Problem: uvicorn processes that crashed without releasing the port keep
# port 8080 occupied, so systemd can't bind bridge.service on restart.
# This script runs every 5 minutes via cron and clears the port.
#
set -euo pipefail

LOG="/home/cleaningbot/bridge/port-guard.log"
PORT=8080

log() {
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" >> "$LOG"
}

# Find PIDs listening on PORT, excluding systemd-managed processes (PID 1's children via systemd).
# We use `ss` to list listening sockets, then check if the PID's parent is systemd (1).
STALE_PIDS=""

# Use ss to find processes on the port; fall back to lsof if ss is unavailable
if command -v ss &>/dev/null; then
  PID_LIST=$(ss -tlnp "sport = :${PORT}" 2>/dev/null | grep -oP 'pid=\K[0-9]+' || true)
else
  PID_LIST=$(lsof -ti ":${PORT}" 2>/dev/null || true)
fi

for PID in $PID_LIST; do
  if [ -z "$PID" ]; then
    continue
  fi

  # Check if this process is managed by systemd (bridge.service)
  # systemd-managed processes have a cgroup containing "bridge.service"
  CGROUP_PATH="/proc/$PID/cgroup"
  IS_SYSTEMD=0

  if [ -f "$CGROUP_PATH" ]; then
    if grep -q "bridge.service" "$CGROUP_PATH" 2>/dev/null; then
      IS_SYSTEMD=1
    fi
  fi

  # Also check the process name — systemd-spawned uvicorn will be fine
  PROC_NAME=$(cat "/proc/$PID/comm" 2>/dev/null || echo "unknown")

  if [ "$IS_SYSTEMD" -eq 1 ]; then
    # This is the systemd-managed bridge — leave it alone
    log "PID $PID ($PROC_NAME) is systemd-managed bridge.service — skipping"
    continue
  fi

  # Stale process — not managed by systemd
  STALE_PIDS="$STALE_PIDS $PID"
  log "Found stale process on port $PORT: PID $PID ($PROC_NAME)"
done

if [ -n "$STALE_PIDS" ]; then
  for PID in $STALE_PIDS; do
    log "Killing stale PID $PID on port $PORT"
    kill -9 "$PID" 2>/dev/null || true
  done

  # Wait briefly for port to be released
  sleep 2

  # Restart bridge service
  log "Restarting bridge.service"
  systemctl restart bridge.service 2>/dev/null || true
  log "bridge.service restart initiated"
else
  # No stale processes — check if bridge is even running
  if ! systemctl is-active --quiet bridge.service 2>/dev/null; then
    log "bridge.service is not active — starting it"
    systemctl start bridge.service 2>/dev/null || true
    log "bridge.service start initiated"
  fi
fi