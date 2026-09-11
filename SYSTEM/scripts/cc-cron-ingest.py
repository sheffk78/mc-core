#!/usr/bin/env python3
"""
cc-cron-ingest.py — Command Center cron-feed ingest (script-only, no LLM)

Scans Hermes cron output files (~/.hermes/cron/output/<job_id>/*.md), extracts
each job's latest response from the last 24h, classifies it as:
  - 'silent'      → not recorded
  - 'fyi'         → notification item in the CC Cron Feed (dismissible)
  - 'needs_action'→ notification item + a task in the CC "Needs your attention" list

State: ~/.hermes/cc-feed/state.json   (persisted seen-map, one-shot flags)
Output: JSON written to stdout (the CC backend reads it directly when possible;
        this file is also the cron job's delivery payload for auditability).

Design constraints (per SYSTEM/CRON-ALTERNATIVE-FRAMEWORK.md):
  - Script-only (no_agent=True) — zero LLM cost
  - Silent on no change (empty stdout → no delivery)
"""

import glob
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
BASE = HOME / ".hermes" / "cron" / "output"
JOBS_JSON = HOME / ".hermes" / "cron" / "jobs.json"
STATE_DIR = HOME / ".hermes" / "cc-feed"
STATE_FILE = STATE_DIR / "state.json"
MAX_AGE_H = 24  # only ingest runs from the last 24h; older history is dead


def _to_ts(at) -> float:
    """Parse a seen-map timestamp ('at') to epoch seconds; 0 on any failure."""
    if isinstance(at, (int, float)):
        return float(at)
    try:
        return datetime.fromisoformat((at or "").replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0

# ── Classification ─────────────────────────────────────────────────────────
# A run "needs action" when its own report says it needs a human decision,
# is blocked, or flags a hard failure. Two independent signals required for
# keyword hits (reduces false positives from narrative text); 🔴 alone is a
# strong single signal. Failure status always needs action.
ASK_PATTERNS = [
    r"needs? kenneth", r"needs? jeff", r"needs? your (approval|decision|greenlight|review|sign)",
    r"awaiting (kenneth|jeff|approval|your)", r"waiting on (kenneth|jeff|your approval)",
    r"kenneth('s)? (review|decision|approval|greenlight)", r"please (approve|review|confirm|decide|greenlight)",
    r"needs? human", r"cannot auto[- ]resolve", r"human judgment required",
    r"needs? manual (review|approval)", r"needs? (jeff|kenneth) review",
    r"before sending", r"awaiting (his|her) (review|decision)",
]
# Completed-work narration that mentions review/decision in past/packaged form —
# "drafts ready for Jeff review" is a delivery notice, not an ask. Strip it before
# classification so it can't trip the ask patterns.
READY_FOR_REVIEW = r"\b(drafts?|copy|report|summary|files?|list)\s+(are|is)?\s*ready\s+for\b"
BLOCK_PATTERNS = [
    r"\bblocker\b", r"\bblocked (by|on|until)\b", r"🚫", r"dead_letter",
]
STRONG_SINGLE = ["🔴"]  # a red flag alone is enough
# Narrative noise that looks like an ask but is a summary of completed work
NEGATIVE_PATTERNS = [
    r"nothing needs (kenneth|jeff)", r"no (action|items) (needed|requiring)", r"no escalations? (needed|required)",
    r"all (handled|clear|resolved)", r"nothing to (action|report)", r"\[all handled\]", r"no outstanding",
]

# Job names whose reports are inherently FYI unless explicitly flagged — these
# are health/monitor jobs that always end with an all-clear narrative.
MONITOR_JOB_HINTS = ["health", "monitor", "watchdog", "sentinel", "canary", "scorecard", "backup", "token refresh"]

# ── Brand derivation ────────────────────────────────────────────────────────
# Feed cards get filterable brands. Match on job-name prefixes (same vocabulary
# as the workspace brand-prefix convention).
BRAND_PREFIXES = [
    ("tjb", "true-joy-birthing"), ("truejoy", "true-joy-birthing"), ("true joy", "true-joy-birthing"),
    ("trustparatodos", "agentic-trust"), ("trustminutes", "trustminutes"), ("trustoffice", "trustoffice"),
    ("aeriusview", "aeriusview"), ("aav", "aeriusview"), ("wingpoint", "wingpoint"),
    ("socialize", "socialize-video"), ("stenodesk", "stenodesk"), ("mlm", "agentic-trust"),
    ("mll", "agentic-trust"), ("montana light", "agentic-trust"),
]


def _brand_from_name(name: str) -> str | None:
    low = (name or "").lower()
    for prefix, brand in BRAND_PREFIXES:
        if low.startswith(prefix) or f" {prefix}" in low:
            return brand
    return None


MAX_BODY = 4000  # cap per-item body stored in feed


def _clean_report_text(text: str) -> str:
    """Strip cron-report scaffolding (headers, [SILENT], code fences, blank
    gaps) so the full-text view reads as a clean, scannable digest."""
    out = []
    in_fence = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue  # drop fenced code blocks — not readable in a feed card
        if re.match(r"^#{1,6} ", line.strip()):
            line = line.strip().lstrip("#").strip()
        elif line.strip() == "[SILENT]":
            continue
        if not line.strip() and (not out or not out[-1].strip()):
            continue  # collapse blank runs
        out.append(line)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out).strip()


