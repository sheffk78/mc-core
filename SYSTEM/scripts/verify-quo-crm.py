#!/usr/bin/env python3
"""
Verification suite for the Quo→CRM wiring (2026-09-04).

Covers the four changed paths:
  - SYSTEM/crm/crm-log.py      (write + dedup + cleanup)
  - SYSTEM/crm/crm.py          (_norm_phone contract + live contact match)
  - SYSTEM/crm/crm-ingest.py   (quo dry-run clean against live API)
  - ~/.hermes/webhook_subscriptions.json (route config integrity)

Usage: python3 verify-quo-crm.py
Exit 0 = all pass, 1 = any fail.
"""

import json
import os
import sqlite3
import subprocess
import sys

CRM_DIR = os.path.expanduser("~/.openclaw/workspace/SYSTEM/crm")
SUBS = os.path.expanduser("~/.hermes/webhook_subscriptions.json")
QUO_KEY = "a599a60168146331561e5c677bc8cbc8d0adf2f856009bb5969764a41e7c3e2a"

PASS, FAIL = "PASS", "FAIL"
results = []


def _run(args, cwd=CRM_DIR, timeout=90, tries=3):
    """subprocess.run with retries — this Mac throws transient
    fork_exec TypeErrors under heavy agent load; identical calls
    succeed on retry."""
    last = None
    for attempt in range(tries):
        try:
            return subprocess.run(args, capture_output=True, text=True,
                                  cwd=cwd, timeout=timeout)
        except TypeError as e:
            last = e
    assert last is not None
    raise last


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))


sys.path.insert(0, CRM_DIR)
from crm import CRM  # noqa: E402

# ── T1: crm-log.py write + dedup + cleanup ──
import time as _time
evt = {
    "brand": "trustoffice", "channel": "phone", "direction": "inbound",
    "subject": "VERIFY missed call", "content_summary": "verification row",
    "thread_id": f"CNverify{_time.time_ns()}", "sent_at": "2026-09-05T00:00:00Z",
    "status": "missed", "contact_phone": "+19995550001",
}
r1 = _run(["python3", "crm-log.py", json.dumps(evt)], timeout=60)
a = json.loads(r1.stdout or "{}")
r2 = _run(["python3", "crm-log.py", json.dumps(evt)], timeout=60)
b = json.loads(r2.stdout or "{}")
check("crm-log.py write + dedup (same id, second call skipped)",
      a.get("logged") and b.get("skipped") and a.get("id") == b.get("id"),
      f"id={a.get('id', '-')}")

conn = sqlite3.connect(os.path.join(CRM_DIR, "crm.db"))
ids = [r[0] for r in conn.execute("SELECT id FROM interactions WHERE thread_id = ?", (evt["thread_id"],))]
for iid in ids:
    row = conn.execute("SELECT contact_id FROM interactions WHERE id = ?", (iid,)).fetchone()
    conn.execute("DELETE FROM interactions WHERE id = ?", (iid,))
    if row and row[0]:
        conn.execute("DELETE FROM contact_aliases WHERE contact_id = ?", (row[0],))
        conn.execute("DELETE FROM contacts WHERE id = ?", (row[0],))
conn.commit()

# ── T2: _norm_phone contract ──
cases = [
    ("+18023490647", "+18023490647"),
    ("+1 (802) 349-0647", "+18023490647"),
    ("+180****0647", "+180*0647"),
    (None, None),
    ("", None),
]
bad = [c for c in cases if CRM._norm_phone(c[0]) != c[1]]
check("_norm_phone contract (5 cases)", not bad, f"failures={bad}" if bad else "")

# ── T3: real caller number from live Quo API → CRM contact match ──
rp = _run(["curl", "-s", "--max-time", "20",
    "https://api.quo.com/v1/conversations?phoneNumbers=PNBvrXRYlq&maxResults=5",
    "-H", f"Authorization: {QUO_KEY}"], timeout=30)
p = json.loads(rp.stdout)["data"][0]["participants"][0]
hit = CRM().lookup(phone=p)
c = (hit or {}).get("contact") or {}
check("real API caller number → CRM contact match",
      bool(c), f"brands={c.get('brands')} interactions={len((hit or {}).get('interactions', []))}")

# ── T4: crm-ingest --quo-only dry-run clean against live API ──
ri = _run(["python3", "crm-ingest.py", "--quo-only", "--dry-run"], timeout=150)
check("crm-ingest --quo-only --dry-run exits 0, zero errors",
      ri.returncode == 0 and "Errors: 0" in ri.stdout,
      f"rc={ri.returncode}")

# ── T5: route config integrity ──
d = json.load(open(SUBS))
qc = d.get("quo-calls", {})
check("quo-calls route: toolsets/deliver/events/prompt intact",
      qc.get("toolsets") == ["terminal"]
      and qc.get("deliver") == "discord:1487501340086108300"
      and len(qc.get("events", [])) == 10
      and "crm-log.py" in qc.get("prompt", "")
      and "PNsamplephonenumber" in qc.get("prompt", ""))

# ── report ──────────────────────────────────────────────
print(f"{'=' * 60}\nQuo→CRM verification — {len(results)} checks\n{'=' * 60}")
fail = 0
for name, ok, detail in results:
    if not ok:
        fail += 1
    print(f"{PASS if ok else FAIL} — {name}" + (f" | {detail}" if detail else ""))
print(f"{'=' * 60}\n{len(results) - fail}/{len(results)} passed")
sys.exit(1 if fail else 0)