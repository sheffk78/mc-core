#!/usr/bin/env bash
# codex-web-test.sh — Spawn a Codex CLI session to deep-test a website
#
# Usage:
#   codex-web-test.sh <url> [brand] [session-label]
#
# Example:
#   codex-web-test.sh https://trustoffice.app TrustOffice "TO-homepage-audit"
#
# What it does:
#   1. Creates an output directory for the brand
#   2. Writes a Codex prompt that references the web-qa-tester skill
#   3. Spawns `codex exec` non-interactively
#   4. Codex creates a Playwright Python script, runs it, and produces a report
#   5. Output: test-results.json + test-report.md + screenshots/
#
# The script can run in background (from Hermes: terminal background=true)
# or foreground from a shell.
#
# Requires: Codex CLI installed + ChatGPT auth, Playwright Python installed

set -euo pipefail

URL="${1:?Usage: codex-web-test.sh <url> [brand] [session-label]}"
BRAND="${2:-generic}"
LABEL="${3:-$(date +%Y%m%d-%H%M%S)}"
WORKSPACE="${HOME}/.openclaw/workspace"
OUTDIR="${WORKSPACE}/Kit/life/brands/${BRAND}/tests/codex-web-tests/${LABEL}"
mkdir -p "${OUTDIR}"

SESSION_FILE="${OUTDIR}/session.jsonl"
REPORT_FILE="${OUTDIR}/test-report.md"
PROMPT_FILE="${OUTDIR}/prompt.md"

# ─── Build the prompt ───
cat > "${PROMPT_FILE}" << PROMPT_EOF
# Website Deep-Test Task

You have access to the **web-qa-tester** skill. Load it and follow its instructions.

## Target
- **URL to test:** ${URL}
- **Output directory:** . (current directory — you are already in the output directory)
- **Report file:** test-report.md (in current directory)

## Instructions

1. Create a Python Playwright test script based on the web-qa-tester skill template.
   - Set TARGET_URL to "${URL}"
   - Set OUTPUT_DIR to the current directory (use os.getcwd() or ".")
   - Save the script to test-script.py (in current directory)

2. Run the script: \`python3 test-script.py\`

3. Read the generated report at test-report.md and summarize the key findings.

4. If the script fails, debug it — fix the error and re-run. Common issues:
   - Playwright browser not found: run \`python3 -m playwright install chromium\`
   - CDP connection refused: the script will fall back to headless launch automatically
   - Timeouts: increase timeout values in the script

5. After the script completes, read test-results.json and provide a summary
   of the most critical findings.

Start now.
PROMPT_EOF

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Codex Web Test Harness (Playwright-based)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  URL:      ${URL}"
echo "  Brand:    ${BRAND}"
echo "  Label:    ${LABEL}"
echo "  OutDir:   ${OUTDIR}"
echo "  Prompt:   ${PROMPT_FILE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── Spawn Codex ───
# exec mode = non-interactive
# --json = JSONL output for parsing
# -C = working directory (brand project or /tmp)
# -o = write final agent message to file
# Use the output directory as the working directory so Codex's sandbox
# allows writing test scripts and reports there. Also add the brand project
# dir as a writable secondary so Codex can read project source if needed.
# --sandbox danger-full-access is required because Playwright launches
# Chromium as a subprocess, which Codex's workspace-write sandbox blocks.
CODEX_CWD="${OUTDIR}"
BRAND_PROJECT="${WORKSPACE}/Kit/life/brands/${BRAND}/projects"
ADD_DIRS=""
if [ -d "${BRAND_PROJECT}" ]; then
  ADD_DIRS="--add-dir ${BRAND_PROJECT}"
fi

codex exec \
  --json \
  --skip-git-repo-check \
  --sandbox danger-full-access \
  -C "${CODEX_CWD}" \
  ${ADD_DIRS} \
  -o "${OUTDIR}/agent-summary.txt" \
  - < "${PROMPT_FILE}" \
  2>&1 | tee "${SESSION_FILE}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test complete."
echo "  Report:     ${OUTDIR}/test-report.md"
echo "  JSON:       ${OUTDIR}/test-results.json"
echo "  Screenshots: ${OUTDIR}/screenshots/"
echo "  Session:    ${SESSION_FILE}"
echo "  Summary:    ${OUTDIR}/agent-summary.txt"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"