def extract_full_text(path: Path) -> str:
    """Full cleaned report body for the CC detail view (not just first 280 chars)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    if "## Response" in text:
        text = text.split("## Response", 1)[1]
    # Cron-scaffold lines (run metadata the card already shows) are dropped
    # wherever they appear — files with and without a '---' separator.
    header_like = re.compile(
        r"^#?\s*(Cron Job:|\*\*Job ID:\*\*|\*\*Run Time:\*\*|\*\*Mode:\*\*|\*\*Status:\*\*)"
    )
    text = "\n".join(
        ln for ln in text.splitlines() if not header_like.match(ln.strip())
    )
    # else: whole file is the payload (script-mode fallback)
    return _clean_report_text(text)[:MAX_BODY]


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"seen": {}, "notified": {}, "tasked": {}}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1))
    os.replace(tmp, STATE_FILE)


def extract_response(path: Path):
    """Return (response_text|None, mode) from a cron output file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None, "unreadable"
    if "## Response" in text:
        return text.split("## Response", 1)[1].strip(), "agent"
    if "silent (empty output)" in text:
        return None, "script-silent"
    if "\n---\n" in text:
        return text.split("\n---\n", 1)[1].strip() or None, "script"
    return None, "unknown"


def classify(resp: str, job_name: str, last_status: str):
    """Return category: silent | fyi | needs_action"""
    # hard failure state FIRST — a failed job must surface even if its
    # response is empty/silent (e.g. script crashed with no output).
    if last_status in ("error", "failed"):
        return "needs_action"
    if not resp or not resp.strip():
        return "silent"
    if re.search(r"^\s*\[SILENT\]\s*$", resp, re.I):
        return "silent"
    low = re.sub(READY_FOR_REVIEW, "", resp.lower())  # packaged-work narration ≠ ask
    for p in NEGATIVE_PATTERNS:
        if re.search(p, low):
            # all-clear narratives override weak keyword hits
            if not any(s in resp for s in STRONG_SINGLE):
                return "fyi"
    asks = sum(1 for p in ASK_PATTERNS if re.search(p, low))
    blocks = sum(1 for p in BLOCK_PATTERNS if re.search(p, low))
    strong = any(s in resp for s in STRONG_SINGLE)
    # one explicit ask or block is enough — packaged-work narration ("drafts
    # ready for review") is stripped above, so the FP class that motivated the
    # old two-signal rule is handled at the source.
    if strong or asks >= 1 or blocks >= 1:
        return "needs_action"
    return "fyi"


def summarise(resp: str, limit: int = 280) -> str:
    """First meaningful paragraph(s), cleaned for a feed card."""
    lines = []
    for raw in resp.splitlines():
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        if re.match(r"^#{1,3} ", line):  # markdown headers → keep text
            line = line.lstrip("# ").strip()
        lines.append(line)
    text = " · ".join(lines) if lines else resp.strip()
    text = re.sub(r"\s+", " ", text)
    return text[:limit].rstrip() + ("…" if len(text) > limit else "")


