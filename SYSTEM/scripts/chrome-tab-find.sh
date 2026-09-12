#!/bin/bash
# chrome-tab-find.sh — Find if a URL is already open in Chrome or Safari.
# Used before opening a new tab to prevent tab proliferation.
#
# Usage:
#   chrome-tab-find.sh <url-or-domain>          — Search both Chrome and Safari. Prints matching tabs with browser + window + tab index.
#   chrome-tab-find.sh <url-or-domain> --json   — Same as above, JSON output for agent parsing.
#
# Returns:
#   exit 0 if at least one matching tab found (prints tab info)
#   exit 1 if no matching tab found
#
# Examples:
#   chrome-tab-find.sh siteguru.co
#   chrome-tab-find.sh "https://app.siteguru.co/dashboard"
#   chrome-tab-find.sh truejoybirthing.com --json

QUERY="${1:-}"
JSON_MODE="${2:-}"

if [[ -z "$QUERY" ]]; then
    echo "Usage: $0 <url-or-domain> [--json]"
    exit 2
fi

# Normalize query to lowercase for case-insensitive matching
QUERY_LOWER=$(echo "$QUERY" | tr '[:upper:]' '[:lower:]')

FOUND_CHROME=""
FOUND_SAFARI=""

# --- Chrome ---
if pgrep -x "Google Chrome" >/dev/null 2>&1; then
    FOUND_CHROME=$(osascript -e '
    tell application "Google Chrome"
        set output to ""
        set winIdx to 0
        repeat with w in windows
            set winIdx to winIdx + 1
            set tabIdx to 0
            repeat with t in tabs of w
                set tabIdx to tabIdx + 1
                set tabURL to (URL of t)
                set tabTitle to (title of t)
                set output to output & "CHROME|Window " & winIdx & "|Tab " & tabIdx & "|" & tabURL & "|" & tabTitle & linefeed
            end repeat
        end repeat
        return output
    end tell' 2>/dev/null)
fi

# --- Safari ---
if pgrep -x Safari >/dev/null 2>&1; then
    FOUND_SAFARI=$(timeout 8 osascript -e '
    tell application "Safari"
        set output to ""
        set winIdx to 0
        repeat with w in windows
            set winIdx to winIdx + 1
            set tabIdx to 0
            repeat with t in tabs of w
                set tabIdx to tabIdx + 1
                set tabURL to (URL of t)
                set tabTitle to (name of t)
                set output to output & "SAFARI|Window " & winIdx & "|Tab " & tabIdx & "|" & tabURL & "|" & tabTitle & linefeed
            end repeat
        end repeat
        return output
    end tell' 2>/dev/null)
fi

ALL_TABS="${FOUND_CHROME}${FOUND_SAFARI}"

if [[ -z "$ALL_TABS" ]]; then
    if [[ "$JSON_MODE" == "--json" ]]; then
        echo '{"found": false, "matches": []}'
    else
        echo "NO_MATCH — no browser tabs found (browsers not running or no tabs open)"
    fi
    exit 1
fi

# Filter for matching tabs
MATCHES=""
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    URL_LOWER=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    if echo "$URL_LOWER" | grep -q "$QUERY_LOWER"; then
        MATCHES="${MATCHES}${line}"$'\n'
    fi
done <<< "$ALL_TABS"

if [[ -z "$MATCHES" ]]; then
    if [[ "$JSON_MODE" == "--json" ]]; then
        echo '{"found": false, "matches": []}'
    else
        echo "NO_MATCH — '${QUERY}' is not open in Chrome or Safari"
    fi
    exit 1
fi

# Output matches
if [[ "$JSON_MODE" == "--json" ]]; then
    # Build JSON array
    echo -n '{"found": true, "matches": ['
    FIRST=true
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        IFS='|' read -r BROWSER WINDOW TABIDX URL TITLE <<< "$line"
        # Escape quotes in title
        TITLE_ESCAPED=$(echo "$TITLE" | sed 's/"/\\"/g')
        if [[ "$FIRST" == "true" ]]; then
            FIRST=false
        else
            echo -n ','
        fi
        echo -n "{\"browser\":\"$BROWSER\",\"window\":\"$WINDOW\",\"tab\":\"$TABIDX\",\"url\":\"$URL\",\"title\":\"$TITLE_ESCAPED\"}"
    done <<< "$MATCHES"
    echo ']}'
else
    echo "FOUND ${QUERY} in open tabs:"
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        IFS='|' read -r BROWSER WINDOW TABIDX URL TITLE <<< "$line"
        echo "  $BROWSER — $WINDOW, $TABIDX — $URL"
        echo "    Title: $TITLE"
    done <<< "$MATCHES"
fi

exit 0