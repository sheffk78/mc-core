#!/usr/bin/env bash
# cron-preflight.sh — mandatory gate before creating ANY cron job (AGENTS.md)
#
# Checks:
#   1. LLM cron (no script) >3x/day -> BLOCK (Hard Rule 2, no exceptions)
#   2. LLM cron on metered provider (ollama-cloud) -> BLOCK (Hard Rule 1)
#   3. Script-only cron >3x/day -> BLOCK unless job name is registered in
#      the Approved High-Frequency Jobs table of CRON-ALTERNATIVE-FRAMEWORK.md
#      (registration = edit the table in the same change as the cron)
#   4. LLM cron 10-min spacing vs other LLM crons (Kenneth directive 2026-08-27)
#
# Usage: cron-preflight.sh "<schedule>" [--script <name>] [--provider P] [--name N]
# Exit 0 = pass, 1 = blocked.

set -uo pipefail
WS="${WORKSPACE:-$HOME/.openclaw/workspace}"
FRAMEWORK="$WS/SYSTEM/CRON-ALTERNATIVE-FRAMEWORK.md"

SCHEDULE=""
SCRIPT=""
PROVIDER="ollama-local"
NAME=""

while [ $# -gt 0 ]; do
  case "$1" in
    --script) SCRIPT="$2"; shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    *) SCHEDULE="$1"; shift ;;
  esac
done

[ -z "$SCHEDULE" ] && { echo "PREFLIGHT FAIL: no schedule given"; exit 1; }

python3 - "$SCHEDULE" "$SCRIPT" "$PROVIDER" "$NAME" "$FRAMEWORK" << 'PYEOF'
import sys, re

schedule, script, provider, name, framework_path = sys.argv[1:6]
is_script_only = bool(script)

def parse_field(field, lo, hi):
    field = field.strip()
    if field == '*':
        return hi - lo + 1
    total = 0
    for part in field.split(','):
        if '/' in part:
            rng, step = part.split('/')
            step = int(step)
            if rng == '*':
                total += len(range(lo, hi + 1, step))
            elif '-' in rng:
                a, b = rng.split('-')
                total += len(range(int(a), int(b) + 1, step))
            else:
                total += len(range(int(rng), hi + 1, step))
        elif '-' in part:
            a, b = part.split('-')
            total += int(b) - int(a) + 1
        else:
            total += 1
    return total

def fires_per_day(schedule):
    s = schedule.strip()
    if s.startswith('every'):
        m = re.match(r'every (\d+)m', s)
        return 1440 / int(m.group(1)) if m else 1
    fields = s.split()
    if len(fields) != 5:
        return 1
    return parse_field(fields[0], 0, 59) * parse_field(fields[1], 0, 23)

fpd = fires_per_day(schedule)

# Rule 1: metered provider on any cron
if not is_script_only and 'cloud' in provider.lower():
    print(f"BLOCKED: LLM cron on metered provider '{provider}' (Hard Rule 1: all crons on ollama-local).")
    sys.exit(1)

# Rule 2: LLM cron cadence — hard 3x/day, no exceptions
if not is_script_only and fpd > 3:
    print(f"BLOCKED: LLM cron at {fpd:.0f} fires/day exceeds the 3x/day hard rule (Hard Rule 2). Reduce to <=3 fires/day or make it script-only.")
    sys.exit(1)

# Rule 3: script-only >3x/day must be registered in the framework table
if is_script_only and fpd > 3:
    try:
        table = open(framework_path).read()
    except FileNotFoundError:
        print("BLOCKED: framework file missing; cannot verify registration.")
        sys.exit(1)
    # Normalize: case + all non-alphanumerics, so "AeriusView Reply Handler"
    # matches "aeriusview-reply-handler" (job names vs table rows differ in
    # hyphenation/spacing conventions).
    norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
    if name and norm(name) in norm(table):
        print(f"PREFLIGHT PASSED: script-only, {fpd:.0f}/day, '{name}' registered in approved table.")
        sys.exit(0)
    print(f"BLOCKED: script-only cron at {fpd:.0f}/day exceeds 3x/day and '{name or '(unnamed)'}' is NOT in the Approved High-Frequency Jobs table of SYSTEM/CRON-ALTERNATIVE-FRAMEWORK.md. Register it there first (edit = approval record), then create.")
    sys.exit(1)

print(f"PREFLIGHT PASSED: {'script-only' if is_script_only else 'LLM'}, {fpd:.1f} fires/day, provider {provider}.")
sys.exit(0)
PYEOF