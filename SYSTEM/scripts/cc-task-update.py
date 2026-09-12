#!/usr/bin/env python3
"""
cc-task-update.py — Kit loop-closure: report task progress to the Command Center.

Stage 2 of the note funnel: when Kit picks up a task note, PATCH the CC API so
Kenneth sees "Kit: in progress · 3m" / "Kit: done ✓" on the card immediately.
Direct API PATCH — the pending-notes queue is for Kenneth→Kit direction only.

Usage:
  cc-task-update.py <task_id> in_progress ["one-line note"]
  cc-task-update.py <task_id> done ["one-line note"]

Auth: COMMAND_CENTER_API_KEY from ~/.hermes/.env (same key as the backend).
Target: http://127.0.0.1:8001 (local backend via launchd). Override with
CC_API_BASE for testing.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV_FILE = Path.home() / ".hermes" / ".env"
DEFAULT_BASE = "http://127.0.0.1:8001"
VALID_STATUSES = ("in_progress", "done")


def api_key() -> str:
    try:
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("COMMAND_CENTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 2 or args[1] not in VALID_STATUSES:
        print("usage: cc-task-update.py <task_id> <in_progress|done> [note]", file=sys.stderr)
        return 2
    task_id, status = args[0], args[1]
    note = args[2].strip() if len(args) > 2 else ""

    key = api_key()
    if not key:
        print("ERROR: COMMAND_CENTER_API_KEY not found in ~/.hermes/.env", file=sys.stderr)
        return 1

    base = DEFAULT_BASE
    try:
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("CC_API_BASE="):
                base = line.split("=", 1)[1].strip().strip('"')
                break
    except Exception:
        pass

    url = f"{base}/command-center/tasks/{urllib.parse.quote(task_id, safe='')}/kit-status"
    payload = json.dumps({"status": status, **({"note": note} if note else {})}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="PATCH",
        headers={"Content-Type": "application/json", "X-API-Key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
        print(f"CC updated: {task_id} → Kit: {body.get('kit_loop_status')}"
              + (f" · {body.get('kit_loop_note')}" if body.get("kit_loop_note") else ""))
        return 0
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = json.loads(exc.read().decode()).get("detail", "")
        except Exception:
            pass
        print(f"ERROR: HTTP {exc.code} {detail}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())