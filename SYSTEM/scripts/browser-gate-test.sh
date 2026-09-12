#!/bin/bash
# browser-gate-test.sh — Live fire test for the two-layer browser gate system.
# Tests: (1) duplicate URL blocking in headless browser_exec, (2) parallel different URLs,
# (3) desktop tab reuse, (4) headless session lifecycle.
# Designed to run as a cron job — fully self-contained, prints results to stdout.
#
# Output is delivered to Discord by the cron job.

set +e  # Never let one test failure kill the whole script

GATE_DESKTOP=~/.openclaw/workspace/SYSTEM/scripts/task-browser-gate.sh
GATE_HEADLESS=~/.openclaw/workspace/SYSTEM/scripts/browser-session-gate.sh
FIND_SCRIPT=~/.openclaw/workspace/SYSTEM/scripts/chrome-tab-find.sh
FOCUS_SCRIPT=~/.openclaw/workspace/SYSTEM/scripts/chrome-tab-focus.sh

PASS=0
FAIL=0
RESULTS=""

result() {
    local status="$1" name="$2" detail="$3"
    if [[ "$status" == "PASS" ]]; then
        RESULTS+="✅ ${name}\n"
        if [[ -n "$detail" ]]; then RESULTS+="   ${detail}\n"; fi
        PASS=$((PASS+1))
    else
        RESULTS+="❌ ${name}\n"
        if [[ -n "$detail" ]]; then RESULTS+="   ${detail}\n"; fi
        FAIL=$((FAIL+1))
    fi
}

echo "=== Browser Gate Live Fire Test ==="
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Pre-flight: verify scripts exist and are executable
echo "--- Pre-flight checks ---"
for script in "$GATE_DESKTOP" "$GATE_HEADLESS" "$FIND_SCRIPT" "$FOCUS_SCRIPT"; do
    if [[ ! -x "$script" ]]; then
        echo "FATAL: $script not found or not executable"
        exit 1
    fi
done
echo "All gate scripts present and executable."
echo ""

# ============================================================================
# TEST 1: Duplicate URL blocking in headless browser_exec
# ============================================================================
echo "--- TEST 1: Duplicate URL blocking (headless layer) ---"
echo "Spawning 3 subagents simultaneously, all targeting the same URL..."
echo ""

# Clean state
echo '{}' > /tmp/browser-session-registry.json

# Simulate 3 concurrent acquire attempts on the same URL
# Use background processes to simulate concurrency
(
    OUT_A=$(bash "$GATE_HEADLESS" acquire "test-1A" "https://stenodesk.co/app/invoices/new" 2>&1)
    echo "Agent A: $OUT_A" > /tmp/gate-test-1A.txt
) &
PID_A=$!

(
    OUT_B=$(bash "$GATE_HEADLESS" acquire "test-1B" "https://stenodesk.co/app/invoices/new" 2>&1)
    echo "Agent B: $OUT_B" > /tmp/gate-test-1B.txt
) &
PID_B=$!

(
    OUT_C=$(bash "$GATE_HEADLESS" acquire "test-1C" "https://stenodesk.co/app/invoices/new" 2>&1)
    echo "Agent C: $OUT_C" > /tmp/gate-test-1C.txt
) &
PID_C=$!

# Wait for all
wait $PID_A $PID_B $PID_C

OUT_A=$(cat /tmp/gate-test-1A.txt 2>/dev/null)
OUT_B=$(cat /tmp/gate-test-1B.txt 2>/dev/null)
OUT_C=$(cat /tmp/gate-test-1C.txt 2>/dev/null)

echo "Agent A: $OUT_A"
echo "Agent B: $OUT_B"
echo "Agent C: $OUT_C"
echo ""

