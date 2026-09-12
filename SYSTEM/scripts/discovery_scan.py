#!/usr/bin/env python3
"""Discovery scanner for the Atlas brand-hygiene lane.

READ-ONLY. Walks a brand tree, classifies each candidate file, checks the
never-touch allowlist and dependency/load-bearing veto, and writes PROPOSALS into
the maintenance queue as staged rows. Does NOT modify, move, or delete anything.

Usage: discovery_scan.py <brand-root>
"""
import json, os, re, sys, time, fnmatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenance_queue as mq

DOCTRINE = json.load(open(os.path.join(mq.QUEUE_DIR, "doctrine.json")))
FG = DOCTRINE["freshness_gate"]
ALLOWLIST = DOCTRINE["allowlist_hard_blocked"]

DOC_EXTS = {".md", ".markdown", ".txt", ".rst", ".org"}
CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", ".yaml",
             ".yml", ".toml", ".sh", ".java", ".go", ".rb", ".php"}
MEDIA_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".png", ".jpg", ".jpeg", ".gif", ".webp",
              ".svg", ".pdf", ".zip", ".mp3", ".wav", ".cr2", ".raw", ".psd", ".ai",
              ".dng", ".tif", ".heic"}

SUPERSEDED_WORDS = {"superseded", "superseded by", "obsolete", "deprecated",
                    "replaced", "no longer used", "outdated", "previous version",
                    "old version", "retired", "deprecated"}
COMPLETE_WORDS = {"complete", "completed", "done", "finished", "shipped", "released",
                  "stable", "changelog", "retired", "archived"}
PAUSED_WORDS = {"paused", "on hold", "deprioritized", "shelved", "parked", "waiting"}
ACTIVE_WORDS = {"in progress", "active", "todo", "planned", "wip", "ongoing",
                "next step", "under way", "current"}


def blocked(rel_path):
    """Return matching allowlist glob or None. rel_path uses forward slashes."""
    for g in ALLOWLIST:
        pat = g.replace("**", "*")
        if fnmatch.fnmatch(rel_path, pat):
            return g
    return None


def classify(path, ext):
    """Content-aware status probe for docs; kind from extension. Returns
    (status_probe, kind, confidence, evidence)."""
    kind = ("doc" if ext in DOC_EXTS else
            "code" if ext in CODE_EXTS else
            "media" if ext in MEDIA_EXTS else "other")
    if ext not in DOC_EXTS:
        return "unknown", kind, 0.2, {}

    try:
        head = open(path, "r", errors="ignore").read(8000).lower()
    except Exception:
        return "unknown", kind, 0.2, {}

    has_super = any(w in head for w in SUPERSEDED_WORDS)
    has_comp = any(w in head for w in COMPLETE_WORDS)
    has_pause = any(w in head for w in PAUSED_WORDS)
    has_act = any(w in head for w in ACTIVE_WORDS)

    if has_super:
        status, conf = "superseded", 0.9
    elif has_comp:
        status, conf = "complete", 0.85
    elif has_pause:
        status, conf = "paused", 0.75
    elif has_act:
        status, conf = "active", 0.8
    else:
        status, conf = "unknown", 0.2

    kw = [w for w in (SUPERSEDED_WORDS | COMPLETE_WORDS | PAUSED_WORDS | ACTIVE_WORDS) if w in head][:6]
    return status, kind, conf, {"keywords": kw}


def dependency_veto(path, kind, brand_root):
    """Return a veto reason string if the file is load-bearing (referenced by an
    INDEX/README/manifest/sibling or build config), else None."""
    base = os.path.basename(path)
    parent = os.path.dirname(path)

    # 1. INDEX/README/MANIFEST in same dir
    for idx in ("INDEX.md", "README.md", "MANIFEST.md"):
        p = os.path.join(parent, idx)
        if os.path.exists(p):
            try:
                if base in open(p).read():
                    return f"linked from {idx}"
            except Exception:
                pass

    # 2. sibling project/docs referencing base
    try:
        for fn in os.listdir(parent):
            if fn == os.path.basename(path):
                continue
            # include html/css so web image assets aren't falsedly flagged
            if fn.lower().endswith((".md", ".json", ".yaml", ".yml", ".toml", ".py", ".js",
                                    ".html", ".htm", ".css", ".jsx", ".tsx")):
                p = os.path.join(parent, fn)
                if os.path.isfile(p):
                    try:
                        if base in open(p, errors="ignore").read(200_000):
                            return f"referenced by sibling {fn}"
                    except Exception:
                        pass
    except Exception:
        pass

    return None