def main() -> int:
    state = load_state()
    seen = state.setdefault("seen", {})
    tasked = state.setdefault("tasked", {})
    now = time.time()
    try:
        _mutes = json.loads((STATE_DIR / "mutes.json").read_text()) or {}
    except Exception:
        _mutes = {}
    try:
        jobs = json.loads(JOBS_JSON.read_text()).get("jobs", [])
    except Exception:
        jobs = []
    job_by_id = {j["id"]: j for j in jobs}

    items = []
    for jid, job in job_by_id.items():
        if not job.get("enabled"):
            continue
        files = sorted(glob.glob(str(BASE / jid / "*.md")))
        if not files:
            continue
        latest = files[-1]
        age_h = (now - os.path.getmtime(latest)) / 3600.0
        if age_h > MAX_AGE_H:
            continue
        run_ts = os.path.basename(latest)[:16].replace("_", " ")  # "2026-09-11 07-46"
        key = f"{jid}:{os.path.basename(latest)}"
        if seen.get(key):
            continue  # already ingested
        resp, mode = extract_response(Path(latest))
        cat = classify(resp or "", job.get("name", ""), job.get("last_status") or "")
        # Ack-as-mute: if Kenneth acknowledged this job's condition and the summary is
        # materially unchanged, downgrade repeat flags to fyi (visible, not attention).
        if cat == "needs_action" and job.get("last_status") not in ("error", "failed"):
            # mute applies to narrative asks only — hard failures always surface
            mute = _mutes.get(jid)
            if mute and (mute.get("until") or "") > datetime.now(timezone.utc).isoformat():
                item_summary = summarise(resp or "")
                sig = hashlib.sha1(item_summary[:200].encode()).hexdigest() if item_summary else ""
                if sig and sig == mute.get("sig"):
                    cat = "fyi"
        if cat == "silent":
            seen[key] = {"cat": "silent", "at": now}
            continue
        item = {
            "id": key,
            "job_id": jid,
            "job_name": job.get("name", jid),
            "brand": _brand_from_name(job.get("name", "")),
            "run_at": datetime.fromtimestamp(os.path.getmtime(latest), tz=timezone.utc).isoformat(),
            "mode": mode,
            "category": cat,
            "deliver": job.get("deliver") or "local",
            "schedule": (job.get("schedule") or {}).get("display") if isinstance(job.get("schedule"), dict) else str(job.get("schedule") or ""),
            "summary": summarise(resp or ""),
            "full_text": extract_full_text(Path(latest)),
            "output_path": str(latest),
            "output_dir": str(BASE / jid),
            "last_status": job.get("last_status"),
        }
        items.append(item)
        seen[key] = {"cat": cat, "at": datetime.now(timezone.utc).isoformat()}

    # prune seen-map: drop silent entries older than 7 days (they carry no value),
    # keep fyi/needs_action entries (the cap below bounds total size)
    state["seen"] = {k: v for k, v in seen.items()
                     if v.get("cat") != "silent" or (now - _to_ts(v.get("at"))) < 7 * 86400}
    # hard cap
    if len(state["seen"]) > 5000:
        keep = sorted(state["seen"].items(), key=lambda kv: kv[1].get("at") or "", reverse=True)[:3000]
        state["seen"] = dict(keep)

    save_state(state)

    # Maintain the rolling feed store the CC backend reads (last 24h of items).
    FEED_STORE = STATE_DIR / "feed.json"
    try:
        prev = json.loads(FEED_STORE.read_text())
        prev_items = prev.get("items", [])
    except Exception:
        prev_items = []
    by_id = {i["id"]: i for i in prev_items}
    for it in items:
        by_id[it["id"]] = it
    # Backfill full_text for items ingested before the field existed: any stored
    # item that still has its source file can get the full-text view for free.
    for it in by_id.values():
        if not it.get("full_text") and it.get("output_path"):
            it["full_text"] = extract_full_text(Path(it["output_path"]))
    cutoff = datetime.fromtimestamp(now - MAX_AGE_H * 3600, tz=timezone.utc).isoformat()
    kept = [i for i in by_id.values() if (i.get("run_at") or "") >= cutoff]
    kept.sort(key=lambda i: i.get("run_at") or "", reverse=True)
    out = {"generated_at": datetime.now(timezone.utc).isoformat(), "items": kept}
    tmp = FEED_STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=1))
    os.replace(tmp, FEED_STORE)

    # Silent on no change: nothing new since last tick → empty stdout
    if not items:
        return 0
    sys.stdout.write(json.dumps({"generated_at": out["generated_at"], "items": items}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())