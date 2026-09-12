#!/usr/bin/env bash
# session-token-watchdog.sh — script-only monitor (cron framework compliant)
#
# Detects RETRY LOOPS in live LLM sessions by scoring state.db every 20 min.
# Tuned + replay-verified against the 2026-09-11 incident (74 near-identical
# EAS expect-scripts over 141 min, 43.3M input tokens) and 6 live sessions:
#
#   Signal: same 150-char command body repeated >= 6x in 30 min with
#   >= 5 byte-identical outputs (the loop signature: same args → same stale
#   result). Legit work never hits this:
#     - healthy forensics: worst repeat 2, outputs all differ
#     - iterating experiments (PDF sig fix): repeat 23 but every output differs
#     - API fix-loops (railway GraphQL): repeat 10, outputs all differ
#     - parallel-batch double-logs: filtered via active=1 + tool_call_id join
#     - INCIDENT: repeat 51, 29 byte-identical outputs ← caught
#
# Independent of in-process tool guardrails (reads state.db after the fact),
# so it also catches guardrail code bugs. Script-only, no LLM. One alert per
# session per burst (dedupe file).
#
# Install (script-only cron):
#   hermes cron create "*/20 * * * *" --script <this file> --no-agent \
#     --name session-token-watchdog --deliver discord:1539771958089093220
#
# Behavior: healthy -> silent exit 0; loop detected -> alert line + report
# file, exit 1.

set -uo pipefail

DB="$HOME/.hermes/state.db"
REPORT_DIR="$HOME/.openclaw/workspace/SYSTEM/cron-reports"
mkdir -p "$REPORT_DIR"
STATE_FILE="/tmp/session-token-watchdog-alerted.txt"

python3 - "$DB" "$STATE_FILE" << 'PYEOF' 2>&1
import sqlite3, sys, time, json
from collections import defaultdict, Counter

db_path, state_file = sys.argv[1], sys.argv[2]
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
now = time.time()

REPEAT_ALERT = 6            # same 150-char command body, N times in window
IDENTICAL_OUT_ALERT = 5     # of those, N byte-identical outputs (stale retry)
FRESH_WINDOW = 600          # session live: last message < 10 min ago
WINDOW = 1800               # 30-min lookback

# Results joined by tool_call_id (never positional — compaction rewrites rows).
tres = conn.execute("""
SELECT tool_call_id, content FROM messages
WHERE role='tool' AND active=1 AND timestamp > ?
""", (now - WINDOW,)).fetchall()
res_by_id = {}
for cid, content in tres:
    try:
        d = json.loads(content)
        out = (d.get('output', '') or '')
    except Exception:
        out = content or ''
    res_by_id[cid] = out

# ONLY active=1 assistant rows — compaction leaves active=0 ghosts that
# otherwise double every call (the first watchdog draft alerted on 5 healthy
# sessions because of exactly this).
acalls = conn.execute("""
SELECT session_id, timestamp, tool_calls FROM messages
WHERE role='assistant' AND active=1 AND tool_calls IS NOT NULL AND tool_calls != ''
AND timestamp > ?
ORDER BY timestamp
""", (now - WINDOW,)).fetchall()

pairs_by_session = defaultdict(list)
for sid, ts, tc in acalls:
    for call in json.loads(tc):
        name = call.get('function', {}).get('name', '?')
        if name not in ('terminal', 'execute_code'):
            continue
        args = call.get('function', {}).get('arguments', '{}')
        try:
            d = json.loads(args)
            body = d.get('command', d.get('code', args))
        except Exception:
            body = args
        pairs_by_session[sid].append((body, res_by_id.get(call.get('id', ''), '')))

try:
    with open(state_file) as f:
        alerted = set(l.strip() for l in f if l.strip())
except FileNotFoundError:
    alerted = set()

alerts = []
for sid, pairs in pairs_by_session.items():
    last = conn.execute(
        "SELECT MAX(timestamp) FROM messages WHERE session_id=?", (sid,)).fetchone()[0] or 0
    if now - last > FRESH_WINDOW:
        continue
    exact = Counter(c[:150] for c, o in pairs)
    worst, n = exact.most_common(1)[0] if exact else ('', 0)
    if n < REPEAT_ALERT:
        continue
    outs = [o[:120] for c, o in pairs if c[:150] == worst]
    identical = len(outs) - len(set(outs))
    if identical < IDENTICAL_OUT_ALERT:
        continue  # outputs differ = iteration, not a stuck retry
    if sid in alerted:
        continue
    tok = conn.execute(
        "SELECT input_tokens, output_tokens FROM session_model_usage WHERE session_id=?",
        (sid,)).fetchone()
    in_tok = tok[0] if tok else 0
    sess = conn.execute("SELECT display_name FROM sessions WHERE id=?", (sid,)).fetchone()
    disp = (sess[0].strip() if sess and sess[0] else sid[-8:])
    fname = f"{time.strftime('%Y-%m-%d')}-runaway-{sid[-8:]}.md"
    report = f"""# Runaway session detected — {sid}
- time: {time.strftime('%Y-%m-%d %H:%M:%S')}
- session: {disp}
- signature: one command body repeated {n}x in 30 min; {identical} repeats returned BYTE-IDENTICAL output
- command: {worst[:120]}
- input tokens: {in_tok:,}
- in-process cap blocks at 100 calls/tool/turn (loop_same_tool_cap); this is the independent detection backstop.
- if still running: inspect via `hermes sessions`, kill via gateway if needed.
"""
    with open(f"{REPORT_DIR}/{fname}", "w") as f:
        f.write(report)
    alerts.append(
        f"🔴 RUNAWAY SESSION {disp} ({sid[-8:]}): cmd repeated {n}x with {identical} identical "
        f"outputs, {in_tok:,} input tokens. Report: SYSTEM/cron-reports/{fname}"
    )
    alerted.add(sid)

if not alerts:
    sys.exit(0)
with open(state_file, "w") as f:
    f.write("\n".join(sorted(alerted)))
print("\n".join(alerts))
sys.exit(1)
PYEOF
RC=$?
[ "$RC" -eq 1 ] && exit 1
exit 0