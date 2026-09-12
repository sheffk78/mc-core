#!/bin/bash
# deploy-gate-context.sh — Generate the deployment gate protocol context block for subagents.
# 
# Usage:
#   deploy-gate-context.sh <brand> <project> [service-name]
#
# Outputs a context string that MUST be appended to any subagent goal/context
# that involves Railway deployment. This ensures subagents automatically:
#   1. Load the railway-deploy skill before any Railway operation
#   2. Run the deploy-preflight gate
#   3. Follow the correct deployment sequence
#   4. Verify and smoke-test after deploy
#
# This is the deployment equivalent of browser-gate-context.sh.
# MANDATORY for all deployment subagent delegations per AGENTS.md.

BRAND="${1:-}"
PROJECT="${2:-}"
SERVICE="${3:-}"

if [[ -z "$BRAND" ]] || [[ -z "$PROJECT" ]]; then
    echo "Usage: deploy-gate-context.sh <brand> <project> [service-name]"
    exit 2
fi

echo "DEPLOYMENT GATE PROTOCOL (mandatory — violations cause failed deployments and Jeff corrections):"
echo ""
echo "## STEP 1: LOAD THE RAILWAY-DEPLOY SKILL — BEFORE ANYTHING ELSE"
echo "  Before any Railway operation, you MUST load the railway-deploy skill:"
echo "    mcp_skill_registry_load_skill('railway-deploy')"
echo "  Do NOT attempt Railway operations without the skill loaded. Do NOT freestyle deployments."
echo "  The skill contains: token location, rwy CLI commands, GraphQL patterns, project IDs,"
echo "  deployment verification steps, and troubleshooting guides."
echo ""
echo "## STEP 2: RUN THE DEPLOY PRE-FLIGHT GATE"
echo "  bash ~/.openclaw/workspace/SYSTEM/scripts/deploy-preflight.sh '${BRAND}' '${PROJECT}' --subagent"
echo "  If BLOCKED → fix the issue before proceeding. Do NOT skip this gate."
echo ""
echo "## STEP 3: RAILWAY CLI IS PERMANENTLY DISABLED"
echo "  NEVER use 'railway up', 'railway init', 'railway link', or any railway CLI commands."
echo "  Use 'rwy' CLI (~/bin/rwy) or GraphQL via curl to backboard.railway.app/graphql/v2."
echo "  Token: ~/.hermes/secrets/railway-token.txt"
echo ""
echo "## STEP 4: DEPLOYMENT SEQUENCE"
if [[ -n "$SERVICE" ]]; then
    echo "  Service: ${SERVICE}"
fi
echo "  a. Verify access: rwy whoami (should show jeff@socialize.video)"
echo "  b. Check current status: rwy status ${PROJECT}"
echo "  c. Deploy: git push (if auto-deploy) OR rwy deploy ${PROJECT}/${SERVICE} --commit <SHA> --yes"
echo "  d. Wait for deploy: poll deployments until status == SUCCESS"
echo "  e. Verify: rwy deployments ${PROJECT}/${SERVICE:-service} --n 1"
echo "  f. Smoke test: curl the health endpoint or live URL"
echo "  g. Report: deployment URL, commit SHA, and verification result"
echo ""
echo "## STEP 5: VERIFY OR FAIL"
echo "  A deployment is NOT complete until:"
echo "    - deployments(last:1) shows status == SUCCESS"
echo "    - Health check returns 200/OK"
echo "    - No build errors in deployment logs"
echo "  If any check fails, diagnose and fix before reporting back."
echo "  Do NOT report 'deployed' without verification. Jeff has corrected this multiple times."
echo ""
echo "## KEY FILES"
echo "  - Skill: ~/.hermes/skills/devops/railway-deploy/SKILL.md"
echo "  - Token: ~/.hermes/secrets/railway-token.txt"
echo "  - rwy CLI: ~/bin/rwy"
echo "  - Preflight: ~/.openclaw/workspace/SYSTEM/scripts/deploy-preflight.sh"
echo "  - Full guide: ~/.openclaw/workspace/TOOLS/railway-deploy.md"
echo ""
echo "## ANTI-PATTERNS (DO NOT DO THESE)"
echo "  - Using 'railway' CLI commands (permanently disabled)"
echo "  - Deploying without loading railway-deploy skill first"
echo "  - Trusting upstreamUrl without checking deployment status"
echo "  - Reporting 'deployed' without health check verification"
echo "  - Skipping the deploy-preflight gate"
echo "  - Freestyling deployment steps from memory instead of following the skill"