# Count how many got ACQUIRED vs DENIED
ACQUIRED_COUNT=0
DENIED_COUNT=0
echo "$OUT_A" | grep -q "ACQUIRED" && ACQUIRED_COUNT=$((ACQUIRED_COUNT+1))
echo "$OUT_B" | grep -q "ACQUIRED" && ACQUIRED_COUNT=$((ACQUIRED_COUNT+1))
echo "$OUT_C" | grep -q "ACQUIRED" && ACQUIRED_COUNT=$((ACQUIRED_COUNT+1))
echo "$OUT_A" | grep -q "DENIED" && DENIED_COUNT=$((DENIED_COUNT+1))
echo "$OUT_B" | grep -q "DENIED" && DENIED_COUNT=$((DENIED_COUNT+1))
echo "$OUT_C" | grep -q "DENIED" && DENIED_COUNT=$((DENIED_COUNT+1))

if [[ $ACQUIRED_COUNT -eq 1 && $DENIED_COUNT -eq 2 ]]; then
    result "PASS" "T1: Duplicate URL blocking" "1 acquired, 2 denied (expected)"
else
    result "FAIL" "T1: Duplicate URL blocking" "Expected 1 acquired + 2 denied, got ${ACQUIRED_COUNT} acquired + ${DENIED_COUNT} denied"
fi

# Cleanup
bash "$GATE_HEADLESS" release "test-1A" >/dev/null 2>&1
bash "$GATE_HEADLESS" release "test-1B" >/dev/null 2>&1
bash "$GATE_HEADLESS" release "test-1C" >/dev/null 2>&1
echo '{}' > /tmp/browser-session-registry.json
rm -f /tmp/gate-test-1*.txt

# ============================================================================
# TEST 2: Parallel on different URLs (should all succeed)
# ============================================================================
echo ""
echo "--- TEST 2: Parallel different URLs (headless layer) ---"
echo "Spawning 3 subagents on 3 different URLs..."
echo ""

(
    OUT_A=$(bash "$GATE_HEADLESS" acquire "test-2A" "https://stenodesk.co/app/jobs" 2>&1)
    echo "$OUT_A" > /tmp/gate-test-2A.txt
) &
PID_A=$!

(
    OUT_B=$(bash "$GATE_HEADLESS" acquire "test-2B" "https://trustoffice.app/dashboard" 2>&1)
    echo "$OUT_B" > /tmp/gate-test-2B.txt
) &
PID_B=$!

(
    OUT_C=$(bash "$GATE_HEADLESS" acquire "test-2C" "https://coverr.co/studio/ai-images-generator" 2>&1)
    echo "$OUT_C" > /tmp/gate-test-2C.txt
) &
PID_C=$!

wait $PID_A $PID_B $PID_C

OUT_A=$(cat /tmp/gate-test-2A.txt 2>/dev/null)
OUT_B=$(cat /tmp/gate-test-2B.txt 2>/dev/null)
OUT_C=$(cat /tmp/gate-test-2C.txt 2>/dev/null)

echo "Agent A (stenodesk): $OUT_A"
echo "Agent B (trustoffice): $OUT_B"
echo "Agent C (coverr): $OUT_C"
echo ""

ACQUIRED_COUNT=0
echo "$OUT_A" | grep -q "ACQUIRED" && ACQUIRED_COUNT=$((ACQUIRED_COUNT+1))
echo "$OUT_B" | grep -q "ACQUIRED" && ACQUIRED_COUNT=$((ACQUIRED_COUNT+1))
echo "$OUT_C" | grep -q "ACQUIRED" && ACQUIRED_COUNT=$((ACQUIRED_COUNT+1))

if [[ $ACQUIRED_COUNT -eq 3 ]]; then
    result "PASS" "T2: Parallel different URLs" "All 3 acquired successfully"
else
    result "FAIL" "T2: Parallel different URLs" "Expected 3 acquired, got ${ACQUIRED_COUNT}"
fi

# Cleanup
bash "$GATE_HEADLESS" release "test-2A" >/dev/null 2>&1
bash "$GATE_HEADLESS" release "test-2B" >/dev/null 2>&1
bash "$GATE_HEADLESS" release "test-2C" >/dev/null 2>&1
echo '{}' > /tmp/browser-session-registry.json
rm -f /tmp/gate-test-2*.txt

