#!/usr/bin/env bash
# build-standard-presence-check.sh — script-only weekly backstop (Layer 6 of adoption, council 2026-09-08)
# NO LLM. Checks JOB-LEDGER for build-standard scorecard presence on process-build jobs.
# Purpose: catch DRIFT (scorecards being skipped entirely). Does NOT judge quality — that's the audit's job.
# Exit 0 = presence healthy · Exit 1 = drift detected (report to #openclaw)
set -u
LEDGER="${1:-$HOME/.openclaw/workspace/SYSTEM/JOB-LEDGER.md}"
[ -f "$LEDGER" ] || { echo "no ledger at $LEDGER"; exit 1; }

total_jobs=$(grep -c "^# JOB " "$LEDGER")
scored=$(grep -c -E "Scores:.*L[0-9]|AUDIT.*BUILD-STANDARD|n/a — no process change" "$LEDGER")
process_jobs=$(grep -E "^# JOB " "$LEDGER" | grep -c -i -E "process|standard|pipeline|framework|protocol|harness")

echo "job-ledger: $total_jobs jobs total, $process_jobs process-related, $scored with scorecard/audit markers"

# Drift signal: process-related jobs exist but ZERO scorecards ever recorded
if [ "$process_jobs" -gt 0 ] && [ "$scored" -eq 0 ]; then
  echo "DRIFT: $process_jobs process-related jobs, no BUILD-STANDARD scorecards anywhere in ledger."
  exit 1
fi
echo "OK: scorecard presence healthy."
exit 0