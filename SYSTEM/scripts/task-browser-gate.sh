#!/bin/bash
# task-browser-gate.sh — Pre-flight gate for any browser navigation or computer_use call.
# Enforces: (1) tab-reuse via chrome-tab-find.sh, (2) lock acquisition for desktop tasks,
# (3) task declaration so only one desktop task runs at a time.
#
# Usage:
#   task-browser-gate.sh navigate <url> [--browser chrome|safari]
#     → Checks if URL is already open. Prints FOCUS <browser> <win> <tab> or OPEN <url>.
#     → Run chrome-tab-focus.sh with the FOCUS output, or open a new tab for OPEN.
#
#   task-browser-gate.sh desktop-acquire <task-name> <estimate-min>
#     → Acquires computer-use-lock for a desktop task. Fails if another task holds it.
#
#   task-browser-gate.sh desktop-release
#     → Releases the computer-use-lock. Run when desktop task is complete/abandoned.
#
#   task-browser-gate.sh status
#     → Prints: lock status, active task, current tab inventory (Chrome + Safari).
#
#   task-browser-gate.sh registry <action> [args]
#     → registry add <task-id> <browser> <window> <tab> <url>  — Register a tab to a task
#     → registry list                                           — Show all registered tabs
#     → registry remove <task-id>                               — Remove a task's tab entry
#     → registry clear                                          — Clear all entries
#
# Theory of operation:
#   - Headless browser_exec tasks: NO lock needed. Run in parallel. This gate doesn't apply.
#   - computer_use desktop tasks: MUST acquire lock. One at a time. This gate enforces it.
#   - Before opening ANY tab: this gate checks if it's already open. No duplicate tabs.
#   - Tab registry tracks which task owns which tab, so switching back is deterministic.

LOCK_SCRIPT=~/.openclaw/workspace/SYSTEM/scripts/computer-use-lock.sh
FIND_SCRIPT=~/.openclaw/workspace/SYSTEM/scripts/chrome-tab-find.sh
FOCUS_SCRIPT=~/.openclaw/workspace/SYSTEM/scripts/chrome-tab-focus.sh
ENSURE_SCRIPT=~/.openclaw/workspace/SYSTEM/scripts/ensure-chrome-awake.sh
REGISTRY_FILE=/tmp/browser-task-registry.json
TASK_FILE=/tmp/browser-active-task.txt
CDP_URL="http://localhost:9222"

# Initialize registry if missing
init_registry() {
    if [[ ! -f "$REGISTRY_FILE" ]]; then
        echo '{}' > "$REGISTRY_FILE"
    fi
}

# CDP-based tab listing (fast — replaces slow AppleScript enumeration for agent Chrome)
cdp_tab_list() {
    curl -s --max-time 3 "$CDP_URL/json/list" 2>/dev/null | python3 -c "
import sys, json
try:
    tabs = json.load(sys.stdin)
    pages = [t for t in tabs if t.get('type') == 'page']
    for t in pages:
        print(json.dumps({'id': t.get('id',''), 'url': t.get('url',''), 'title': t.get('title','')}))
except:
    pass
" 2>/dev/null
}

# CDP-based tab finding by URL substring (fast O(1) vs AppleScript O(n))
cdp_find_tab() {
    local url_pattern="$1"
    curl -s --max-time 3 "$CDP_URL/json/list" 2>/dev/null | python3 -c "
import sys, json
pattern = '$url_pattern'.lower()
try:
    tabs = json.load(sys.stdin)
    for t in tabs:
        if t.get('type') == 'page':
            url = t.get('url', '').lower()
            title = t.get('title', '').lower()
            if pattern in url or pattern in title:
                print(json.dumps({'found': True, 'id': t.get('id',''), 'url': t.get('url',''), 'title': t.get('title','')}))
                sys.exit(0)
    print(json.dumps({'found': False}))
except SystemExit:
    raise
except Exception:
    print(json.dumps({'found': False}))
" 2>/dev/null
}

