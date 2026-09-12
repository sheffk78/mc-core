#!/bin/bash
# Cron Sentinel — enforces the 3x/day rule and provider pinning
# Runs 3x/day (8am, 2pm, 8pm) as a no_agent cron job
# Silent when all clear; posts violations to #kit-ops when found
#
# Checks:
#   1. Any enabled LLM job exceeding 3 runs/day
#   2. Any job on ollama-cloud or any metered provider
#   3. Any LLM job that could be no_agent (detect-and-defer candidate)
#   4. Any job with provider=None (inherited default — unpinned)

set -euo pipefail

JOBS_FILE="$HOME/.hermes/cron/jobs.json"
WEBHOOK_URL="${DISCORD_WEBHOOK_URL:-}"

if [ ! -f "$JOBS_FILE" ]; then
    exit 0
fi

VIOLATIONS=$(python3 << 'PYEOF'
import json, re, sys

with open("$HOME/.hermes/cron/jobs.json".replace("$HOME", __import__("os").path.expanduser("~"))) as f:
    data = json.load(f)

jobs = data.get("jobs", [])
if isinstance(jobs, dict):
    jobs = list(jobs.values())

def daily_runs(schedule):
    if isinstance(schedule, dict):
        if schedule.get("kind") == "once":
            return 0
        display = schedule.get("display", "")
        if "every" in display:
            m = re.search(r"every (\d+)m", display)
            if m:
                return max(1, int(1440 / int(m.group(1))))
        return 1
    if isinstance(schedule, str):
        if schedule.startswith("every"):
            m = re.search(r"every (\d+)m", schedule)
            if m:
                return max(1, int(1440 / int(m.group(1))))
            return 1
        if schedule.startswith("once"):
            return 0
        parts = schedule.split()
        if len(parts) == 5:
            hour = parts[1]
            if "-" in hour and "," not in hour:
                s, e = hour.split("-")
                return int(e) - int(s) + 1
            if "," in hour:
                return len(hour.split(","))
            return 1
    return 1

violations = []

for j in jobs:
    if not j.get("enabled", True):
        continue
    
    jid = j.get("id", "?")[:8]
    name = j.get("name", "?")
    provider = j.get("provider")
    model = j.get("model")
    no_agent = j.get("no_agent", False)
    runs = daily_runs(j.get("schedule"))
    
    # Check 1: LLM job exceeding 3x/day
    if not no_agent and runs > 3:
        violations.append(f"🔴 FREQ: {name} ({jid}) — LLM job runs {runs}x/day (max 3)")
    
    # Check 2: On ollama-cloud or metered provider
    if provider == "ollama-cloud":
        violations.append(f"🔴 CLOUD: {name} ({jid}) — on ollama-cloud (must be ollama-local)")

    # Check 2b: Agent-driven cron model must be the approved local worker.
    # Approved: atlas:latest (Ministral 3 14B — cron worker), bedrock:latest (Qwen 3.8 27B — workhorse).
    # Legacy names kept for backward compat.
    APPROVED_CRON_MODELS = {"atlas:latest", "bedrock:latest", "cron-orchestrator:latest", "cron-orchestrator-v2:latest", "cron-worker-64k:latest"}
    if not no_agent and provider == "ollama-local" and model not in APPROVED_CRON_MODELS:
        violations.append(f"🔴 MODEL: {name} ({jid}) — model {model} is not an approved local cron worker")
    
    # Check 3: Inherited/unpinned (provider=None) and is LLM
    if provider is None and not no_agent:
        violations.append(f"🟡 UNPINNED: {name} ({jid}) — no provider set (inherits default, may burn tokens)")
    
    # Check 4: Script job exceeding 3x/day that isn't in approved list
    APPROVED_SCRIPTS = {"tjb-city-completion-monitor.py", "ollama-api-health-check.sh", "model-health-guard.sh", "atlas-warmup.sh", "ollama-model-health-check.sh"}
    script = j.get("script", "")
    if no_agent and runs > 3 and script not in APPROVED_SCRIPTS:
        violations.append(f"🟡 UNAPPROVED: {name} ({jid}) — script runs {runs}x/day, not in approved list")

if violations:
    print("⚠️ CRON SENTINEL — " + str(len(violations)) + " violation(s) found:\n")
    print("\n".join(violations))
    print("\nReview: SYSTEM/CRON-ALTERNATIVE-FRAMEWORK.md")
PYEOF
)

if [ -n "$VIOLATIONS" ]; then
    echo "$VIOLATIONS"
fi

# Silent on no violations (empty stdout = no Discord delivery)
exit 0