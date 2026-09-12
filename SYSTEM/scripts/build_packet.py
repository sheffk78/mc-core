#!/usr/bin/env python3
"""Build the daily review packet from staged maintenance proposals.

Produces a ranked, human-skimable digest (the council's lane-3 requirement):
safety/high-concern first, then archive proposals, then flagged media, then
leave/unknown abstentions summary. Raw diff-level detail is drill-down only.

Usage: build_packet.py [--brand X] [--limit N]
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenance_queue as mq

PRIORITY = {"unknown": 0, "superseded": 1, "complete": 2, "paused": 3, "active": 4, "leave": 5}


def load_proposals():
    path = os.path.join(mq.QUEUE_DIR, "proposals.jsonl")
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            p = json.loads(line)
            p["note_obj"] = json.loads(p.get("note") or "{}")
            out.append(p)
        except Exception:
            continue
    return out


def band_key(n):
    """Batch proposals into review buckets for the packet."""
    a = n.get("note_obj", {}).get("action")
    return {"archive": "ARCHIVE", "flag": "FLAG (media)", "consolidate": "CONSOLIDATE",
            "leave": "ABSTAIN"}.get(a, "OTHER")


def build(brand=None, limit=60):
    proposals = load_proposals()
    if brand:
        proposals = [p for p in proposals if p.get("note_obj", {}).get("brand") == brand]
    # rank: safety/unknown first, then superseded, welfare, complete
    ranked = sorted(proposals, key=lambda p: PRIORITY.get(p.get("note_obj", {}).get("status_probe"), 9))
    bands = {}
    for p in ranked:
        bands.setdefault(band_key(p), []).append(p)

    meta = {
        "generated": time.time(),
        "brand": brand or "ALL",
        "total_proposals": len(proposals),
        "by_action": {k: len(v) for k, v in bands.items()},
        "safety_notes": [],
    }
    # Safety section: anything low-confidence OR conflicted evidence
    for p in ranked:
        n = p.get("note_obj", {})
        if n.get("status_probe") == "unknown" and n.get("action") == "archive":
            meta["safety_notes"].append({
                "row": p["row_id"], "path": p["path"],
                "why": "archive proposed on unknown status - low confidence, needs human check",
            })

    out = {"meta": meta, "review_bands": {}}
    for band, items in bands.items():
        out["review_bands"][band] = [{
            "row": p["row_id"],
            "path": p["path"],
            "status": p.get("note_obj", {}).get("status_probe"),
            "action": p.get("note_obj", {}).get("action"),
            "reason": p.get("note_obj", {}).get("reason"),
            "size": p.get("note_obj", {}).get("size"),
        } for p in items[:limit]]

    # idempotently write packet; keep most recent
    dest = os.path.join(mq.QUEUE_DIR, f"packet_{brand or 'all'}_{time.strftime('%Y%m%d')}.json")
    with open(dest, "w") as f:
        json.dump(out, f, indent=2)
    print("packet written:", dest)
    print("bands:", meta["by_action"])
    if meta["safety_notes"]:
        print("SAFETY NOTES (low-confidence archives):", len(meta["safety_notes"]))
        for s in meta["safety_notes"][:5]:
            print("  ", s["row"], os.path.basename(s["path"]), "-", s["reason"])
    return dest


if __name__ == "__main__":
    brand = None
    limit = 60
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--brand" and i+1 < len(args): brand = args[i+1]
        if a == "--limit" and i+1 < len(args): limit = int(args[i+1])
    build(brand=brand, limit=limit)