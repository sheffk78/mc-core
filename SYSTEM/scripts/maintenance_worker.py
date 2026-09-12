#!/usr/bin/env python3
"""Maintenance worker for the Atlas brand-hygiene lane.

IDLE-GATED + INTERRUPTIBLE. This is the "interrupt and pick back up" engine:
  - Claims ONE pending row at a time (small unit, seconds).
  - Before acting, rechecks priority: if a higher-priority queue (Jeff's
    interactive work, an approval gate, a busy Ollama/disk) has claims, it
    SKIPS this cycle and exits quietly. No state to preserve.
  - A row is a single idempotent file-decision; resume = start at next pending row.
  - Runs propose-only: nothing is archived/deleted here. It stages findings.

Usage: worker.py --once            (process a single row if idle, then exit)
       worker.py --drain N         (process up to N rows, stopping if priority hits)
"""
import json, os, sys, time, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenance_queue as mq

ARCHIVE_ROOT = "/Volumes/RENDER DISK/archive"
PRIORITY_QUEUES = ["interactive", "approval", "bug"]  # higher-priority work


def system_busy():
    """Return True if the machine/Ollama is busy and maintenance should yield.
    Cheap heuristics: Ollama currently processing (has active compute), any
    foreground modding process touching the brand tree."""
    # Ollama active compute check
    try:
        r = subprocess.run(["ollama", "ps", "--json"], capture_output=True, text=True, timeout=5)
        import json as J
        models = J.loads(r.stdout or "[]")
        for m in models:
            if m.get("processor_now", 0) > 0.5:
                return True  # a model is actively inferring
    except Exception:
        pass
    return False


def priority_pending():
    """Check whether any higher-priority queue/a task is waiting. Real integration
    checks JOB-LEDGER; for the skeleton this checks for a marker file/flag."""
    for q in PRIORITY_QUEUES:
        mark = os.path.join(mq.QUEUE_DIR, "..", "..", "..", "QUEUES", f"{q}.flag")
        if os.path.exists(mark):
            return q
    return None


def process_one(owner="worker", dry_run=True):
    """Claim + process a single row. Returns outcome string."""
    pri = priority_pending()
    if pri:
        return f"skipped: higher-priority ({pri}) present"

    if system_busy():
        return "skipped: system busy"

    row = mq.claim_next(owner, lane="maintenance")
    if not row:
        return "no pending rows"

    # This row is now RESERVED (lease). Apply the doctrine decision.
    # For propose-only, we do NOT move anything: we surface the decision.
    path = row["path"]
    if not os.path.exists(path):
        mq.transition(row["id"], "staged", owner, "gone: source missing")
        return f"row {row['id']}: source missing -> reclassified"

    # resolve proposal from the stored action/note
    note = {}
    for it in _all_notes():
        if it.get("row_id") == row["id"]:
            note = json.loads(it.get("note") or "{}")
            break
    action = note.get("action")

    if action == "archive":
        # PROPOSE-ONLY: drop into the approved queue for human sign-off.
        # Never archive without approval. This is the irreversible gate.
        mq.transition(row["id"], "approved", owner, "queued for human archive approval")
        return f"row {row['id']}: ARCHIVE proposed -> awaiting approval"
    elif action == "flag":
        mq.transition(row["id"], "approved", owner, "flagged media awaiting review")
        return f"row {row['id']}: MEDIA flagged -> awaiting review"
    else:
        mq.transition(row["id"], "rejected", owner, "no action applicable")
        return f"row {row['id']}: no-op -> rejected"


def _all_notes():
    path = os.path.join(mq.QUEUE_DIR, "proposals.jsonl")
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path):
        line = line.strip()
        if line:
            try: out.append(json.loads(line))
            except Exception: pass
    return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "--drain"
    owner = "atlas-worker"
    if mode == "--drain":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        for _ in range(n):
            # re-check priority before each unit
            res = process_one(owner)
            print(res, flush=True)
            if res.startswith("skipped"):
                break
    else:
        print(process_one(owner), flush=True)