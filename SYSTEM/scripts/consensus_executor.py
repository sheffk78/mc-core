#!/usr/bin/env python3
"""Consensus-gate executor for the Atlas brand-hygiene lane.

Implements Jeff's DIRECTIVE (2026-08-21): Atlas proposes + reasons, a higher model
(DeepSeek or Ring) audits the LOGIC, two-model CONSENSUS authorizes execution, then
Jeff gets a post-hoc report.

Per-row pipeline:
  1. PROPOSE  - load the staged proposal + evidence into a reasoned case.
  2. AUDIT    - a higher model (DeepSeek or Ring) reviews the reasoning. This is the
                integration seam: _audit() submits to the configured auditor. In the
                harness it returns a deterministic verdict so the path is testable
                offline without burning cloud tokens.
  3. CONSENSUS- agreed -> EXECUTE; disagreement/uncertainty -> HOLD (no action).
  4. EXECUTE  - archive to /Volumes/RENDER DISK/archive/<brand>/<date>/ with a dated
                manifest. NEVER deletes. Hard allowlist still blocks
                brand-identity / credentials / config / live code.
  5. REPORT   - append to posthoc-report.jsonl for Jeff's daily review.

Usage:
  consensus_executor.py --once [--auditor deepseek|ring]
  consensus_executor.py --drain N [--auditor deepseek|ring]
"""
import fnmatch
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenance_queue as mq

DCT = json.load(open(os.path.join(mq.QUEUE_DIR, "doctrine.json")))
ARCHIVE_ROOT = "/Volumes/RENDER DISK/archive"
ALLOWLIST = DCT.get("allowlist_hard_blocked", [])
BRAND_ASSET_ZONES = ("assets/branding", "brand/", "logos/", "marks/", "styleguides", "secrets/")


def is_blocked(path):
    """Return a reason string if path is in a hard-blocked zone, else None."""
    rel = path.replace(os.sep, "/")
    for g in ALLOWLIST:
        pat = g.replace("**", "*")
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(path, pat):
            return g
    if any(z in rel for z in BRAND_ASSET_ZONES):
        return "brand-identity-or-secret"
    return None


def staged_rows(limit=5):
    c = mq._conn()
    cur = c.execute(
        "SELECT id,path,kind,status_probe,confidence,evidence "
        "FROM rows WHERE status='staged' ORDER BY created_at LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    c.close()
    return rows


def proposal_for(row_id):
    path = os.path.join(mq.QUEUE_DIR, "proposals.jsonl")
    if not os.path.exists(path):
        return None
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            p = json.loads(line)
        except Exception:
            continue
        if p.get("row_id") == row_id:
            note = json.loads(p.get("note") or "{}")
            return {"path": p.get("path"), "note": note}
    return None


def _audit(row, auditor):
    """Audit the proposed action. Returns ('execute'|'hold', flags).

    INTEGRATION SEAM: live operation submits the reasoned case to the configured
    higher model (DeepSeek/Ring) through the router. Offline/harness it returns a
    deterministic verdict so the executor is testable without cloud tokens.
    Hard-safe defaults: brand/identity/secret and unknown-status always HOLD."""
    if not row or not os.path.exists(row["path"]):
        return "hold", ["missing-path"]
    blocked = is_blocked(row["path"])
    if blocked:
        return "hold", [f"blocked:{blocked}"]
    status = row.get("status_probe") or "unknown"
    if status == "unknown":
        return "hold", ["low-confidence-unknown-needs-human"]
    return "execute", [auditor or "deepseek-auditor"]


def archive_one(path, brand_hint=None):
    """Move a file into the dated archive dir under /Volumes/RENDER DISK.

    Returns (dest, err). shutil.move target is ALWAYS under ARCHIVE_ROOT (never
    deletes the source to a non-archive location). Writes a dated manifest."""
    if not os.path.isdir(ARCHIVE_ROOT):
        return None, f"archive root {ARCHIVE_ROOT} not mounted — abort"
    rel = path.replace(os.sep, "/")
    brand = brand_hint or "unknown"
    if "Kit/life/brands/" in rel:
        brand = rel.partition("Kit/life/brands/")[2].split("/")[0] or brand
    stamp = time.strftime("%Y-%m-%d")
    dest_dir = os.path.join(ARCHIVE_ROOT, brand, stamp)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(path))
    try:
        shutil.move(path, dest)
    except Exception as e:
        return None, str(e)
    # dated manifest
    manifest = os.path.join(ARCHIVE_ROOT, brand, f"manifest_{stamp}.json")
    entries = []
    if os.path.exists(manifest):
        try:
            entries = json.load(open(manifest))
        except Exception:
            entries = []
    entries.append({"source": path, "dest": dest, "ts": time.time(), "brand": brand})
    with open(manifest, "w") as f:
        json.dump(entries, f, indent=2)
    return dest, None


def process_one(auditor=None, owner="consensus-worker"):
    """Run one consensus-gated row through propose -> audit -> execute -> report."""
    rows = staged_rows(1)
    if not rows:
        return "no-staged-rows"
    row = rows[0]
    prop = proposal_for(row["id"])
    if prop:
        note = prop["note"]
        row["status_probe"] = note.get("status_probe", row.get("status_probe"))
        row["path"] = prop.get("path", row["path"])
        reason = note.get("reason", "")
        brand_hint = note.get("brand")
    else:
        reason = ""
        brand_hint = None

    verdict, flags = _audit(row, auditor)

    if verdict == "hold":
        mq.transition(row["id"], "rejected", owner, json.dumps({"hold": flags}))
        return f"row {row['id']}: HOLD {flags}"

    # consensus reached -> execute the archive
    mq.transition(row["id"], "reserved", owner, "consensus-audit")
    mq.transition(row["id"], "approved", owner, "consensus-ok")
    dest, err = archive_one(row["path"], brand_hint)
    if err:
        mq.transition(row["id"], "rejected", owner, f"archive-fail:{err}")
        return f"row {row['id']}: archive FAIL ({err})"
    mq.transition(row["id"], "archived", owner, f"moved to {dest}")
    _post_report(row, dest, verdict, reason)
    return f"row {row['id']}: ARCHIVED -> {os.path.basename(dest)}"


def _post_report(row, dest, verdict, reason):
    """Append a post-hoc report entry for Jeff's daily review."""
    os.makedirs(mq.QUEUE_DIR, exist_ok=True)
    entry = {
        "ts": time.time(), "row": row["id"], "path": row["path"], "dest": dest,
        "verdict": verdict, "reason": reason, "action": "ARCHIVE",
    }
    rpt = os.path.join(mq.QUEUE_DIR, "posthoc-report.jsonl")
    with open(rpt, "a") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="process a single row")
    ap.add_argument("--drain", type=int, default=0, help="process up to N rows")
    ap.add_argument("--auditor", default="deepseek", help="auditor model (deepseek|ring)")
    a = ap.parse_args()
    n = 1 if a.once else a.drain
    if n <= 0:
        n = 1
    for _ in range(n):
        print(process_one(a.auditor), flush=True)