# ============================================================================
# TEST 3: Desktop tab reuse — find existing tab, don't open new
# ============================================================================
echo ""
echo "--- TEST 3: Desktop tab reuse (desktop layer) ---"
echo "Checking if coverr.co is already open in Chrome/Safari..."
echo ""

# coverr.co should already be open (5 duplicate tabs exist from prior sessions)
NAV_RESULT=$(bash "$GATE_DESKTOP" navigate "coverr.co" 2>&1)
echo "$NAV_RESULT"
echo ""

if echo "$NAV_RESULT" | grep -q "FOCUS"; then
    # Extract browser/window/tab
    FOCUS_LINE=$(echo "$NAV_RESULT" | grep "^FOCUS")
    BROWSER=$(echo "$FOCUS_LINE" | awk '{print $2}')
    WIN=$(echo "$FOCUS_LINE" | awk '{print $3}')
    TAB=$(echo "$FOCUS_LINE" | awk '{print $4}')
    result "PASS" "T3: Desktop tab reuse — found existing" "Would focus $BROWSER W$WIN T$TAB instead of opening new"
else
    result "FAIL" "T3: Desktop tab reuse" "Expected FOCUS for coverr.co (known to be open), got: $NAV_RESULT"
fi

# Test with a URL that's definitely not open
echo ""
echo "Checking a URL that should NOT be open..."
NAV_RESULT2=$(bash "$GATE_DESKTOP" navigate "https://nonexistent-test-site-xyz123.com" 2>&1)
echo "$NAV_RESULT2"
echo ""

if echo "$NAV_RESULT2" | grep -q "OPEN"; then
    result "PASS" "T3b: Desktop tab reuse — not found" "Correctly returned OPEN for unknown URL"
else
    result "FAIL" "T3b: Desktop tab reuse — not found" "Expected OPEN, got: $NAV_RESULT2"
fi

# ============================================================================
# TEST 4: Desktop lock acquire/release lifecycle
# ============================================================================
echo ""
echo "--- TEST 4: Desktop lock lifecycle ---"
echo ""

# Acquire
ACQUIRE_OUT=$(bash "$GATE_DESKTOP" desktop-acquire "gate-test-task" 2 2>&1)
echo "Acquire: $ACQUIRE_OUT"
if echo "$ACQUIRE_OUT" | grep -q "ACQUIRED"; then
    result "PASS" "T4a: Desktop lock acquire" "Lock acquired for 'gate-test-task'"
else
    result "FAIL" "T4a: Desktop lock acquire" "Expected ACQUIRED, got: $ACQUIRE_OUT"
fi

# Try to acquire again (different task) — should fail
echo ""
ACQUIRE2_OUT=$(bash "$GATE_DESKTOP" desktop-acquire "gate-test-task-2" 2 2>&1)
echo "Second acquire attempt: $ACQUIRE2_OUT"
if echo "$ACQUIRE2_OUT" | grep -q "DENIED"; then
    result "PASS" "T4b: Desktop lock blocks second task" "Second task correctly denied"
else
    result "FAIL" "T4b: Desktop lock blocks second task" "Expected DENIED, got: $ACQUIRE2_OUT"
fi

# Status should show the lock held
echo ""
STATUS_OUT=$(bash "$GATE_DESKTOP" status 2>&1)
if echo "$STATUS_OUT" | grep -q "HELD"; then
    result "PASS" "T4c: Desktop lock status shows held" "Status correctly shows lock held"
else
    result "FAIL" "T4c: Desktop lock status shows held" "Expected HELD in status, got: $STATUS_OUT"
fi

# Release
echo ""
RELEASE_OUT=$(bash "$GATE_DESKTOP" desktop-release 2>&1)
echo "Release: $RELEASE_OUT"
if echo "$RELEASE_OUT" | grep -q "RELEASED"; then
    result "PASS" "T4d: Desktop lock release" "Lock released successfully"
