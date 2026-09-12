#!/bin/bash
# =============================================================================
# browser-separation-guard.sh — Enforces agent Chrome vs Kenneth's Chrome isolation
# =============================================================================
# Verifies that the agent Chrome instance is:
#   1. Running headless (no visible window)
#   2. Using the dedicated agent profile (NOT Kenneth's profile)
#   3. CDP responsive on port 9222
#   4. Kenneth's personal Chrome is NOT running with --remote-debugging-port
#
# Also checks that NO agent process is attached to Kenneth's Chrome windows.
#
# Usage:
#   browser-separation-guard.sh              # Verify (exit 0 = clean, exit 1 = violation)
#   browser-separation-guard.sh enforce      # Verify + kill any rogue CDP on Kenneth's Chrome
#   browser-separation-guard.sh status       # JSON status report (no side effects)
#
# HARD RULE (Kenneth directive 2026-08-26, amended 2026-09-04 — permission gate):
#   All agent browser work DEFAULTS to browser_exec (headless agent Chrome via CDP port 9222).
#   computer_use on Kenneth's personal Chrome windows requires his explicit Discord
#   permission first (chrome-permission.sh grant token); without it, blocked.
#   The headless agent Chrome has NO visible window — it cannot collide with Kenneth's desktop.
# =============================================================================

set -euo pipefail

AGENT_CHROME_PROFILE="${HOME}/.openclaw/workspace/SYSTEM/chrome-agent-profile"
KENNETH_CHROME_PROFILE="${HOME}/Library/Application Support/Google/Chrome"
CDP_PORT=9222
CDP_URL="http://localhost:${CDP_PORT}"

# --- Colors (for terminal output) ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# --- Check: Agent Chrome running and headless ---
check_agent_chrome() {
    # Find the MAIN agent Chrome process: must have --headless AND the agent profile path.
    # Child renderer processes inherit the flags but aren't the main browser process.
    local agent_pid=""
    for pid in $(pgrep -f "remote-debugging-port=${CDP_PORT}" 2>/dev/null || true); do
        local cmd_line
        cmd_line=$(ps -p "$pid" -o args= 2>/dev/null || true)
        if echo "$cmd_line" | grep -q -- "--headless" && echo "$cmd_line" | grep -q -- "chrome-agent-profile"; then
            agent_pid="$pid"
            break
        fi
    done
    
    if [[ -z "$agent_pid" ]]; then
        echo "AGENT_CHROME_NOT_RUNNING"
        return 1
    fi
    
    # Check it's headless
    local cmd_line
    cmd_line=$(ps -p "$agent_pid" -o args= 2>/dev/null || true)
    
    if echo "$cmd_line" | grep -q -- "--headless=new\|--headless"; then
        echo "AGENT_CHROME_HEADLESS:${agent_pid}"
    else
        echo "AGENT_CHROME_NOT_HEADLESS:${agent_pid}"
        return 1
    fi
    
    # Check it's using the agent profile
    if echo "$cmd_line" | grep -q -- "user-data-dir=${AGENT_CHROME_PROFILE}"; then
        echo "AGENT_CHROME_PROFILE_OK"
    else
        echo "AGENT_CHROME_WRONG_PROFILE"
        return 1
    fi
    
    return 0
}

# --- Check: Kenneth's Chrome does NOT have CDP ---
check_kenneth_chrome_clean() {
    # Strategy: Any Chrome process with remote-debugging-port that also has
    # the agent profile path (chrome-agent-profile) is the agent — NOT a violation.
    # Any Chrome process with remote-debugging-port that does NOT have the agent
    # profile path is Kenneth's Chrome with CDP — violation.
    local all_cdp_pids
    all_cdp_pids=$(pgrep -f "remote-debugging-port" 2>/dev/null || true)
    
    local violations=0
    for pid in $all_cdp_pids; do
        local cmd_line
        cmd_line=$(ps -p "$pid" -o args= 2>/dev/null || true)
        if echo "$cmd_line" | grep -q "remote-debugging-port"; then
            # Check if this is an agent Chrome process (has agent profile path)
            if echo "$cmd_line" | grep -q "chrome-agent-profile"; then
                # Agent Chrome process — OK
                continue
            fi
            # Not agent Chrome — this is Kenneth's Chrome with CDP
            echo "KENNETH_CHROME_CDP_VIOLATION:${pid}"
            violations=$((violations + 1))
        fi
    done
    
    if [[ $violations -eq 0 ]]; then
        echo "KENNETH_CHROME_CLEAN"
        return 0
    else
        return 1
    fi
}

# --- Check: CDP responsive ---
check_cdp() {
    if curl -s --max-time 2 "$CDP_URL/json/version" 2>/dev/null | grep -q '"Browser"'; then
        echo "CDP_RESPONSIVE"
        return 0
    else
        echo "CDP_NOT_RESPONSIVE"
        return 1
    fi
}

