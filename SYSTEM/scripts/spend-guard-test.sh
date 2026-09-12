#!/usr/bin/env bash
# spend-guard-test.sh - REAL canary tests for the spend-guard enforcement layer.
#
# No mocks. Exercises the actual spend_guard.py against a throwaway test DB
# (SPEND_GUARD_DB override) and asserts enforcement BITES:
#   (a) cap canary      - 1c cap, 2c spend -> exit 1 + CAP breach reason
#   (b) loop canary     - 5 identical (channel,action) in window -> 5th blocks
#                         AND a kill-switch flag file is created
#   (c) reset path      - reset the channel (test-mode), next attempt ALLOWED
#   (d) fail-closed     - point DB at unreadable path -> spend BLOCKS (exit 1)
#   (e) ledger integrity- verify allowed AND blocked attempts are both recorded
#
# Outputs PASS/FAIL per test, exits non-zero if any fail. Cleans up artifacts.
set -uo pipefail

WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"
GUARD_DIR="$WORKSPACE/SYSTEM/spend-guard"
PY="$GUARD_DIR/spend_guard.py"
RESET_SH="$WORKSPACE/SYSTEM/scripts/spend-guard-reset.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/spendguard.XXXXXX")"
TEST_DB="$TMP/test.sqlite"
TEST_CFG="$TMP/test-config.yaml"

# Isolated suspend dir so we don't touch the real one.
export SPEND_GUARD_DB="$TEST_DB"
export SPEND_GUARD_CONFIG="$TEST_CFG"
export SPEND_GUARD_SUSPEND_DIR="$TMP/suspended"
export SPEND_GUARD_TEST=1   # allow the reset script to run in test mode

PASS=0
FAIL=0
SUMMARY=()

ok()   { PASS=$((PASS+1)); SUMMARY+=("PASS: $1"); echo "  [PASS] $1"; }
bad()  { FAIL=$((FAIL+1)); SUMMARY+=("FAIL: $1"); echo "  [FAIL] $1"; }

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# --- write a minimal test config: 1-cent daily cap on a fake 'canary' channel --
cat > "$TEST_CFG" <<'YAML'
global:
  per_tx_cents: 5000
  loop_tripwire:
    enabled: true
    count: 5
    window_seconds: 60
channels:
  canary:
    daily_cents: 1        # 1 cent/day -> forces a daily cap breach on a 2c spend
  loopchan:
    daily_cents: 100000   # high daily so only the tripwire fires
  failchan:
    daily_cents: 100000
YAML

echo "=== spend-guard canary tests (DB=$TEST_DB) ==="

# (a) CAP canary: set a 1-cent daily cap, attempt 2-cent spend, expect BLOCK.
python3 "$PY" init >/dev/null
OUT=$(python3 "$PY" enforce --channel canary --action-type chat --amount-cents 2 2>&1); RC=$?
if [ "$RC" -eq 1 ] && echo "$OUT" | grep -qi "cap"; then
  ok "cap canary: 2c spend on 1c-cap channel blocked (RC=$RC) reason=$(echo "$OUT" | grep -i block | head -1)"
else
  bad "cap canary: expected BLOCK w/ cap reason, got RC=$RC OUT=[$OUT]"
fi

# (b) LOOP canary: 5 identical (loopchan, ping) within window -> 5th blocks + flag.
#    The code fires the tripwire on the Nth identical action (recent+1 >= n),
#    so with count=5 the 5th attempt (recent=4, 4+1=5 >= 5) blocks.
for i in 1 2 3 4 5; do
  R=$(python3 "$PY" enforce --channel loopchan --action-type ping --amount-cents 1 2>&1); RC=$?
  if [ "$i" -lt 5 ]; then
    [ "$RC" -eq 0 ] || bad "loop canary: attempt $i should be ALLOWED, got RC=$RC [$R]"
  else
    if [ "$RC" -eq 1 ] && echo "$R" | grep -qi "tripwire"; then
      FLAG="$TMP/suspended/loopchan.flag"
      if [ -f "$FLAG" ]; then
        ok "loop canary: 5th identical action blocked by tripwire AND flag file created"
      else
        bad "loop canary: blocked but kill-switch flag file MISSING at $FLAG"
      fi
    else
      bad "loop canary: 5th should block via tripwire, got RC=$RC [$R]"
    fi
  fi
