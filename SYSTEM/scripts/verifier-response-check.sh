#!/usr/bin/env bash
# verifier-response-check.sh — Scans the last assistant message for false success claims
# when the file-mutation verifier flagged a blocked write.
#
# Usage: verifier-response-check.sh <assistant_message_text>
# Exit 0 = clean, exit 1 = false claim detected
#
# Deployed as part of the protected-file honesty rule (AGENTS.md).

set -euo pipefail

MSG="${1:-}"

if [ -z "$MSG" ]; then
  echo "Usage: verifier-response-check.sh <message>"
  exit 0
fi

# Check if the message contains verifier-blocked language
if ! echo "$MSG" | grep -qiE "file.mutation verifier|Refusing to write|NOT modified"; then
  # No verifier block in this message — nothing to check
  exit 0
fi

# Check for false success claims despite the block
# Match success verbs only when followed by period, exclamation, or end-of-line
# (avoids matching words inside instructions like "Edit ... manually")
if echo "$MSG" | grep -qiE '\b(Done|Updated|Changed|Applied|Bumped|Wrote|Saved|Created|Modified|Patched)[.!]|\bSet\b[^"]*$'; then
  # Exclude if the message also contains manual-edit instructions (honest acknowledgment)
  if echo "$MSG" | grep -qiE 'blocked|manually|Edit .* directly|could not|was not|cannot|unable|failed'; then
    # The agent acknowledged the block AND gave manual instructions — honest
    exit 0
  fi
  echo "⚠️ FALSE CLAIM DETECTED: Message contains a success claim ('Done'/'Updated'/etc.) alongside a file-mutation verifier block."
  echo "The agent claimed a write succeeded but the verifier blocked it."
  exit 1
fi

exit 0