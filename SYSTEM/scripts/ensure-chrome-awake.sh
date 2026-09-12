#!/bin/bash
# =============================================================================
# ensure-chrome-awake.sh — Pre-flight guarantee for browser automation
# =============================================================================
# Ensures three things before any browser task:
#   1. Chrome (agent instance with CDP) is running
#   2. The display is awake (cua-driver can't capture blanked display)
#   3. The CDP endpoint is responsive on localhost:9222
#
# This script is idempotent — safe to call before every computer_use/browser task.
# If Chrome is already running with CDP, it just verifies and returns fast.
#
# Usage:
#   ensure-chrome-awake.sh [duration]    # Prepare environment, hold display for N seconds
#   ensure-chrome-awake.sh status        # Report status as JSON (no side effects)
#
# The agent Chrome instance uses a dedicated profile at:
#   ~/.openclaw/workspace/SYSTEM/chrome-agent-profile/
#
# This keeps agent tabs separate from Jeff's personal Chrome — no accidental
# closure of Jeff's tabs, and CDP gives us programmatic tab control.
# =============================================================================

set -euo pipefail

AGENT_CHROME_PROFILE="${HOME}/.openclaw/workspace/SYSTEM/chrome-agent-profile"
CDP_PORT=9222
CDP_URL="http://localhost:${CDP_PORT}"
WAKE_SCRIPT="${HOME}/.local/bin/kit-wake-display"
CHROME_BINARY="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WAKE_DURATION="${1:-300}"  # Default 5 min hold
WAKE_PID_FILE="/tmp/ensure-chrome-wake.pid"
STATE_DIR="${HOME}/.openclaw/workspace/SYSTEM/state"

mkdir -p "$STATE_DIR" "$AGENT_CHROME_PROFILE"

# --- Helper: check if CDP endpoint is responsive ---
cdp_alive() {
    curl -s --max-time 2 "$CDP_URL/json/version" 2>/dev/null | grep -q '"Browser"'
}

# --- Helper: check if display is awake ---
display_awake() {
    if [[ "$WAKE_SCRIPT" == *kit-wake-display* ]] && [[ -f "$WAKE_SCRIPT" ]]; then
        "$WAKE_SCRIPT" --status 2>/dev/null | grep -q "awake" && return 0
    fi
    # Fallback: check if caffeinate is running
    pgrep -f "caffeinate -u" >/dev/null 2>&1
}

# --- Helper: wake display ---
wake_display() {
    local duration="$1"
    if [[ -f "$WAKE_SCRIPT" ]]; then
        # Kill any existing wake process from us
        if [[ -f "$WAKE_PID_FILE" ]]; then
            kill "$(cat "$WAKE_PID_FILE")" 2>/dev/null || true
        fi
        # Launch wake in background (non-blocking)
    nohup "$WAKE_SCRIPT" "$duration" &>/dev/null &
        echo $! > "$WAKE_PID_FILE"
        # Give it a moment to assert
        sleep 0.5
    fi
}

# --- Helper: launch agent Chrome with CDP ---
launch_agent_chrome() {
    if [[ ! -f "$CHROME_BINARY" ]]; then
        echo "ERROR: Chrome binary not found at $CHROME_BINARY"
        return 1
    fi

    # Launch Chrome with CDP and dedicated agent profile
    # --remote-allow-origins=* is required for WebSocket CDP access in Chrome 151+
    # Headless: zero visible windows — agent instance must never appear on
    # screen or collide with Kenneth's personal Chrome (fixed 2026-08-24).
    "$CHROME_BINARY" \
        --headless=new \
        --remote-debugging-port="$CDP_PORT" \
        --user-data-dir="$AGENT_CHROME_PROFILE" \
        --no-first-run \
        --no-default-browser-check \
        --disable-features=Translate \
        '--remote-allow-origins=*' \
        --window-size=1280,800 \
        &>/dev/null &

    local chrome_pid=$!
    echo "$chrome_pid" > "$STATE_DIR/agent-chrome.pid"

    # Wait for CDP to come alive (max 10 seconds)
    local attempts=0
    while ! cdp_alive; do
        attempts=$((attempts + 1))
        if [[ $attempts -ge 20 ]]; then
            echo "ERROR: Chrome launched but CDP endpoint did not respond after 10s"
            return 1
        fi
        sleep 0.5
    done
}

# --- Status mode (no side effects) ---
if [[ "${1:-}" == "status" ]]; then
    chrome_running=false
    chrome_pid=""
    cdp_responsive=false
    display_up=false

    if [[ -f "$STATE_DIR/agent-chrome.pid" ]]; then
        chrome_pid=$(cat "$STATE_DIR/agent-chrome.pid")
        if kill -0 "$chrome_pid" 2>/dev/null; then
            chrome_running=true
        fi
    fi

    if cdp_alive; then
        cdp_responsive=true
    fi

    if display_awake; then
        display_up=true
    fi

    # Get tab count from CDP
    tab_count=0
    if cdp_alive; then
        tab_count=$(curl -s --max-time 2 "$CDP_URL/json/list" 2>/dev/null | python3 -c "import sys,json; tabs=json.load(sys.stdin); print(len([t for t in tabs if t.get('type')=='page']))" 2>/dev/null || echo 0)
    fi

    echo "{\"chrome_running\": ${chrome_running}, \"chrome_pid\": \"${chrome_pid}\", \"cdp_responsive\": ${cdp_responsive}, \"cdp_port\": ${CDP_PORT}, \"display_awake\": ${display_up}, \"agent_tabs\": ${tab_count}, \"profile\": \"${AGENT_CHROME_PROFILE}\"}"
    exit 0
fi

# --- Main: ensure everything is ready ---

# Step 1: Check if agent Chrome is running with CDP
if ! cdp_alive; then
    # Check if our tracked PID is still alive
    if [[ -f "$STATE_DIR/agent-chrome.pid" ]]; then
        tracked_pid=$(cat "$STATE_DIR/agent-chrome.pid")
        if ! kill -0 "$tracked_pid" 2>/dev/null; then
            # Process died, clean up
            rm -f "$STATE_DIR/agent-chrome.pid"
        fi
    fi

    # Launch Chrome
    launch_agent_chrome
    echo "CHROME_LAUNCHED: Agent Chrome started with CDP on port ${CDP_PORT}"
else
    # Chrome is running with CDP — verify PID
    if [[ ! -f "$STATE_DIR/agent-chrome.pid" ]]; then
        # CDP is alive but we don't have a PID — find it
        cdp_pid=$(pgrep -f "remote-debugging-port=${CDP_PORT}" 2>/dev/null | head -1 || true)
        if [[ -n "$cdp_pid" ]]; then
            echo "$cdp_pid" > "$STATE_DIR/agent-chrome.pid"
        fi
    fi
    echo "CHROME_READY: Agent Chrome already running with CDP"
fi

# Step 2: Wake the display if not already awake
if ! display_awake; then
    wake_display "$WAKE_DURATION"
    echo "DISPLAY_WAKED: Display woken, held for ${WAKE_DURATION}s"
else
    echo "DISPLAY_READY: Display already awake"
fi

# Step 3: Final verification
if cdp_alive; then
    echo "READY: All systems go — Chrome + CDP + display"
    exit 0
else
    echo "ERROR: CDP still not responsive after launch attempt"
    exit 1
fi