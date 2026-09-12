#!/usr/bin/env bash
# ledger-append.sh — Append-only guard for JOB-LEDGER (and any target md file).
#
# Usage:
#   ledger-append.sh [target.md]            # read text from stdin, append
#   ledger-append.sh [target.md] --file F   # read text from file F, append
#
# Behavior:
#   - Default target: SYSTEM/JOB-LEDGER.md (relative to workspace root).
#   - Before appending, copies the CURRENT file into a dated .bak inside
#     SYSTEM/ledger-backups/ (mkdir -p the dir; name JOB-LEDGER.YYYYMMDD-HHMM.bak).
#   - Appends with >> (never truncates or rewrites the whole file).
#   - On any error, leaves the original untouched.
#
# Exit codes: 0 success; 1 usage/error (original untouched).

set -euo pipefail

WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"
DEFAULT_TARGET="$WORKSPACE/SYSTEM/JOB-LEDGER.md"
BACKUP_DIR="$WORKSPACE/SYSTEM/ledger-backups"

# --- arg parsing -----------------------------------------------------------
TARGET=""
INPUT_FILE=""
ARGS=("$@")
i=0
for a in ${ARGS[@]+"${ARGS[@]}"}; do
  if [ "$a" = "--file" ]; then
    i=$((i+1))
    INPUT_FILE="${ARGS[$i]:-}"
    if [ -z "$INPUT_FILE" ]; then
      echo "ledger-append: --file requires a path" >&2
      exit 1
    fi
  elif [ -z "$TARGET" ] && [ "$a" != "--file" ]; then
    TARGET="$a"
  fi
  i=$((i+1))
done

if [ -z "$TARGET" ]; then
  TARGET="$DEFAULT_TARGET"
fi

# --- validations -----------------------------------------------------------
if [ ! -f "$TARGET" ]; then
  echo "ledger-append: target not found: $TARGET" >&2
  exit 1
fi

if [ -n "$INPUT_FILE" ]; then
  if [ ! -f "$INPUT_FILE" ]; then
    echo "ledger-append: input file not found: $INPUT_FILE" >&2
    exit 1
  fi
else
  if [ -t 0 ]; then
    echo "ledger-append: no input on stdin and no --file given" >&2
    exit 1
  fi
fi

# --- backup current file (dated) -------------------------------------------
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M)"
BASE="$(basename "$TARGET")"
BACKUP="$BACKUP_DIR/${BASE}.${STAMP}.bak"
if ! cp "$TARGET" "$BACKUP"; then
  echo "ledger-append: failed to create backup $BACKUP" >&2
  exit 1
fi

# --- append (never truncate) ------------------------------------------------
if [ -n "$INPUT_FILE" ]; then
  if ! cat "$INPUT_FILE" >> "$TARGET"; then
    echo "ledger-append: append failed; original left untouched (backup at $BACKUP)" >&2
    exit 1
  fi
else
  if ! cat >> "$TARGET"; then
    echo "ledger-append: append failed; original left untouched (backup at $BACKUP)" >&2
    exit 1
  fi
fi

echo "ledger-append: appended to $TARGET (backup: $BACKUP)"
exit 0