# CDP-based tab closure
cdp_close_tab() {
    local tab_id="$1"
    local resp
    resp=$(curl -s --max-time 3 -X DELETE "$CDP_URL/json/close/$tab_id" 2>/dev/null)
    # Response is "Target is closing" on success
    echo "$resp" | grep -qi "closing" && return 0 || return 1
}

# CDP-based tab activation (focus)
cdp_activate_tab() {
    local tab_id="$1"
    curl -s --max-time 3 "$CDP_URL/json/activate/$tab_id" 2>/dev/null | grep -q "Target activated" && return 0 || return 1
}

case "${1:-}" in

    # --- Navigation gate ---
    navigate)
        URL="${2:-}"
        BROWSER="${3:-}"
        if [[ -z "$URL" ]]; then
            echo "ERROR: No URL provided"
            echo "Usage: task-browser-gate.sh navigate <url> [--browser chrome|safari]"
            exit 2
        fi
        # Strip --browser prefix if present
        if [[ "$BROWSER" == "--browser" ]]; then
            BROWSER="${3#--browser }"
            BROWSER="${4:-}"
        fi
        # Strip --browser from the URL position if accidentally combined
        BROWSER=$(echo "$BROWSER" | sed 's/--browser //')

        # Ensure Chrome + CDP + display are ready
        if [[ -f "$ENSURE_SCRIPT" ]]; then
            bash "$ENSURE_SCRIPT" 120 &>/dev/null || true
        fi

        # Try CDP first (fast, agent Chrome) — fall back to AppleScript
        CDP_RESULT=$(cdp_find_tab "$URL")
        if echo "$CDP_RESULT" | grep -q '"found": true'; then
            CDP_TAB_ID=$(echo "$CDP_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
            CDP_TAB_URL=$(echo "$CDP_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('url',''))" 2>/dev/null)
            if [[ -n "$CDP_TAB_ID" ]]; then
                cdp_activate_tab "$CDP_TAB_ID" 2>/dev/null || true
                echo "FOCUS_CDP $CDP_TAB_ID"
                echo "FOUND: $URL is already open in agent Chrome (CDP tab: ${CDP_TAB_ID:0:12}...)"
                echo "URL: $CDP_TAB_URL"
                echo "DO NOT open a new tab."
                exit 0
            fi
        fi

        echo "GATE: Checking if '$URL' is already open in Safari/personal Chrome..."
        RESULT=$($FIND_SCRIPT "$URL" --json 2>/dev/null)

        if echo "$RESULT" | grep -q '"found": true'; then
            # Parse first match
            BROWSER_FOUND=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('found') and data['matches']:
    m = data['matches'][0]
    print(f\"{m['browser']} {m['window'].split()[1]} {m['tab'].split()[1]}\")
" 2>/dev/null)

            if [[ -n "$BROWSER_FOUND" ]]; then
                read -r B WIN TAB <<< "$BROWSER_FOUND"
                echo "FOCUS $B $WIN $TAB"
                echo "FOUND: $URL is already open in $B (Window $WIN, Tab $TAB)"
                echo "ACTION: Run chrome-tab-focus.sh $B $WIN $TAB to bring it to front."
                echo "DO NOT open a new tab."
                exit 0
            fi
        fi

        echo "OPEN $URL"
        echo "NOT_FOUND: $URL is not open in any browser."
        echo "ACTION: Safe to open a new tab."
        exit 0
        ;;

    # --- Desktop lock acquisition ---
    desktop-acquire)
        TASK_NAME="${2:-unknown-task}"
        ESTIMATE_MIN="${3:-10}"
        echo "GATE: Acquiring desktop lock for task '$TASK_NAME'..."
        $LOCK_SCRIPT acquire "$TASK_NAME" "$ESTIMATE_MIN"
        EXIT_CODE=$?
        if [[ $EXIT_CODE -eq 0 ]]; then
            echo "$TASK_NAME" > "$TASK_FILE"
            echo "GATE: Lock acquired. Task '$TASK_NAME' is now the active desktop task."
            echo "GATE: Run 'task-browser-gate.sh desktop-release' when task is complete."
        else
            echo "GATE: DENIED. Another task holds the desktop lock."
            echo "GATE: Wait for it to release, or use headless browser_exec if the task doesn't need the desktop."
        fi
        exit $EXIT_CODE
        ;;

    # --- Desktop lock release ---
    desktop-release)
        ACTIVE_TASK=$(cat "$TASK_FILE" 2>/dev/null || echo "unknown")
        echo "GATE: Releasing desktop lock (was held by '$ACTIVE_TASK')..."
        $LOCK_SCRIPT release
        rm -f "$TASK_FILE"
        # Clear this task's registry entries
        init_registry
        python3 -c "
