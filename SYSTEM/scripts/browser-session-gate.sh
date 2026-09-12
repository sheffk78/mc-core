#!/bin/bash
# browser-session-gate.sh — Gate for headless browser_exec sessions.
# Prevents multiple parallel subagents from opening the same URL in separate CDP sessions.
# Uses a session registry file to track which URLs are currently active in headless browsers.
#
# Usage:
#   browser-session-gate.sh acquire <task-id> <url>     — Register a URL as in-use by a task. Fails if URL already active.
#   browser-session-gate.sh release <task-id>            — Release a task's browser session.
#   browser-session-gate.sh release <task-id> --close-tabs — Release AND close the task's tab(s) in agent Chrome (mandatory at task end).
#   browser-session-gate.sh check <url>                 — Check if URL is already active in a headless session.
#   browser-session-gate.sh status                       — Show all active headless browser sessions.
#   browser-session-gate.sh list                         — List all active sessions (JSON).
#
# This is SEPARATE from computer-use-lock.sh because headless browser_exec
# doesn't touch the desktop — it uses CDP directly. Multiple headless sessions
# CAN run in parallel, but they should NOT open the same URL simultaneously
# (causes duplicate tabs, session conflicts, race conditions on forms).
#
# Theory:
#   - Headless browser_exec tasks CAN run in parallel with each other IF they're on different URLs.
#   - Headless browser_exec tasks CAN run in parallel with computer_use (different surfaces).
#   - Two headless tasks on the SAME URL = conflict. This gate prevents that.
#   - One headless task + one computer_use on the same URL = also fine (different surfaces),
#     but should be avoided. The gate warns but doesn't block.

SESSION_FILE=/tmp/browser-session-registry.json
CDP_URL="http://localhost:9222"

init_registry() {
    if [[ ! -f "$SESSION_FILE" ]]; then
        echo '{}' > "$SESSION_FILE"
    fi
}

# Normalize URL for comparison (strip trailing slash, lowercase, strip protocol)
normalize_url() {
    local url="$1"
    # Lowercase, strip trailing slash, strip http:// or https:// (BSD sed needs -E for ?)
    echo "$url" | tr '[:upper:]' '[:lower:]' | sed 's|/$||' | sed -E 's|https?://||'
}

# Atomic lock using mkdir (works on all macOS/Linux, no flock needed)
LOCK_DIR="/tmp/browser-session-gate.lock"
acquire_lock() {
    local attempts=0
    while ! mkdir "$LOCK_DIR" 2>/dev/null; do
        attempts=$((attempts + 1))
        if [[ $attempts -gt 50 ]]; then
            # Stale lock — force remove after 5 seconds
            local lock_age=$(stat -f %m "$LOCK_DIR" 2>/dev/null || echo 0)
            local now=$(date +%s)
            if [[ $((now - lock_age)) -gt 5 ]]; then
                rmdir "$LOCK_DIR" 2>/dev/null
                continue
            fi
            echo "ERROR: Could not acquire gate lock after 50 attempts"
            return 1
        fi
        sleep 0.1
    done
    return 0
}
release_lock() {
    rmdir "$LOCK_DIR" 2>/dev/null
}

