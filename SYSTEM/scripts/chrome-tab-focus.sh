#!/bin/bash
# chrome-tab-focus.sh — Bring an existing Chrome or Safari tab to the front.
# Used after chrome-tab-find.sh locates the tab you want to reuse.
#
# Usage:
#   chrome-tab-focus.sh chrome <window-num> <tab-num>
#   chrome-tab-focus.sh safari <window-num> <tab-num>
#
# Examples:
#   chrome-tab-focus.sh chrome 1 3      — Focus Chrome window 1, tab 3
#   chrome-tab-focus.sh safari 2 1      — Focus Safari window 2, tab 1
#
# After focusing, computer_use can drive the tab. This prevents opening duplicate tabs.

BROWSER="${1:-}"
WIN_NUM="${2:-}"
TAB_NUM="${3:-}"

if [[ -z "$BROWSER" || -z "$WIN_NUM" || -z "$TAB_NUM" ]]; then
    echo "Usage: $0 {chrome|safari} <window-num> <tab-num>"
    exit 2
fi

case "$BROWSER" in
    chrome)
        if ! pgrep -x "Google Chrome" >/dev/null 2>&1; then
            echo "ERROR: Chrome is not running"
            exit 1
        fi
        osascript -e "
        tell application \"Google Chrome\"
            activate
            set w to window ${WIN_NUM}
            set active tab index of w to ${TAB_NUM}
            set index of w to 1
        end tell" 2>&1
        echo "FOCUSED Chrome window ${WIN_NUM} tab ${TAB_NUM}"
        ;;
    safari)
        if ! pgrep -x Safari >/dev/null 2>&1; then
            echo "ERROR: Safari is not running"
            exit 1
        fi
        timeout 8 osascript -e "
        tell application \"Safari\"
            activate
            set w to window ${WIN_NUM}
            set current tab of w to tab ${TAB_NUM}
            set index of w to 1
        end tell" 2>&1
        echo "FOCUSED Safari window ${WIN_NUM} tab ${TAB_NUM}"
        ;;
    *)
        echo "ERROR: Unknown browser '$BROWSER'. Use 'chrome' or 'safari'."
        exit 2
        ;;
esac

exit 0