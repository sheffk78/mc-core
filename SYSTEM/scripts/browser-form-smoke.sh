#!/usr/bin/env bash
# Safe non-submitting regression test for the browser form-filling lane.
# It fills httpbin's demo form, verifies text/radio/checkbox state, captures
# evidence, confirms the URL did not change, and never clicks Submit order.
set -euo pipefail

BIN="${AGENT_BROWSER_BIN:-/opt/homebrew/bin/agent-browser}"
SESSION="browser-form-smoke-$$"
OUT_DIR="${1:-/tmp/browser-form-smoke}"
mkdir -p "$OUT_DIR"
trap '"$BIN" --session "$SESSION" close >/dev/null 2>&1 || true' EXIT

[[ "$($BIN --version)" == "agent-browser 0.33.1" ]]
"$BIN" --session "$SESSION" open https://httpbin.org/forms/post >/dev/null
sleep 3
"$BIN" --session "$SESSION" snapshot -i --json > "$OUT_DIR/before.json"
"$BIN" --session "$SESSION" fill 'input[name=custname]' 'Kit Browser Test' >/dev/null
"$BIN" --session "$SESSION" fill 'input[name=custemail]' 'kit@example.test' >/dev/null
"$BIN" --session "$SESSION" fill 'textarea[name=comments]' 'Non-submitting verification run.' >/dev/null
"$BIN" --session "$SESSION" click 'input[value="medium"]' >/dev/null
"$BIN" --session "$SESSION" check 'input[value="bacon"]' >/dev/null
"$BIN" --session "$SESSION" snapshot -i --json > "$OUT_DIR/after.json"
"$BIN" --session "$SESSION" get url > "$OUT_DIR/url.txt"
"$BIN" --session "$SESSION" screenshot "$OUT_DIR/final.png" >/dev/null

python3 - "$OUT_DIR" <<'PY'
import json, pathlib, sys
out = pathlib.Path(sys.argv[1])
after = json.loads((out / 'after.json').read_text())
snapshot = after['data']['snapshot']
assert after['success']
for value in ('Kit Browser Test', 'kit@example.test', 'Non-submitting verification run.'):
    assert value in snapshot, value
assert 'radio " Medium" [checked=true' in snapshot
assert 'checkbox " Bacon" [checked=true' in snapshot
assert (out / 'url.txt').read_text().strip() == 'https://httpbin.org/forms/post'
print('FORM_SUITE_PASS')
print('filled_text_radio_checkbox=True')
print('resnapshot_verified=True')
print('url_unchanged=True')
print('submit_untouched=True')
print(f'evidence={out}')
PY
