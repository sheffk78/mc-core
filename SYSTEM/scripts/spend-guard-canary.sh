#!/usr/bin/env bash
# spend-guard-canary.sh — daily canary replay for the spend-guard layer
# (script-only, no LLM — cron framework compliant)
#
# Runs the full spend-guard canary suite against a throwaway test DB.
# SUCCESS  -> empty stdout (silent delivery), exit 0
# FAILURE  -> emits a 🔴 alert line (delivered to #openclaw) + appends a
#             timestamped record to SYSTEM/spend-guard/canary-alerts.log,
#             exit 1
#
# Install (mirror of media-watchdog.sh pattern):
#   hermes cron create "17 5 * * *" --script <this file> --no-agent \
#     --name spend-guard-canary --deliver discord:1539771958089093220
#
# Why this exists: enforcement that silently rots is worse than none. This is
# the continuous-audit loop for the guard — it catches a broken/patched-over
# spend_guard.py, a corrupted ledger, or a config regression within 24h.

set -uo pipefail

WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"
TEST="$WORKSPACE/SYSTEM/scripts/spend-guard-test.sh"
ALERT_LOG="$WORKSPACE/SYSTEM/spend-guard/canary-alerts.log"

OUT=$(bash "$TEST" 2>&1)
RC=$?

if [ "$RC" -eq 0 ] && echo "$OUT" | grep -q "0 failed"; then
    # Healthy: stay silent (empty stdout = no Discord delivery).
    exit 0
fi

# Failure path: alert + persist evidence.
mkdir -p "$(dirname "$ALERT_LOG")" 2>/dev/null || true
{
    echo "===== $(date -u +%Y-%m-%dT%H:%M:%SZ) canary FAILURE (rc=$RC) ====="
    echo "$OUT"
} >> "$ALERT_LOG" 2>/dev/null || true

FIRST_FAIL=$(echo "$OUT" | grep "^\s*\[FAIL\]" | head -2 | tr '\n' ' | ')
echo "🔴 SPEND-GUARD CANARY FAILED (rc=$RC): enforcement may be compromised — $FIRST_FAIL"
echo "    Full output: $ALERT_LOG | last line: $(echo "$OUT" | tail -1)"
exit 1