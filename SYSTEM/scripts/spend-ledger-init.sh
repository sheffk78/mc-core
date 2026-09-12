#!/usr/bin/env bash
# spend-ledger-init.sh - idempotent spend-guard ledger bootstrap.
#
# Creates SYSTEM/spend-guard/spend.sqlite with the ledger + kill-switch schema
# (WAL mode). Safe to re-run: CREATE TABLE IF NOT EXISTS, no truncation.
#
# Usage: bash spend-ledger-init.sh
# Env overrides (tests): SPEND_GUARD_DB
set -euo pipefail

WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"
GUARD_DIR="$WORKSPACE/SYSTEM/spend-guard"
PY="$GUARD_DIR/spend_guard.py"

if [ ! -f "$PY" ]; then
  echo "spend-ledger-init: missing $PY" >&2
  exit 1
fi

echo "spend-guard: bootstrapping ledger schema at ${SPEND_GUARD_DB:-$GUARD_DIR/spend.sqlite}"
python3 "$PY" init
echo "spend-guard: schema ready (idempotent - safe to re-run)."
exit 0
