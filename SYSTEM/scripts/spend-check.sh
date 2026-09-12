#!/usr/bin/env bash
# spend-check.sh - thin wrapper around spend_guard.py enforce.
#
# Mirrors the cron-preflight.sh output style: a clear BLOCKED line + reason on
# block, a clean PASS line on allow. Exit 0 = allow, exit 1 = block.
#
# Usage:
#   bash spend-check.sh --channel X --action-type Y --amount-cents N [--session-id S]
#   (all args forwarded verbatim to spend_guard.py enforce)
#
# Env: SPEND_GUARD_DB, SPEND_GUARD_CONFIG, SPEND_GUARD_DISABLED may be set.
set -euo pipefail

# Emoji glyphs (byte-safe hex escapes so the script is ASCII-source clean).
RED_BLOCK=$'\xf0\x9f\x94\xb4'   # ð´
GREEN_OK=$'\xe2\x9c\x93'        # â

WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"
PY="$WORKSPACE/SYSTEM/spend-guard/spend_guard.py"

if [ ! -f "$PY" ]; then
  echo "spend-check: missing $PY" >&2
  exit 1
fi

# Forward every arg to the python enforce command.
OUT="$(python3 "$PY" enforce "$@" 2>&1)" && RC=0 || RC=$?

# Render a consistent, scannable verdict regardless of RC.
if [ "$RC" -eq 0 ]; then
  echo "${GREEN_OK} SPEND CHECK PASSED: $OUT"
  exit 0
else
  # Pull the BLOCK reason (last line emitted by spend_guard.py).
  echo "${RED_BLOCK} BLOCKED: spend-guard rejected this action."
  printf '%s\n' "$OUT" | sed 's/^/   /'
  echo "   Dispatch halted. Owner reset / break-glass required to proceed."
  exit 1
fi
