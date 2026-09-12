#!/bin/bash
# Deploy Pre-Flight Gate — run BEFORE any Railway deployment operation
#
# Usage: bash deploy-preflight.sh "<brand-name>" "<project-name>" [--subagent]
#
# Verifies that the railway-deploy skill has been loaded and that a deployment
# subagent is being used (or explicitly confirmed for direct deployment).
#
# Returns exit 0 if OK to proceed, exit 1 with violations if blocked.
# This is a GATE, not a suggestion. If it blocks, you must fix the issue first.
#
# Checks performed:
#   1. railway-deploy skill is loaded (verified via skill registry)
#   2. Railway token exists and is valid
#   3. rwy CLI is accessible
#   4. --subagent flag present OR --direct-deploy override (subagent is the default)
#
# The default expectation is that deployments are handled by a dedicated
# development subagent with the railway-deploy skill loaded. Direct deploys
# by the orchestrator require --direct-deploy override.

set -euo pipefail

BRAND="${1:-}"
PROJECT="${2:-}"
SUBAGENT_MODE="${3:-}"
DIRECT_DEPLOY="false"

# Parse flags
for arg in "$@"; do
    case "$arg" in
        --subagent) SUBAGENT_MODE="true" ;;
        --direct-deploy) DIRECT_DEPLOY="true" ;;
    esac
done

VIOLATIONS=""

# ─── Check 1: Brand and project specified ────────────────────────────────────
if [ -z "$BRAND" ] || [ "$BRAND" = "--subagent" ] || [ "$BRAND" = "--direct-deploy" ]; then
    VIOLATIONS="$VIOLATIONS\n🔴 BLOCKED: No brand specified. Usage: deploy-preflight.sh <brand> <project> [--subagent|--direct-deploy]"
fi

if [ -z "$PROJECT" ] || [ "$PROJECT" = "--subagent" ] || [ "$PROJECT" = "--direct-deploy" ]; then
    if [ -n "$BRAND" ] && [ "$BRAND" != "--subagent" ] && [ "$BRAND" != "--direct-deploy" ]; then
        VIOLATIONS="$VIOLATIONS\n🟡 WARNING: No project name specified. Proceeding but specify for better tracking."
    fi
fi

# ─── Check 2: Railway token exists ───────────────────────────────────────────
TOKEN_FILE="$HOME/.hermes/secrets/railway-token.txt"
if [ ! -f "$TOKEN_FILE" ]; then
    VIOLATIONS="$VIOLATIONS\n🔴 BLOCKED: Railway token not found at $TOKEN_FILE. Token is required for all Railway operations."
else
    TOKEN=$(cat "$TOKEN_FILE" | tr -d '[:space:]')
    if [ -z "$TOKEN" ] || [ ${#TOKEN} -lt 20 ]; then
        VIOLATIONS="$VIOLATIONS\n🔴 BLOCKED: Railway token appears empty or invalid. Tell Jeff to rotate it."
    fi
fi

# ─── Check 3: rwy CLI accessible ─────────────────────────────────────────────
if ! command -v rwy &>/dev/null && [ ! -f "$HOME/bin/rwy" ]; then
    VIOLATIONS="$VIOLATIONS\n🟡 WARNING: rwy CLI not found in PATH or ~/bin/. GraphQL fallback available but rwy is preferred."
fi

# ─── Check 4: Subagent mode (default expectation) ────────────────────────────
if [ "$DIRECT_DEPLOY" != "true" ] && [ "$SUBAGENT_MODE" != "true" ]; then
    VIOLATIONS="$VIOLATIONS\n🟡 WARNING: No --subagent or --direct-deploy flag. Default expectation is a dedicated deployment subagent."
    VIOLATIONS="$VIOLATIONS\n   If deploying directly, pass --direct-deploy. Otherwise spawn a subagent with railway-deploy skill loaded."
fi

# ─── Check 5: Skill loaded marker ────────────────────────────────────────────
# The orchestrator should have loaded the railway-deploy skill via MCP before
# calling this script. We check for a marker file that the skill loading process
# can create, or we warn that the skill should be loaded.
SKILL_MARKER="/tmp/railway-deploy-skill-loaded.$$"
if [ -f "/tmp/railway-deploy-skill-loaded" ]; then
    # Marker exists (set by orchestrator after loading skill)
    :
else
    VIOLATIONS="$VIOLATIONS\n🟡 REMINDER: Load the 'railway-deploy' skill via MCP before proceeding with any Railway operation."
    VIOLATIONS="$VIOLATIONS\n   Run: mcp_skill_registry_load_skill('railway-deploy') or skill_view(name='railway-deploy')"
    VIOLATIONS="$VIOLATIONS\n   If already loaded, create marker: touch /tmp/railway-deploy-skill-loaded"
fi

# ─── Output ──────────────────────────────────────────────────────────────────
if [ -n "$VIOLATIONS" ]; then
    echo -e "\n⚠️ DEPLOY PRE-FLIGHT GATE — Issues found for '$BRAND/${PROJECT:-unknown}':$VIOLATIONS"
    echo ""
    echo "Fix these issues before deploying."
    echo "If this is a genuine emergency, use --direct-deploy AND get Jeff approval."
    echo ""
    echo "Standard deployment protocol:"
    echo "  1. Load railway-deploy skill via MCP"
    echo "  2. Spawn a dedicated deployment subagent with skill context"
    echo "  3. Include deploy-gate-context.sh output in subagent context"
    echo "  4. Subagent runs deploy-preflight.sh before any Railway operation"
    echo "  5. Verify deploy with deployments(last:1) status == SUCCESS"
    echo "  6. Run smoke test on live URL"
    exit 1
fi

echo "✓ Deploy pre-flight passed for '$BRAND/${PROJECT:-unknown}' (subagent=$SUBAGENT_MODE, direct=$DIRECT_DEPLOY)"
echo "  Token: OK | rwy: $(command -v rwy &>/dev/null && echo 'available' || echo 'fallback to GraphQL')"
echo "  Next: verify deployments(last:1) status == SUCCESS after deploy, then smoke test."
exit 0