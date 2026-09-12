#!/usr/bin/env python3
"""
TJB Google Play Console review-status watchdog.

Script-only detect-and-defer monitor (CRON-ALTERNATIVE-FRAMEWORK pattern):
- Reuses an existing Play Console tab for this app in the agent headless Chrome
  (CDP 9222), navigating it to Publishing overview if needed; opens a new tab otherwise.
- Reads the review-status banner (visible text only) from Publishing overview.
- Silent (empty stdout) unless the status CHANGES vs the state file -> zero-cost when idle.
- On change: prints a short status line (cron delivers verbatim) + writes a report file.

Deploy: copy to ~/.hermes/scripts/play-review-watchdog.py (cron executes that copy).
State:  ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/state/play-review-state.json
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import websocket  # websocket-client

APP_URL = "https://play.google.com/console/u/0/developers/7073800881508405551/app/4972601950486224295/publishing"
APP_ID = "4972601950486224295"
STATE_PATH = os.path.expanduser(
    "~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/state/play-review-state.json"
)
REPORT_DIR = os.path.expanduser(
    "~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/reports"
)
CDP = "http://127.0.0.1:9222"

KNOWN_STATUSES = {
    "IN_REVIEW": "Changes are in review (waiting on Google).",
    "READY_TO_SEND": "Changes need sending for review (action required).",
    "READY_TO_PUBLISH": "APPROVED - ready to publish. Managed publishing is ON: go live via Publishing overview -> Publish changes (Kit can click it).",
    "LIVE": "APPROVED AND LIVE on Google Play.",
    "REJECTED": "REJECTED - needs action in console.",
    "IDLE_NOTHING_PENDING": "Idle — nothing pending with Google; last published build is live.",
}


def cdp_json(path):
    with urllib.request.urlopen(f"{CDP}{path}", timeout=10) as r:
        return json.loads(r.read().decode())


def open_new_tab():
    """Open a new tab at APP_URL (/json/new requires PUT on modern Chrome)."""
    req = urllib.request.Request(
        f"{CDP}/json/new?{urllib.parse.quote(APP_URL, safe='')}", method="PUT")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def main():
    # Transient-infra guard (Sep 9 fix): if CDP is unreachable, the Chrome
    # daemon is restarting (e.g. ensure-chrome-awake mid-boot) or the display
    # is asleep. Exit SILENT (rc=0) so the cron doesn't page a false alarm;
    # the next tick re-checks normally. Only a real read (page reachable,
    # status classified) may alert.
    try:
        cdp_json("/json")
    except Exception:
        return 0  # transient infra hiccup — silent retry next tick

    ws_url = next(
        (t.get("webSocketDebuggerUrl") for t in cdp_json("/json")
         if t.get("type") == "page" and APP_ID in t.get("url", "")),
        None,
    )
    if not ws_url:
        try:
            ws_url = open_new_tab().get("webSocketDebuggerUrl")
            time.sleep(2)
        except Exception:
            return 0  # could not open/reuse a tab — transient; silent retry next tick

    try:
        ws = websocket.create_connection(ws_url, timeout=30, suppress_origin=True)
    except Exception:
        return 0  # transient websocket error — silent retry next tick

    def eval_js(expr, timeout=30):
        ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {
            "expression": expr, "returnByValue": True}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = json.loads(ws.recv())
            if msg.get("id") == 2:
                res = msg.get("result", {}).get("result", {})
                return res.get("value") if res.get("type") == "string" else None
        return None

    try:
        page_url = eval_js("location.href")
        if page_url is None:
            return 0  # tab crashed/unresponsive — silent retry next tick
        if "play.google.com/console" not in page_url or "/publishing" not in page_url:
            eval_js(f"location.href={APP_URL!r}")
            time.sleep(8)

        # Wait (bounded) for the status banner, then classify from VISIBLE text only.
        # body.innerText excludes hidden DOM (the page hides template sections like
        # 'Changes ready to publish' and program badges like 'Teacher Approved' that
        # textContent would falsely surface).
        banner_line = None
        txt = ""
        for _ in range(6):  # ~30s bounded wait
            time.sleep(5)
            txt = eval_js("document.body?document.body.innerText:''") or ""
            # Post-rejection the page shows BOTH the 'Some recent changes were
            # rejected' card and a 'Your changes can now be sent for review'
            # banner. The rejection card is the dominant truth — check it FIRST,
            # otherwise the banner wins and a rejection reads as READY_TO_SEND
            # (the exact Sep 4-6 blind spot).
            if "recent changes were rejected" in txt.lower():
                banner_line = "Some recent changes were rejected (rejection card present)"
                break
            lines = [l.strip() for l in txt.splitlines()
                     if l.strip().lower().startswith("your changes")]
            if lines:
                banner_line = " | ".join(lines)
                break
        body_len = len(txt)

        # Idle-state detection (Sep 9 fix): when NOTHING is pending with Google,
        # the page shows no banner at all — just the empty 'Changes ready to
        # publish' explainer + a 'Last published on ...' date. That is a real,
        # stable state and must classify as IDLE, not UNKNOWN (the old behavior
        # flagged UNKNOWN with a body-length suffix that changed run to run,
        # producing spurious alerts).
        if banner_line is None and body_len >= 200:
            idle_markers = [
                "changes ready to publish will appear here",
                "changes that are ready to publish will appear here",
            ]
            if any(m in txt.lower() for m in idle_markers):
                banner_line = "No changes pending — 'Changes ready to publish' empty (idle)"

        def canon(banner):
            b = (banner or "").lower()
            if "no changes pending" in b or "changes ready to publish will appear here" in b:
                return "IDLE_NOTHING_PENDING"
            # Order matters: rejection card text (and the post-rejection
            # 'Your changes can now be sent for review' banner) must classify as
            # REJECTED / READY_TO_SEND BEFORE the generic "in review" check,
            # which would otherwise match '...now in review' patterns and
            # misreport a rejection as IN_REVIEW (the Sep 4-6 blind spot).
            if "recent changes were rejected" in b or "update rejected" in b:
                return "REJECTED"
            if "ready to send" in b or "can now be sent" in b:
                return "READY_TO_SEND"
            if "ready to publish" in b:
                return "READY_TO_PUBLISH"
            if "have been published" in b or "available on google play" in b:
                return "LIVE"
            if "in review" in b or "sent for review" in b:
                return "IN_REVIEW"
            return "UNKNOWN"

        now = time.strftime("%Y-%m-%d %H:%M:%S %Z")
        new_key = canon(banner_line)
        if new_key == "UNKNOWN":
            if body_len < 200:
                return 0  # page not loaded / signed out -> silent, not a change
            # Stable key (Sep 9 fix): exclude body length — it varies run to run
            # (cookie banners, lazy-loaded rows) and made UNKNOWN re-alert.
            new_key = f"UNKNOWN ({banner_line or 'no banner found'})"

        prev = None
        if os.path.exists(STATE_PATH):
            try:
                with open(STATE_PATH) as f:
                    prev = json.load(f).get("status_text")
            except Exception:
                prev = None

        if new_key == prev:
            return 0  # unchanged -> silent

        # STATUS CHANGED -> report
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w") as f:
            json.dump({"status_text": new_key, "checked_at": now, "raw": banner_line}, f)
        os.makedirs(REPORT_DIR, exist_ok=True)
        rep = os.path.join(REPORT_DIR, f"play-review-status-{time.strftime('%Y%m%d-%H%M%S')}.md")
        friendly = KNOWN_STATUSES.get(new_key, "Status changed - check console.")
        with open(rep, "w") as f:
            f.write(
                f"# TJB Google Play review status change\n\n"
                f"- When: {now}\n- Marker: {new_key}\n- Meaning: {friendly}\n"
                f"- Console: {APP_URL}\n\nIf approved AND 'Managed publishing on' is still shown, "
                f"go live = Publishing overview -> Publish changes (Kit can click it).\n"
            )
        # L7 CONTINUOUS AUDIT: confirmed production outcomes feed the failure
        # library standing feed (outcomes.jsonl). Kit converts pending outcomes
        # into replayable cases on next library touch (failure-library.py outcomes).
        # Seeding must never break the watchdog's alerting function.
        try:
            outcomes_path = os.path.expanduser(
                "~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/projects/"
                "truejoybirthing-website/scripts/failure-library/outcomes.jsonl")
            os.makedirs(os.path.dirname(outcomes_path), exist_ok=True)
            outcome = {
                "date": time.strftime("%Y-%m-%d"),
                "source": "play-review-watchdog",
                "status": new_key,
                "raw": banner_line,
                "report": rep,
                "converted_to_case": False,
            }
            with open(outcomes_path, "a") as f:
                f.write(json.dumps(outcome) + "\n")
        except Exception as e:
            print(f"WARNING: outcome feed write failed (watchdog unaffected): {e}")
        print(f"🔔 TJB Play review status: {new_key} ({now})")
        print(friendly)
        print(f"Report: {rep}")
        return 0
    finally:
        ws.close()


if __name__ == "__main__":
    sys.exit(main())