# --- Status mode (JSON, no side effects) ---
if [[ "${1:-}" == "status" ]]; then
    agent_chrome="false"
    agent_headless="false"
    agent_profile_ok="false"
    cdp_ok="false"
    kenneth_clean="true"
    
    # Capture all output from check_agent_chrome in one call
    agent_output=$(check_agent_chrome 2>/dev/null || true)
    if echo "$agent_output" | grep -q "AGENT_CHROME_HEADLESS"; then
        agent_chrome="true"
        agent_headless="true"
    fi
    if echo "$agent_output" | grep -q "AGENT_CHROME_PROFILE_OK"; then
        agent_profile_ok="true"
    fi
    
    check_cdp >/dev/null 2>&1 && cdp_ok="true"
    
    if ! check_kenneth_chrome_clean >/dev/null 2>&1; then
        kenneth_clean="false"
    fi
    
    echo "{"
    echo "  \"agent_chrome_running\": ${agent_chrome},"
    echo "  \"agent_chrome_headless\": ${agent_headless},"
    echo "  \"agent_profile_ok\": ${agent_profile_ok},"
    echo "  \"cdp_responsive\": ${cdp_ok},"
    echo "  \"cdp_port\": ${CDP_PORT},"
    echo "  \"kenneth_chrome_clean\": ${kenneth_clean},"
    echo "  \"agent_profile\": \"${AGENT_CHROME_PROFILE}\","
    echo "  \"kenneth_profile\": \"${KENNETH_CHROME_PROFILE}\","
    echo "  \"separation_ok\": $( [[ "$agent_chrome" == "true" && "$agent_headless" == "true" && "$agent_profile_ok" == "true" && "$kenneth_clean" == "true" ]] && echo "true" || echo "false" )"
    echo "}"
    exit 0
fi

# --- Verify mode ---
echo "=== Browser Separation Guard ==="
echo ""

violations=0

# 1. Agent Chrome
echo -n "Agent Chrome: "
agent_output=$(check_agent_chrome 2>&1) || violations=$((violations + 1))
case "$agent_output" in
    AGENT_CHROME_NOT_RUNNING)
        echo -e "${YELLOW}NOT RUNNING${NC} — will be launched by ensure-chrome-awake.sh"
        ;;
    AGENT_CHROME_NOT_HEADLESS:*)
        pid=${agent_output#AGENT_CHROME_NOT_HEADLESS:}
        echo -e "${RED}RUNNING BUT NOT HEADLESS (PID ${pid})${NC} — THIS IS A VIOLATION"
        ;;
    AGENT_CHROME_WRONG_PROFILE)
        echo -e "${RED}WRONG PROFILE${NC} — using Kenneth's profile!"
        ;;
    AGENT_CHROME_HEADLESS:*)
        pid=${agent_output#AGENT_CHROME_HEADLESS:}
        echo -e "${GREEN}OK — headless, PID ${pid}${NC}"
        ;;
    *)
        echo "$agent_output"
        ;;
esac

# 2. Agent profile
if echo "$agent_output" | grep -q "PROFILE_OK"; then
    echo -e "Agent profile: ${GREEN}OK${NC} — using dedicated agent profile"
else
    echo -e "Agent profile: ${RED}CHECK FAILED${NC}"
    violations=$((violations + 1))
fi

# 3. CDP
echo -n "CDP (port ${CDP_PORT}): "
if check_cdp >/dev/null 2>&1; then
    echo -e "${GREEN}RESPONSIVE${NC}"
else
    echo -e "${YELLOW}NOT RESPONDING${NC}"
fi

# 4. Kenneth's Chrome clean
echo -n "Kenneth's Chrome: "
kenneth_output=$(check_kenneth_chrome_clean 2>&1) || violations=$((violations + 1))
case "$kenneth_output" in
    KENNETH_CHROME_CLEAN)
        echo -e "${GREEN}CLEAN — no CDP/debug port${NC}"
        ;;
    KENNETH_CHROME_CDP_VIOLATION:*)
        pid=${kenneth_output#KENNETH_CHROME_CDP_VIOLATION:}
        echo -e "${RED}CDP LEAK (PID ${pid})${NC} — Kenneth's Chrome has debug port!"
        if [[ "${1:-}" == "enforce" ]]; then
            echo -e "${YELLOW}ENFORCING: killing rogue CDP process ${pid}${NC}"
            kill "$pid" 2>/dev/null || true
        fi
        ;;
    *)
        echo "$kenneth_output"
        ;;
esac

echo ""
if [[ $violations -eq 0 ]]; then
    echo -e "${GREEN}✓ SEPARATION OK${NC} — agent Chrome is isolated from Kenneth's Chrome"
    exit 0
else
    echo -e "${RED}✗ ${violations} VIOLATION(S)${NC} — agent Chrome may be leaking into Kenneth's session"
    echo ""
    echo "REMEDIATION:"
    echo "  1. Run: browser-separation-guard.sh enforce"
    echo "  2. If persisting: kill agent Chrome, restart with ensure-chrome-awake.sh"
    echo "  3. All browser tasks must use browser_exec (CDP), NOT computer_use on visible Chrome"
    exit 1
fi