else
    result "FAIL" "T4d: Desktop lock release" "Expected RELEASED, got: $RELEASE_OUT"
fi

# Status should show free
echo ""
STATUS2_OUT=$(bash "$GATE_DESKTOP" status 2>&1)
if echo "$STATUS2_OUT" | grep -q "FREE"; then
    result "PASS" "T4e: Desktop lock status shows free" "Status correctly shows lock free"
else
    result "FAIL" "T4e: Desktop lock status shows free" "Expected FREE in status, got: $STATUS2_OUT"
fi

# ============================================================================
# TEST 5: URL normalization edge cases
# ============================================================================
echo ""
echo "--- TEST 5: URL normalization ---"
echo ""

# Acquire with trailing slash
bash "$GATE_HEADLESS" acquire "norm-test" "https://example.com/dashboard/" >/dev/null 2>&1

# Check without trailing slash — should match (denied)
OUT=$(bash "$GATE_HEADLESS" acquire "norm-test-2" "https://example.com/dashboard" 2>&1)
if echo "$OUT" | grep -q "DENIED"; then
    result "PASS" "T5a: Trailing slash normalization" "https://example.com/dashboard/ matches https://example.com/dashboard"
else
    result "FAIL" "T5a: Trailing slash normalization" "Expected DENIED for same URL without slash, got: $OUT"
fi

# Check with HTTP vs HTTPS — should match (denied)
OUT=$(bash "$GATE_HEADLESS" acquire "norm-test-3" "http://example.com/dashboard" 2>&1)
if echo "$OUT" | grep -q "DENIED"; then
    result "PASS" "T5b: Protocol normalization" "http:// matches https:// for same path"
else
    result "FAIL" "T5b: Protocol normalization" "Expected DENIED for http vs https same URL, got: $OUT"
fi

# Check with uppercase domain — should match (denied)
OUT=$(bash "$GATE_HEADLESS" acquire "norm-test-4" "https://EXAMPLE.COM/dashboard" 2>&1)
if echo "$OUT" | grep -q "DENIED"; then
    result "PASS" "T5c: Case normalization" "EXAMPLE.COM matches example.com"
else
    result "FAIL" "T5c: Case normalization" "Expected DENIED for uppercase domain, got: $OUT"
fi

# Cleanup
bash "$GATE_HEADLESS" release "norm-test" >/dev/null 2>&1
echo '{}' > /tmp/browser-session-registry.json

# ============================================================================
# TEST 6: Tab inventory — verify we can see what's open
# ============================================================================
echo ""
echo "--- TEST 6: Tab inventory ---"
echo ""

TAB_COUNT=$(bash "$GATE_DESKTOP" status 2>&1 | grep -c "CHROME\|SAFARI")
if [[ $TAB_COUNT -gt 0 ]]; then
    result "PASS" "T6: Tab inventory visible" "Found $TAB_COUNT open browser tabs in status output"
else
    result "FAIL" "T6: Tab inventory visible" "No browser tabs found in status output"
fi

# Count duplicates
DUPE_ANALYSIS=$(bash "$FIND_SCRIPT" "." --json 2>/dev/null | python3 -c "
import sys, json
from collections import Counter
data = json.load(sys.stdin)
urls = [m['url'] for m in data.get('matches', [])]
dupes = [(url, count) for url, count in Counter(urls).items() if count > 1]
print(f'{len(dupes)} duplicate URL groups, {sum(c-1 for _, c in dupes)} redundant tabs')
" 2>/dev/null)

echo ""
echo "Current tab dedup status: $DUPE_ANALYSIS"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "=============================================="
echo "=== TEST SUMMARY: $PASS passed, $FAIL failed ==="
echo "=============================================="
echo ""
echo -e "$RESULTS"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo "🎉 ALL TESTS PASSED — Browser gate system is working correctly."
else
    echo "⚠️  $FAIL test(s) failed. Review the details above."
fi

echo ""
echo "Completed: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "--- Current browser state ---"
bash "$GATE_DESKTOP" status 2>&1