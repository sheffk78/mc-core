#!/usr/bin/env bash
# spend-guard-reset.sh - OWNER-ONLY channel kill-switch reset.
#
# !!! THIS IS AN OWNER ACTION. !!!
# Removing a kill-switch flag lets a previously-suspended channel spend again.
# The AGENT is permitted to RUN this script ONLY when a canary test fixture
# explicitly requires it (see spend-guard-test.sh). Resetting a real channel
# outside a test is an owner decision and must be done by/with Kenneth.
#
# Usage: bash spend-guard-reset.sh <channel>
#   e.g. bash spend-guard-reset.sh ollama-cloud
#
# Effects:
#   - removes SYSTEM/spend-guard/suspended/<channel>.flag (fast-path flag)
#   - logs the reset to SYSTEM/spend-guard/reset.log with timestamp + actor
# The kill_switches DB row is left in place (audit trail) but enforcement reads
# the flag file first, so removing the flag re-enables the channel.
set -euo pipefail

WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"
GUARD_DIR="$WORKSPACE/SYSTEM/spend-guard"
# Honour the isolated test suspend dir (SPEND_GUARD_SUSPEND_DIR) so canary tests
# never touch the real kill-switch flags. Real runs default to <guard>/suspended.
SUSPEND_DIR="${SPEND_GUARD_SUSPEND_DIR:-$GUARD_DIR/suspended}"
RESET_LOG="$GUARD_DIR/reset.log"
TEST_MODE="${SPEND_GUARD_TEST:-0}"

CHANNEL="${1:-}"
if [ -z "$CHANNEL" ]; then
  echo "spend-guard-reset: usage: bash spend-guard-reset.sh <channel>" >&2
  exit 2
fi

# Safety interlock: refuse to silently reset a real channel outside test mode.
if [ "$TEST_MODE" != "1" ]; then
  echo "spend-guard-reset: REFUSING - this is an OWNER action." >&2
  echo "  Resetting a real channel outside a canary test is not permitted by" >&2
  echo "  the agent. Set SPEND_GUARD_TEST=1 only inside spend-guard-test.sh," >&2
  echo "  or have the owner run this with explicit approval." >&2
  exit 3
fi

mkdir -p "$SUSPEND_DIR"
FLAG="$SUSPEND_DIR/${CHANNEL}.flag"
if [ -f "$FLAG" ]; then
  rm -f "$FLAG"
  echo "spend-guard-reset: removed kill-switch flag for '$CHANNEL'."
else
  echo "spend-guard-reset: no active kill-switch flag for '$CHANNEL' (nothing to do)."
fi

TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
  echo "${TS}  RESET channel=${CHANNEL} actor=spend-guard-test(test-mode)"
} >> "$RESET_LOG"

echo "spend-guard-reset: logged reset to $RESET_LOG"
exit 0
