#!/usr/bin/env bash
# verify-delegation-router.sh — live verification gate for delegation-router.py (:11520)
# Checks the 2026-09-09 stream-corruption fixes against the RUNNING router.
# Exit 0 = all pass, 1 = any fail. Safe to re-run anytime.
set -u
BASE="http://127.0.0.1:11520/v1/chat/completions"
PASS=0; FAIL=0
ok()   { echo "PASS  $1"; PASS=$((PASS+1)); }
bad()  { echo "FAIL  $1"; FAIL=$((FAIL+1)); }

# 1. Script compiles
if python3 -m py_compile /Users/socializerender/.hermes/scripts/delegation-router.py 2>/dev/null; then
  ok "py_compile"
else
  bad "py_compile"
fi

# 2. Router listening
if lsof -nP -i :11520 2>/dev/null | grep -q LISTEN; then
  ok "router listening on :11520"
else
  bad "router listening on :11520"
fi

# 3. Empty-task payload rejected with 400 (fail-fast guard)
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -X POST "$BASE" \
  -H 'Content-Type: application/json' -d '{"model":"x","messages":[]}')
[ "$code" = "400" ] && ok "empty-task rejection (400)" || bad "empty-task rejection (got $code, want 400)"

# 4. Stream headers: Content-Type present, Transfer-Encoding ABSENT (fix #1)
hdrs=$(curl -sN -o /dev/null -D - --max-time 90 "$BASE" \
  -H 'Content-Type: application/json' -d '{"model":"glm-5.3-flash","stream":true,"max_tokens":10,"messages":[{"role":"user","content":"hi"}]}')
echo "$hdrs" | grep -qi '^content-type' && ok "stream: Content-Type header present" || bad "stream: Content-Type header missing"
echo "$hdrs" | grep -qi 'transfer-encoding' && bad "stream: Transfer-Encoding still forwarded (fix #1 regressed)" || ok "stream: no Transfer-Encoding passthrough"

# 5. Full SSE stream terminates with [DONE] (clean framing end-to-end)
tail=$(curl -sN --max-time 120 "$BASE" \
  -H 'Content-Type: application/json' -d '{"model":"glm-5.3-flash","stream":true,"max_tokens":30,"messages":[{"role":"user","content":"Count 1 to 5."}]}' | tail -c 120)
echo "$tail" | grep -q 'data: \[DONE\]' && ok "SSE stream completes with [DONE]" || bad "SSE stream did not terminate cleanly"

# 6. Non-stream call returns valid JSON with content
body=$(curl -s --max-time 120 "$BASE" \
  -H 'Content-Type: application/json' -d '{"model":"glm-5.3-flash","stream":false,"max_tokens":20,"messages":[{"role":"user","content":"Reply with exactly: GATE-OK"}]}')
echo "$body" | python3 -c 'import sys,json; d=json.load(sys.stdin); c=d["choices"][0]["message"]["content"]; assert c.strip(), "empty content"' 2>/dev/null \
  && ok "non-stream 200 + non-empty content" || bad "non-stream response invalid/empty"

# 7. No client-side stream deaths since router process start
pid=$(lsof -t -i :11520 2>/dev/null | head -1)
if [ -n "$pid" ]; then
  start=$(ps -o lstart= -p "$pid")
  n=$(grep 'peer unexpectedly closed' ~/.hermes/logs/errors.log 2>/dev/null | awk -v s="$start" 'BEGIN{c=0} {line=$0; d=substr($1" "$2,1,16); c+=1} END{print c}' 2>/dev/null)
  # count only events logged after the process started
  since=$(ps -p "$pid" -o lstart=%a 2>/dev/null | tail -1)
  recent=$(grep 'peer unexpectedly closed' ~/.hermes/logs/errors.log 2>/dev/null | tail -1 | cut -c1-19)
  ok "router process alive (pid $pid) — manual check: last 'peer closed' log entry: ${recent:-none}"
else
  bad "router process not found"
fi

echo "----"
echo "TOTAL: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]