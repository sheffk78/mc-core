#!/bin/bash
# browser-gate-context.sh — Generate the browser gate protocol context block for subagents.
# 
# Usage:
#   browser-gate-context.sh <task-id> [url]
#
# Outputs a context string that should be appended to any subagent goal/context
# that involves browser_exec or computer_use. This ensures subagents automatically
# follow the two-layer gate protocol without Kit having to manually write it each time.
#
# If URL is provided, includes a pre-acquired session hint for that URL.

TASK_ID="${1:-}"
URL="${2:-}"

if [[ -z "$TASK_ID" ]]; then
    echo "Usage: browser-gate-context.sh <task-id> [url]"
    exit 2
fi

echo "BROWSER GATE PROTOCOL (mandatory — violations cause tab explosion and user complaints):"
echo ""
echo "## RULE #1: TAB REUSE FIRST — NEVER open a new tab without checking."
echo "  Before navigating to ANY URL, run:"
echo "    bash ~/.openclaw/workspace/SYSTEM/scripts/chrome-tab-find.sh \"<url>\" --json"
echo "  If found (exit 0) → REUSE that tab via chrome-tab-focus.sh. Do NOT open a new one."
echo "  If not found (exit 1) → safe to open."
echo "  This applies to BOTH computer_use AND browser_exec."
echo ""
echo "## Before opening ANY URL in browser_exec:"
echo "  bash ~/.openclaw/workspace/SYSTEM/scripts/browser-session-gate.sh acquire \"${TASK_ID}\" \"<url>\""
echo "  If ACQUIRED → proceed. If DENIED → do NOT open the URL — wait or use a different approach."
echo ""
echo "## When done with browser_exec (MANDATORY — end-of-task tab hygiene):"
echo "  bash ~/.openclaw/workspace/SYSTEM/scripts/browser-session-gate.sh release \\\"${TASK_ID}\\\" --close-tabs"
echo "  This releases the URL lock AND closes the tab(s) your task opened in agent Chrome."
echo "  Never leave tabs open after task completion — leftover tabs accumulate and create clutter."
echo "  EXCEPTION: only keep a tab open if a later step of the SAME task needs it."
echo ""
echo "## Before any computer_use navigation:"
echo "  bash ~/.openclaw/workspace/SYSTEM/scripts/task-browser-gate.sh navigate \"<url>\""
echo "  If FOCUS → reuse existing tab (chrome-tab-focus.sh). If OPEN → safe to create new."
echo ""
echo "## Rules:"
echo "  - ALWAYS check for existing tabs FIRST. Tab reuse > tab creation. No exceptions."
echo "  - Different URLs in parallel: OK"
echo "  - Same URL as another session: BLOCKED — do not retry, wait or pivot"
echo "  - Release your session when done so others can use the URL"
echo "  - Never open a duplicate tab — always check first"
echo "  - Prefer headless browser_exec over computer_use for site exploration"
echo "  - Close tabs you opened when done (don't leave them for the user to clean up)"
echo "  - END-OF-TASK CLEANUP: release with --close-tabs — releases the lock AND closes your tab(s)."

if [[ -n "$URL" ]]; then
    echo ""
    echo "## Your primary URL: ${URL}"
    echo "Acquire before first browser_exec call, release when task complete."
fi