import json
with open('$REGISTRY_FILE', 'r') as f:
    data = json.load(f)
if '$ACTIVE_TASK' in data:
    del data['$ACTIVE_TASK']
with open('$REGISTRY_FILE', 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null
        echo "GATE: Released. Desktop is free."
        exit 0
        ;;

    # --- Status check ---
    status)
        echo "=== Browser Task Gate Status ==="
        echo ""
        echo "--- Desktop Lock ---"
        $LOCK_SCRIPT status
        echo ""
        ACTIVE_TASK=$(cat "$TASK_FILE" 2>/dev/null || echo "(none)")
        echo "Active desktop task: $ACTIVE_TASK"
        echo ""
        echo "--- Tab Registry ---"
        init_registry
        cat "$REGISTRY_FILE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if not data:
    print('  (empty — no tabs registered to tasks)')
else:
    for task_id, info in data.items():
        print(f\"  {task_id}: {info.get('browser','?')} Window {info.get('window','?')} Tab {info.get('tab','?')} — {info.get('url','?')}\")
" 2>/dev/null
        echo ""
        echo "--- Open Browser Tabs (Chrome + Safari) ---"
        $FIND_SCRIPT "." --json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    matches = data.get('matches', [])
    if not matches:
        print('  (no browser tabs found)')
    else:
        for m in matches:
            print(f\"  {m['browser']:8s} W{m['window'].split()[-1]} T{m['tab'].split()[-1]:2s} {m['url'][:70]}\")
except:
    print('  (unable to read tabs)')
" 2>/dev/null
        exit 0
        ;;

    # --- Tab registry ---
    registry)
        ACTION="${2:-list}"
        init_registry

        case "$ACTION" in
            add)
                TASK_ID="${3:-}"
                REG_BROWSER="${4:-}"
                REG_WINDOW="${5:-}"
                REG_TAB="${6:-}"
                REG_URL="${7:-}"
                if [[ -z "$TASK_ID" || -z "$REG_BROWSER" ]]; then
                    echo "Usage: task-browser-gate.sh registry add <task-id> <browser> <window> <tab> <url>"
                    exit 2
                fi
                python3 -c "
import json
with open('$REGISTRY_FILE', 'r') as f:
    data = json.load(f)
data['$TASK_ID'] = {
    'browser': '$REG_BROWSER',
    'window': '$REG_WINDOW',
    'tab': '$REG_TAB',
    'url': '$REG_URL'
}
with open('$REGISTRY_FILE', 'w') as f:
    json.dump(data, f, indent=2)
print(f'Registered: $TASK_ID → $REG_BROWSER W$REG_WINDOW T$REG_TAB ($REG_URL)')
" 2>/dev/null
                exit 0
                ;;
            list)
                cat "$REGISTRY_FILE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if not data:
    print('(empty)')
else:
    for task_id, info in data.items():
        print(f'{task_id}: {info}')
" 2>/dev/null
                exit 0
                ;;
            remove)
                TASK_ID="${3:-}"
                python3 -c "
import json
with open('$REGISTRY_FILE', 'r') as f:
    data = json.load(f)
if '$TASK_ID' in data:
    del data['$TASK_ID']
with open('$REGISTRY_FILE', 'w') as f:
    json.dump(data, f, indent=2)