case "${1:-}" in

    acquire)
        TASK_ID="${2:-}"
        URL="${3:-}"
        if [[ -z "$TASK_ID" || -z "$URL" ]]; then
            echo "ERROR: Usage: browser-session-gate.sh acquire <task-id> <url>"
            exit 2
        fi
        init_registry

        NORM_URL=$(normalize_url "$URL")

        # Atomic check-and-write — prevents race condition when multiple
        # subagents acquire the same URL simultaneously.
        acquire_lock || exit 1
        trap release_lock EXIT

        # Check if URL is already active (inside lock)
        CONFLICT=$(python3 -c "
import json
with open('$SESSION_FILE') as f:
    data = json.load(f)
norm = '$NORM_URL'
for tid, info in data.items():
    if info.get('url_norm') == norm:
        print(f'{tid}|{info.get(\"url\", \"\")}')
        break
" 2>/dev/null)

        if [[ -n "$CONFLICT" ]]; then
            CONFLICT_TASK=$(echo "$CONFLICT" | cut -d'|' -f1)
            CONFLICT_URL=$(echo "$CONFLICT" | cut -d'|' -f2)
            echo "DENIED: URL '$URL' is already active in headless session '$CONFLICT_TASK'"
            echo "CONFLICT_TASK: $CONFLICT_TASK"
            echo "CONFLICT_URL: $CONFLICT_URL"
            echo "ACTION: Wait for '$CONFLICT_TASK' to release, or use a different URL/approach."
            release_lock
            trap - EXIT
            exit 1
        fi

        # Acquire (inside lock)
        python3 -c "
import json
with open('$SESSION_FILE') as f:
    data = json.load(f)
data['$TASK_ID'] = {
    'url': '$URL',
    'url_norm': '$NORM_URL',
    'acquired': __import__('time').time()
}
with open('$SESSION_FILE', 'w') as f:
    json.dump(data, f, indent=2)
print(f'ACQUIRED: Task \"$TASK_ID\" now holds headless session for $URL')
" 2>/dev/null
        release_lock
        trap - EXIT
        exit 0
        ;;

    release)
        TASK_ID="${2:-}"
        CLOSE_TABS=false
        [[ "${3:-}" == "--close-tabs" ]] && CLOSE_TABS=true
        if [[ -z "$TASK_ID" ]]; then
            echo "ERROR: Usage: browser-session-gate.sh release <task-id> [--close-tabs]"
            exit 2
        fi
        init_registry
        RELEASED_URL=$(RURL_TASK="$TASK_ID" python3 -c "
import json, os
with open('$SESSION_FILE') as f:
    data = json.load(f)
task = os.environ.get('RURL_TASK', '')
if task in data:
    url = data[task].get('url', '?')
    del data[task]
    with open('$SESSION_FILE', 'w') as f:
        json.dump(data, f, indent=2)
    print(f'RELEASED: Task \"{task}\" released headless session for {url}')
    print(f'RELEASED_URL:{url}')
else:
    print(f'NOT_FOUND: Task \"{task}\" had no registered session')
" 2>/dev/null)
        echo "$RELEASED_URL" | grep -v '^RELEASED_URL:'
        # --close-tabs: end-of-task tab hygiene — close every tab matching the released URL in agent Chrome
        if $CLOSE_TABS; then
            RURL=$(echo "$RELEASED_URL" | grep '^RELEASED_URL:' | sed 's/^RELEASED_URL://')
            if [[ -n "$RURL" && "$RURL" != "?" ]]; then
                CLOSED=0
                for tab_id in $(curl -s --max-time 3 "$CDP_URL/json/list" 2>/dev/null | RURL_TARGET="$RURL" python3 -c "
import sys, json, os
target = os.environ.get('RURL_TARGET', '').lower().replace('https://', '').replace('http://', '').rstrip('/')
try:
    tabs = json.load(sys.stdin)
except Exception:
    tabs = []
if target:
    for t in tabs:
        if t.get('type') == 'page':
            u = t.get('url', '').lower().replace('https://', '').replace('http://', '').rstrip('/')
            if u == target or u.startswith(target + '?') or u.startswith(target + '/'):
                print(t['id'])
" 2>/dev/null); do
                    curl -s --max-time 3 -X DELETE "$CDP_URL/json/close/$tab_id" >/dev/null 2>&1 && CLOSED=$((CLOSED + 1))
                done
                echo "CLEANUP: Closed $CLOSED tab(s) matching '$RURL' in agent Chrome"
            fi
        fi
        exit 0
        ;;

    check)
        URL="${2:-}"
        if [[ -z "$URL" ]]; then
            echo "ERROR: Usage: browser-session-gate.sh check <url>"
            exit 2
        fi
        init_registry
        NORM_URL=$(normalize_url "$URL")
        RESULT=$(python3 -c "
import json
with open('$SESSION_FILE') as f:
    data = json.load(f)
norm = '$NORM_URL'
for tid, info in data.items():
    if info.get('url_norm') == norm:
        print(f'ACTIVE|{tid}|{info.get(\"url\", \"\")}')
        break
else:
    print('FREE')
" 2>/dev/null)
        echo "$RESULT"
        if echo "$RESULT" | grep -q "^ACTIVE"; then
            exit 0  # URL is active (found)
        else
            exit 1  # URL is free (not found)
        fi
        ;;

    status)
        init_registry
        echo "=== Headless Browser Session Registry ==="
        python3 -c "
import json, time
with open('$SESSION_FILE') as f:
    data = json.load(f)
if not data:
    print('  (no active headless sessions)')
else:
    now = time.time()
    for tid, info in data.items():
        age = int(now - info.get('acquired', now))
        print(f'  {tid}: {info.get(\"url\", \"?\")} (active {age}s)')
" 2>/dev/null
        echo ""
        echo "--- Desktop Lock ---"
        ~/.openclaw/workspace/SYSTEM/scripts/computer-use-lock.sh status 2>/dev/null
        exit 0
        ;;

    list)
        init_registry
        cat "$SESSION_FILE"
        exit 0
        ;;

    *)
        echo "Usage: browser-session-gate.sh {acquire|release|check|status|list} [args]"
        echo ""
        echo "Commands:"
        echo "  acquire <task-id> <url>    Register a URL as in-use by a task. Denies if URL already active."
        echo "  release <task-id>          Release a task's session."
        echo "  check <url>                Check if URL is already active (exit 0=active, 1=free)."
        echo "  status                      Show all active sessions + desktop lock."
        echo "  list                        Raw JSON output."
        echo ""
        echo "Rules:"
        echo "  - Different URLs in parallel: OK (different sessions, no conflict)."
        echo "  - Same URL in parallel: DENIED (prevents duplicate tabs / form conflicts)."
        echo "  - Headless + computer_use on same URL: allowed but warned (different surfaces)."
        exit 2
        ;;

esac