done

# (c) RESET path: reset loopchan (test mode) then a next attempt is ALLOWED.
OUT=$(bash "$RESET_SH" loopchan 2>&1); RC=$?
if [ "$RC" -ne 0 ]; then
  bad "reset path: reset script failed RC=$RC [$OUT]"
else
  # After reset the kill-switch flag is gone. A non-looping action_type must now
  # be ALLOWED (proving the channel suspension was lifted). Using a different
  # action_type avoids the legitimately-still-active tripwire window from the
  # prior 5 identical 'ping' events -- reset lifts the kill-switch, not a real
  # ongoing loop.
  R=$(python3 "$PY" enforce --channel loopchan --action-type pong --amount-cents 1 2>&1); RC2=$?
  if [ "$RC2" -eq 0 ]; then
    ok "reset path: after reset, channel un-suspended (different action ALLOWED, RC=$RC2)"
  else
    bad "reset path: after reset expected ALLOW, got RC=$RC2 [$R]"
  fi
fi

# (d) FAIL-CLOSED: point DB at an unreadable path -> spend BLOCKS.
export SPEND_GUARD_DB="/proc/this-path-does-not-exist/spend.sqlite"
OUT=$(python3 "$PY" enforce --channel failchan --action-type send --amount-cents 100 2>&1); RC=$?
if [ "$RC" -eq 1 ] && echo "$OUT" | grep -qi "fail-closed\|cannot open"; then
  ok "fail-closed: unreadable DB -> spend BLOCKED (RC=$RC)"
else
  bad "fail-closed: expected BLOCK on unreadable DB, got RC=$RC [$OUT]"
fi
# restore test db for integrity check
export SPEND_GUARD_DB="$TEST_DB"

# (e) LEDGER INTEGRITY: both allowed and blocked attempts recorded.
python3 "$PY" init >/dev/null
python3 "$PY" enforce --channel canary --action-type chat --amount-cents 1 >/dev/null 2>&1  # allowed (1c <= 1c cap... actually equals; allow)
python3 "$PY" enforce --channel canary --action-type chat --amount-cents 5 >/dev/null 2>&1  # blocked (over cap)
COUNTS=$(python3 - "$TEST_DB" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
allowed = c.execute("SELECT COUNT(*) FROM spend_events WHERE status='allowed'").fetchone()[0]
blocked = c.execute("SELECT COUNT(*) FROM spend_events WHERE status='blocked'").fetchone()[0]
print(f"{allowed} {blocked}")
PY
)
A=$(echo "$COUNTS" | awk '{print $1}'); B=$(echo "$COUNTS" | awk '{print $2}')
if [ "$A" -ge 1 ] && [ "$B" -ge 1 ]; then
  ok "ledger integrity: allowed=$A blocked=$B (both recorded)"
else
  bad "ledger integrity: expected >=1 allowed AND >=1 blocked, got allowed=$A blocked=$B"
fi

# (f) UNREGISTERED CHANNEL: a channel absent from config must BLOCK.
#     Fails closed: no reviewed budget -> no spend, until added to config.yaml.
OUT=$(python3 "$PY" enforce --channel nosuchchan --action-type chat --amount-cents 1 2>&1); RC=$?
if [ "$RC" -eq 1 ] && echo "$OUT" | grep -qi "UNREGISTERED"; then
  ok "unregistered channel: spend on channel missing from config BLOCKED (RC=$RC)"
else
  bad "unregistered channel: expected BLOCK w/ UNREGISTERED reason, got RC=$RC [$OUT]"
fi

echo "=== summary: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
  printf '%s\n' "${SUMMARY[@]}"
  exit 1
fi
exit 0