print(f'Removed: $TASK_ID')
" 2>/dev/null
                exit 0
                ;;
            clear)
                echo '{}' > "$REGISTRY_FILE"
                echo "Registry cleared."
                exit 0
                ;;
            *)
                echo "Usage: task-browser-gate.sh registry {add|list|remove|clear}"
                exit 2
                ;;
        esac
        ;;

    # --- CDP tab listing (agent Chrome only, fast) ---
    cdp-tabs)
        if ! curl -s --max-time 2 "$CDP_URL/json/version" 2>/dev/null | grep -q '"Browser"'; then
            echo "ERROR: CDP not available. Run ensure-chrome-awake.sh first."
            exit 1
        fi
        echo "=== Agent Chrome Tabs (CDP) ==="
        cdp_tab_list | python3 -c "
import sys, json
count = 0
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    t = json.loads(line)
    count += 1
    print(f'  [{count}] {t[\"id\"][:12]}  {t[\"url\"][:70]}')
if count == 0:
    print('  (no tabs)')
else:
    print(f'  Total: {count} tab(s)')
" 2>/dev/null
        exit 0
        ;;

    # --- Close a CDP tab by ID or URL pattern ---
    close-tab)
        TARGET="${2:-}"
        if [[ -z "$TARGET" ]]; then
            echo "Usage: task-browser-gate.sh close-tab <tab-id|url-pattern>"
            exit 2
        fi
        # If it looks like a CDP tab ID (hex), close directly
        if [[ "$TARGET" =~ ^[A-F0-9]{32}$ ]]; then
            if cdp_close_tab "$TARGET"; then
                echo "CLOSED: Tab $TARGET closed via CDP"
            else
                echo "ERROR: Failed to close tab $TARGET"
                exit 1
            fi
        else
            # Find by URL pattern, close first match
            CDP_RESULT=$(cdp_find_tab "$TARGET")
            if echo "$CDP_RESULT" | grep -q '"found": true'; then
                TAB_ID=$(echo "$CDP_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
                if cdp_close_tab "$TAB_ID"; then
                    echo "CLOSED: Tab matching '$TARGET' (ID: ${TAB_ID:0:12}...) closed via CDP"
                else
                    echo "ERROR: Found tab but failed to close it"
                    exit 1
                fi
            else
                echo "NOT_FOUND: No tab matching '$TARGET' in agent Chrome"
                exit 0
            fi
        fi
        exit 0
        ;;

    # --- Close all CDP tabs (nuclear option) ---
    close-all-tabs)
        if ! curl -s --max-time 2 "$CDP_URL/json/version" 2>/dev/null | grep -q '"Browser"'; then
            echo "ERROR: CDP not available."
            exit 1
        fi
        COUNT=0
        for tab_id in $(curl -s --max-time 3 "$CDP_URL/json/list" 2>/dev/null | python3 -c "
import sys, json
tabs = json.load(sys.stdin)
for t in tabs:
    if t.get('type') == 'page':
        print(t['id'])
" 2>/dev/null); do
            cdp_close_tab "$tab_id" 2>/dev/null && COUNT=$((COUNT + 1))
        done
        echo "CLOSED: $COUNT tab(s) closed in agent Chrome"
        exit 0
        ;;

    *)
        echo "Usage: task-browser-gate.sh {navigate|desktop-acquire|desktop-release|status|registry|cdp-tabs|close-tab|close-all-tabs} [args]"
        echo ""
        echo "Commands:"
        echo "  navigate <url>                    Check if URL is already open. Returns FOCUS or OPEN."
        echo "  desktop-acquire <task> <min>      Acquire desktop lock for a task."
        echo "  desktop-release                   Release desktop lock when task is done."
        echo "  status                            Show lock + registry + all open tabs."
        echo "  registry add|list|remove|clear     Manage task-to-tab mappings."
        echo "  cdp-tabs                           List agent Chrome tabs via CDP (fast)."
        echo "  close-tab <id|url>                 Close a tab in agent Chrome via CDP."
        echo "  close-all-tabs                     Close all agent Chrome tabs (nuclear)."
        echo ""
        echo "Rules:"
        echo "  - Headless browser_exec tasks: NO lock needed. Run in parallel."
        echo "  - computer_use desktop tasks: MUST acquire lock first. One at a time."
        echo "  - Before opening ANY tab: run 'navigate <url>' first. Reuse if found."
        echo "  - AFTER a task completes: close its tabs ('close-tab <id|url>') — no leftovers."
        exit 2
        ;;

esac