def _detect_redundancy(path, dirpath, filenames):
    """Tier-0: detect near-identical sibling text files (redundancy). Returns a
    dict {twin, similarity} or None. Uses a simple content-similarity heuristic:
    normalized token overlap between sibling docs."""
    if not os.path.isfile(path):
        return None
    ext = os.path.splitext(path)[1].lower()
    if ext not in DOC_EXTS:
        return None  # only docs consolidate
    try:
        with open(path, errors="ignore") as _f:
            mine = _f.read().lower()
    except Exception:
        return None
    if not mine.strip():
        return None
    my_tokens = set(mine.split())
    if len(my_tokens) < 10:
        return None
    best, best_sim = None, 0.0
    for fn in filenames:
        if fn == os.path.basename(path):
            continue
        sibling = os.path.join(dirpath, fn)
        if not os.path.isfile(sibling):
            continue
        if os.path.splitext(fn)[1].lower() not in DOC_EXTS:
            continue
        try:
            with open(sibling, errors="ignore") as _f:
                sib = _f.read()
        except Exception:
            continue
        sib_tokens = set(sib.lower().split())
        if not sib_tokens:
            continue
        # jaccard overlap
        inter = len(my_tokens & sib_tokens)
        union = len(my_tokens | sib_tokens)
        if union == 0:
            continue
        sim = inter / union
        if sim > 0.6 and sim > best_sim:
            best_sim = sim
            best = fn
    if best:
        return {"twin": best, "similarity": round(best_sim * 100)}
    return None


def scan(root):
    mq.init_db()
    brand = os.path.basename(root.rstrip("/"))
    seen = 0
    proposed = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # prune blocked directories before descending
        kept = []
        for d in dirnames:
            rel = os.path.join(dirpath, d).replace(os.sep, "/")
            if not blocked(rel + "/"):
                kept.append(d)
        dirnames[:] = kept

        for fn in filenames:
            p = os.path.join(dirpath, fn)
            rel = p.replace(os.sep, "/")
            if blocked(rel):
                continue
            try:
                st = os.stat(p)
            except Exception:
                continue
            if not os.path.isfile(p):
                continue
            ext = os.path.splitext(fn)[1].lower()
            seen += 1

            status, kind, conf, ev = classify(p, ext)
            age_days = (time.time() - st.st_mtime) / 86400.0
            veto = dependency_veto(p, kind, root)

            # freshness trigger (mtime REVIEWS, never decides)
            thresh = FG["paused_doc_review_days"] if status == "paused" else FG["active_working_doc_review_days"]
            stale = age_days > thresh

            # DECISION (propose-only):
            # - hard veto (load-bearing / referenced) -> leave
            # - superseded/complete doc, stale, no veto -> archive proposal
            # - stale media -> flag for human review (never auto-archive)
            # - REDUNDANCY (Tier-0): near-identical sibling files -> consolidate proposal
            # - everything else -> leave
            redundancy = _detect_redundancy(p, dirpath, filenames)
            if veto:
                action = "leave"
                reason = f"load-bearing ({veto})"
            elif redundancy:
                action = "consolidate"
                reason = f"redundant with {redundancy['twin']} ({redundancy['similarity']}%)"
                ev["redundant_with"] = redundancy["twin"]
            elif stale and not veto and status in ("superseded", "complete", "paused"):
                action = "archive"
                reason = f"{status}, idle {round(age_days)}d"
            elif stale and kind == "media":
                action = "flag"
                reason = f"orphan media, idle {round(age_days)}d"
            else:
                action = "leave"
                reason = "not a stale/archive candidate"

            if action != "leave":
                row_id = mq.add_row("maintenance", p)
                if row_id:
                    mq.transition(row_id, "staged", "scanner")
                    # attach the evidence/action payload
                    note = json.dumps({
                        "action": action, "status_probe": status, "kind": kind,
                        "confidence": ev.get("keywords"), "age_days": round(age_days, 1),
                        "size": st.st_size, "reason": reason, "brand": brand,
                    })
                    proposal = {"row_id": row_id, "path": p, "note": note}
                    _append_proposal(proposal)
                    proposed += 1

    # write a review packet
    _write_review_packet(brand, proposed)
    return seen, proposed


def _append_proposal(p):
    os.makedirs(mq.QUEUE_DIR, exist_ok=True)
    with open(os.path.join(mq.QUEUE_DIR, "proposals.jsonl"), "a") as f:
        f.write(json.dumps(p) + "\n")


def _write_review_packet(brand, n_proposed):
    """Emit a minimal daily packet reference. Full prose digest is produced by the
    worker/review step. This records the scan happened and how many were proposed."""
    data = {"brand": brand, "proposals": n_proposed, "generated": time.time()}
    with open(os.path.join(mq.QUEUE_DIR, f"packet_{brand}_{time.strftime('%Y%m%d')}.json"), "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else None
    if not root or not os.path.isdir(root):
        sys.exit("usage: discovery_scan.py <brand-root>")
    t0 = time.time()
    seen, proposed = scan(root)
    print(f"scanned {seen} files, {proposed} proposals in {round(time.time()-t0,1)}s", flush=True)