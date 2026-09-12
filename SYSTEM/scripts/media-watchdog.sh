#!/bin/bash
# media-watchdog.sh — self-healing media pipeline monitor (script-only, no LLM)
#
# Runs health checks on the QNAP media pipeline; AUTO-HEALS known-recoverable
# failures (errored torrents, dead stalls); prints alert lines ONLY when a
# problem remains after healing. Empty stdout = healthy = silent cron delivery.
#
# Install: hermes cron create "0 8,14,20 * * *" --script <this file> --no-agent \
#            --name media-watchdog --deliver discord:1539771958089093220
# (3x/day script-only monitor — within cron framework limits; #openclaw per
#  AGENTS.md Cron Channel Targeting Rule: infra/agent-internal signals)
# NOTE: credentials come from ~/.hermes/secrets/qnap-media.json — never inline.

ENGINE="$HOME/.openclaw/workspace/SYSTEM/scripts/media-engine.py"
ALERT_LOG="$HOME/.openclaw/workspace/SYSTEM/media/alerts.log"

# ensure alert-log dir exists (2026-09-08: missing dir crashed the script mid-alert
# and mangled the Discord delivery — alert must never die on a logging failure)
mkdir -p "$(dirname "$ALERT_LOG")" 2>/dev/null || true

# 1) auto-heal pass (rate-limited inside the engine)
HEAL_OUT=$(python3 "$ENGINE" heal 2>&1)
HEAL_RC=$?
if [ $HEAL_RC -eq 2 ]; then
    echo "🔴 MEDIA WATCHDOG: engine unreachable (qBittorrent/NAS down?): $HEAL_OUT"
    exit 1
fi

# 1b) restore polite download cap when queue fully drains (was raised to 12 for mass recovery)
ACTIVE=$(python3 "$ENGINE" status --json 2>/dev/null | python3 -c "import json,sys
try: d=json.load(sys.stdin); print(len(d.get('active',[])))
except Exception: print(-1)")
if [ "$ACTIVE" = "0" ]; then
    NOTICE=$(python3 - <<'PYEOF' 2>/dev/null
import json, urllib.request, urllib.parse
SECRETS = __import__("pathlib").Path(__import__("os").path.expanduser("~/.hermes/secrets/qnap-media.json"))
c = json.loads(SECRETS.read_text())
BASE = "http://192.168.1.221:8081"
data = urllib.parse.urlencode({"username": c["qb_user"], "password": c["qb_pass"]}).encode()
resp = urllib.request.urlopen(urllib.request.Request(BASE + "/api/v2/auth/login", data=data), timeout=10)
cj = resp.headers.get("Set-Cookie", "").split(";")[0]
req = urllib.request.Request(BASE + "/api/v2/app/preferences", headers={"Cookie": cj})
prefs = json.loads(urllib.request.urlopen(req, timeout=15).read())
if prefs.get("max_active_downloads", 4) > 4:
    # setPreferences takes FORM-ENCODED json=<string>, not a raw JSON body (400 otherwise)
    body = urllib.parse.urlencode({"json": json.dumps({"max_active_downloads": 4})}).encode()
    urllib.request.urlopen(urllib.request.Request(BASE + "/api/v2/app/setPreferences", data=body, headers={"Cookie": cj}), timeout=15)
    print("drained: restored max_active_downloads to 4")
PYEOF
)
    # cap restore is routine infra state, not an alert: log it, keep stdout clean
    # (write must never crash the script — 2026-09-08 lesson)
    if [ -n "$NOTICE" ]; then
        echo "$(date '+%m-%d %H:%M') $NOTICE" >> "$ALERT_LOG" 2>/dev/null || true
    fi
fi

# 2) health check after healing; non-empty stdout = problem survived = alert
OUT=$(python3 "$ENGINE" health 2>/dev/null)
RC=$?

# 2b) Mac-side last-resort repair (2026-09-08): if ONLY Plex is down (qBt fine),
# the NAS-side plex-license-guard.sh failed its job — try the repair from here
# via SSH before alerting. Covers guard-script breakage itself.
if [ $RC -ne 0 ] && echo "$OUT" | grep -q "Plex :32400 not responding" && ! echo "$OUT" | grep -q "qBittorrent"; then
    PW=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.hermes/secrets/qnap-media.json')))['nas_pass'])" 2>/dev/null)
    if [ -n "$PW" ]; then
        sshpass -p "$PW" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 admin@192.168.1.221 \
            "export PATH=/bin:/sbin:/usr/bin:/usr/sbin:\$PATH; sed -i '/^\[PlexMediaServer\]/,/^\[/ s/Enable = FALSE/Enable = TRUE/' /etc/config/qpkg.conf; /etc/init.d/plex.sh start >/dev/null 2>&1" \
            >/dev/null 2>&1
        sleep 45
        OUT=$(python3 "$ENGINE" health 2>/dev/null)
        RC=$?
        [ $RC -eq 0 ] && echo "$(date '+%m-%d %H:%M') mac-side plex repair succeeded" >> "$ALERT_LOG" 2>/dev/null
    fi
fi

if [ $RC -ne 0 ]; then
    echo "⚠️ MEDIA PIPELINE ALERT (auto-heal ran, issue persists):"
    echo "$OUT"
    echo "Kit: see SYSTEM/media/alerts.log for heal history; dead swarms need a replacement source (torrents-csv search)."
    exit 1
fi

# healthy — silent (empty stdout suppressed by cron delivery)
exit 0