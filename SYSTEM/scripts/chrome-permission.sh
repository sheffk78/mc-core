#!/bin/bash
# chrome-permission.sh — Browser permission token for computer_use (Kenneth directive 2026-09-04)
#
# Supersedes the 2026-08-26 browser-isolation HARD BLOCK. computer_use on browser
# apps (Chrome/Safari/etc.) is now allowed WITH Kenneth's explicit permission.
# Kenneth grants permission in Discord → the agent runs `grant` → a token file
# unlocks browser-targeted computer_use calls in the computer-use-lock plugin
# until it expires. No token → those calls are blocked and the agent must ask.
#
# Usage:
#   chrome-permission.sh grant [<minutes>]   # Grant browser permission (default 120min)
#   chrome-permission.sh status              # Show current permission state
#   chrome-permission.sh revoke              # Revoke permission immediately
#
# Token file: /tmp/chrome-permission.json (must match PERMISSION_FILE in the plugin)

set -u

PERMISSION_FILE="/tmp/chrome-permission.json"
PLUGIN_CONSTS="$HOME/.hermes/plugins/computer-use-lock/__init__.py"

# Keep TTL in sync with the plugin's PERMISSION_TTL_MIN constant
DEFAULT_TTL_MIN=$(grep -m1 'PERMISSION_TTL_MIN = ' "$PLUGIN_CONSTS" 2>/dev/null | sed 's/.*= \([0-9]*\).*/\1/')
DEFAULT_TTL_MIN="${DEFAULT_TTL_MIN:-120}"

now=$(date +%s)

case "${1:-status}" in
    grant)
        minutes="${2:-$DEFAULT_TTL_MIN}"
        if ! [[ "$minutes" =~ ^[0-9]+$ ]] || [ "$minutes" -lt 1 ]; then
            echo "ERROR: minutes must be a positive integer (got '$minutes')" >&2
            exit 1
        fi
        expires=$((now + minutes * 60))
        granted=$(date "+%Y-%m-%d %H:%M:%S")
        expires_h=$(date -r "$expires" "+%Y-%m-%d %H:%M:%S" 2>/dev/null)
        cat > "$PERMISSION_FILE" <<EOF
{"granted": ${now}, "expires": ${expires}, "ttl_min": ${minutes}, "granted_by": "kenneth", "granted_at": "${granted}"}
EOF
        chmod 600 "$PERMISSION_FILE" 2>/dev/null
        echo "GRANTED: browser computer_use permitted until ${expires_h:-epoch $expires} (${minutes}min)"
        echo "Token: ${PERMISSION_FILE}"
        ;;

    revoke)
        if [ -f "$PERMISSION_FILE" ]; then
            rm -f "$PERMISSION_FILE"
            echo "REVOKED: browser permission cleared"
        else
            echo "No permission token present (already revoked/expired)"
        fi
        ;;

    status)
        if [ ! -f "$PERMISSION_FILE" ]; then
            echo "NO PERMISSION — browser computer_use is blocked; ask Kenneth in Discord, then run: $0 grant"
            exit 0
        fi
        expires=$(python3 -c "import json;print(json.load(open('$PERMISSION_FILE'))['expires'])" 2>/dev/null) || expires=0
        if [ "$expires" -lt "$now" ]; then
            echo "EXPIRED — browser computer_use is blocked; re-grant with: $0 grant"
            rm -f "$PERMISSION_FILE"
            exit 0
        fi
        remaining=$(( (expires - now + 59) / 60 ))
        granted_at=$(python3 -c "import json;d=json.load(open('$PERMISSION_FILE'));print(d.get('granted_at','?'))" 2>/dev/null)
        echo "ACTIVE — browser computer_use permitted (~${remaining}min remaining, granted ${granted_at})"
        ;;
    *)
        echo "Usage: $0 {grant [<minutes>] | status | revoke}"
        exit 2
        ;;
esac