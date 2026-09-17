#!/usr/bin/env python3
"""
directory-preflight.py — executable gate for the TrustOffice trustee-directory pipeline.
Fail-closed: exit 0 only when every requested gate's checks pass. No exit 0 = no deploy.

Adapted from the TJB pipeline gate pattern (tjb-page-preflight / preflight-stage-gate.py)
and from the sandbox-verified logic harness (deleg_b05a02c9 task 2, score 100/100).

Usage:
  python3 directory-preflight.py G2.5 <dist_dir> <pages-manifest.json> <counts.json> [sitemap.xml]
  python3 directory-preflight.py G3    <dist_dir> <pages-manifest.json> <counts.json> [sitemap.xml]
  python3 directory-preflight.py G4    <dist_dir> <pages-manifest.json> <counts.json> <siteguru.json>

Exit codes (TJB convention): 0 pass | 1 fail | 2 config error | 3 partial (some pages failed)
Evidence: writes gate-result JSON next to the artifacts it checked.
"""

import json, os, re, sys, hashlib, datetime, urllib.parse

BANNED_WORDS = [
    "verified", "vetted", "top", "rated", "ranking", "endorsed", "approved",
    "recommended", "accredited", "premier", "leading", "trusted", "best",
]
# Legit contextual uses that are NOT endorsements (scanned as phrases, allowed):
ALLOWED_PHRASES = [
    "top of page", "top right", "top left", "on top", "best practices",
]
META_MIN, META_MAX = 140, 160
NAME_CAP = 200
SUBSTANCE_FLOOR = 3          # metro-unique facts required on hubs
SCORE_FLOOR = 85             # per-page SEO score floor (G2.5-seo)
NO_SCORE_FLOOR = 70          # below this = hard no-ship (per plan)
BASE_URL = "https://trustoffice.app"  # sitemap URL construction for manifest entries without explicit url

METRO_FACTS_KEYS = ["metro_unique_facts"]


def load_json(p):
    with open(p) as f:
        return json.load(f)


def strip_html(html):
    """Visible-text extraction for scans (crude but sufficient + deterministic)."""
    txt = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    txt = re.sub(r"<style[\s\S]*?</style>", " ", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt


def check_banned_language(html, visible):
    hits = []
    low = visible.lower()
    for w in BANNED_WORDS:
        for m in re.finditer(rf"\b{re.escape(w)}\b", low):
            ctx = visible[max(0, m.start() - 40): m.end() + 40]
            if any(p in ctx.lower() for p in ALLOWED_PHRASES):
                continue
            hits.append({"word": w, "context": ctx.strip()})
    # Banned words must not hide in JSON-LD either (schema strings count as page text)
    for m in re.finditer(r"<script type=\"application/ld\+json\">([\s\S]*?)</script>", html, re.I):
        blob = m.group(1).lower()
        for w in BANNED_WORDS:
            if re.search(rf"\b{re.escape(w)}\b", blob):
                hits.append({"word": w, "context": "JSON-LD blob"})
    # Meta attributes: title/description/OG are page text too (audit hole 2 — banned word
    # "trusted" inside meta description passed the visible-text scan).
    meta_text = " ".join(
        v for v in parse_metas(html).values() if isinstance(v, str)).lower()
    for w in BANNED_WORDS:
        if re.search(rf"\b{re.escape(w)}\b", meta_text):
            hits.append({"word": w, "context": f"meta attribute ({w})"})
    return hits


def parse_metas(html):
    d = {}
    for prop in ["description", "og:title", "og:url", "robots"]:
        m = re.search(rf"<meta[^>]+name=[\"']{prop}[\"'][^>]+content=[\"']([^\"']*)[\"']", html, re.I)
        if not m:
            m = re.search(rf"<meta[^>]+content=[\"']([^\"']*)[\"'][^>]+name=[\"']{prop}[\"']", html, re.I)
        if m:
            d[prop] = m.group(1)
    for prop in ["og:url", "og:title", "robots"]:
        m = re.search(rf"<meta[^>]+property=[\"']{prop}[\"'][^>]+content=[\"']([^\"']*)[\"']", html, re.I)
        if m:
            d[prop] = m.group(1)
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    d["title"] = title.group(1).strip() if title else None
    canon = re.search(r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']*)[\"']", html, re.I)
    if not canon:
        canon = re.search(r"<link[^>]+href=[\"']([^\"']*)[\"'][^>]+rel=[\"']canonical[\"']", html, re.I)
    d["canonical"] = canon.group(1) if canon else None
    return d


def extract_metas(html):
    return parse_metas(html)


def check_page_structure(html, metas):
    problems = []
    h1s = re.findall(r"<h1[\s>]", html, re.I)
    if len(h1s) != 1:
        problems.append(f"expected exactly 1 H1, found {len(h1s)}")
    # Heading hierarchy: no skipped levels (h2 before h3 etc.)
    levels = [int(x) for x in re.findall(r"<h([1-6])[\s>]", html, re.I)]
    prev = 0
    for lv in levels:
        if lv > prev + 1:
            problems.append(f"heading skip h{prev}->h{lv}")
        prev = lv
    # Meta description length
    md = metas.get("description")
    if not md:
        problems.append("meta description missing")
    elif not (META_MIN <= len(md) <= META_MAX):
        problems.append(f"meta description {len(md)} chars (need {META_MIN}-{META_MAX})")
    # Title present + length sanity
    t = metas.get("title")
    if not t:
        problems.append("title missing")
    elif len(t) > 65:
        problems.append(f"title {len(t)} chars (>65)")
    # Canonical absolute + trailing slash
    c = metas.get("canonical")
    if not c:
        problems.append("canonical missing")
    else:
        if not c.startswith("https://"):
            problems.append("canonical not absolute https")
        if not c.endswith("/"):
            problems.append("canonical missing trailing slash")
    # og:url must equal canonical
    og = metas.get("og:url")
    if og != c:
        problems.append(f"og:url ({og}) != canonical ({c})")
    # Internal links resolve to files in dist
    for m in re.finditer(r"href=[\"'](\/[^\"'#]*)[\"']", html):
        path = urllib.parse.urlparse(m.group(1)).path
        rel = path.lstrip("/")
        if rel == "":
            continue
        if not (os.path.exists(os.path.join(DIST_DIR, rel))
                or os.path.exists(os.path.join(DIST_DIR, rel, "index.html"))
                or os.path.exists(os.path.join(DIST_DIR, rel.rstrip("/") + ".html"))):
            problems.append(f"internal link target missing in dist: {path}")
    return problems


def extract_schema_errors(html):
    errs = []
    blobs = re.findall(r"<script type=\"application/ld\+json\">([\s\S]*?)</script>", html, re.I)
    if not blobs:
        return ["no JSON-LD schema found"]
    types = set()
    for b in blobs:
        try:
            data = json.loads(b)
        except json.JSONDecodeError as e:
            errs.append(f"JSON-LD parse error: {e}")
            continue
        nodes = data if isinstance(data, list) else data.get("@graph", [data])
        for n in nodes:
            t = n.get("@type", "")
            types.add(t if isinstance(t, str) else ",".join(t))
    required_any = {"Organization", "Person", "ProfessionalService", "LocalBusiness"}
    if not types & required_any:
        errs.append(f"no entity schema node (found: {sorted(types)})")
    if "BreadcrumbList" not in types:
        errs.append("BreadcrumbList missing")
    if "FAQPage" not in types:
        errs.append("FAQPage missing")
    return errs


def check_substance_floor(html, facts, metro_tokens):
    """>=3 metro-unique facts, each verified by >=1 distinct metro-gazetteer token
    (sandbox-proven method: token match over the facts corpus)."""
    if len(facts) < SUBSTANCE_FLOOR:
        return [f"substance floor: {len(facts)} facts < {SUBSTANCE_FLOOR}"]
    visible = strip_html(html).lower()
    problems = []
    verified = 0
    for fact in facts:
        fl = fact.lower()
        if any(tok.lower() in fl for tok in metro_tokens) and any(tok.lower() in visible for tok in metro_tokens):
            verified += 1
    if verified < SUBSTANCE_FLOOR:
        problems.append(f"substance floor: only {verified}/{len(facts)} facts metro-anchored")
    return problems


def compute_seo_score(html, metas, topic, visible, page=None):
    """12-item must-pass scorer (plan §3.4 + TJB local-SEO spec). Returns 0-100."""
    checks = []
    # topic keyword placement
    slug = urllib.parse.urlparse(metas.get("canonical") or "").path.strip("/").split("/")[-1]
    page = page or {}
    metro_tokens = page.get("metro_tokens") or []
    is_hub = page.get("page_type") == "metro-hub"
    checks.append(("topic in title", topic.lower() in (metas.get("title") or "").lower()))
    checks.append(("topic in meta", topic.lower() in (metas.get("description") or "").lower()))
    # Slug rule: listing pages carry the exact topic phrase; metro hubs carry the metro
    # token (§3.1 URL model vs §3.4 topic-in-slug tension — hub slugs are metro-based).
    # Slug tokens are hyphenated; normalize before matching.
    slug_norm = slug.lower().replace("-", " ").replace("_", " ")
    if is_hub and metro_tokens:
        checks.append(("topic in slug (hub: metro token)", any(tok.lower() in slug_norm for tok in metro_tokens)))
    else:
        checks.append(("topic in slug", topic.lower() in slug_norm))
    first10 = visible[: max(1, len(visible) // 10)].lower()
    checks.append(("topic in first 10%", topic.lower() in first10))
    # structure
    checks.append(("one H1", len(re.findall(r"<h1[\s>]", html, re.I)) == 1))
    checks.append(("schema present", bool(re.search(r"application/ld\+json", html, re.I))))
    checks.append(("alt text on images", all(
        re.search(r"alt=[\"'][^\"']+[\"']", tag, re.I)
        for tag in re.findall(r"<img[^>]*>", html, re.I)) or not re.findall(r"<img[^>]*>", html, re.I)))
    checks.append(("meta desc length ok", META_MIN <= len(metas.get("description") or "") <= META_MAX))
    checks.append(("canonical trailing slash", (metas.get("canonical") or "").endswith("/")))
    checks.append(("og:url == canonical", metas.get("og:url") == metas.get("canonical")))
    checks.append(("title <=65", len(metas.get("title") or "") <= 65))
    checks.append(("no banned words", not check_banned_language(html, visible)))
    return round(100.0 * sum(1 for _, ok in checks if ok) / len(checks), 1), [n for n, ok in checks if not ok]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_evidence(gate, result, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    result["timestamp"] = datetime.datetime.now().isoformat()
    result["gate"] = gate
    out = os.path.join(out_dir, f"preflight-{gate.replace('.', '-')}.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    return out


# ---------------------------------------------------------------- gates

def run_gate(gate, dist, manifest_path, counts_path, extra):
    global DIST_DIR
    DIST_DIR = dist
    result = {"pass": False, "pages_checked": 0, "problems": [], "failed_pages": {}}

    if not os.path.isdir(dist):
        result["problems"].append(f"dist dir missing: {dist}")
        return result, 2

    manifest = load_json(manifest_path)
    pages = manifest["pages"] if isinstance(manifest, dict) else manifest
    result["pages_checked"] = len(pages)
    per_page = {}
    all_ok = True

    # G3 adds the sitemap positive-membership check: every manifest URL must appear
    # in sitemap.xml (audit hole 1 — G3 ignored the sitemap arg entirely).
    sm_problems = []
    if gate == "G3":
        if not extra or not os.path.exists(extra):
            sm_problems.append("G3 requires sitemap.xml path")
        else:
            sm_raw = open(extra, encoding="utf-8", errors="replace").read()
            sm_locs = [u.strip().rstrip("/") for u in re.findall(r"<loc>([^<]+)</loc>", sm_raw)]
            for page in pages:
                page_url = page.get("url")
                if not page_url:
                    sm_problems.append(f"manifest entry missing required 'url' field: {page.get('path') or page.get('slug')}")
                    continue
                if page_url.strip().rstrip("/") not in sm_locs:
                    sm_problems.append(f"sitemap missing manifest URL: {page_url}")
    result["problems"] += sm_problems
    if sm_problems:
        all_ok = False

    for page in pages:
        rel = page.get("path") or page.get("slug", "")
        hp = os.path.join(dist, rel.lstrip("/"))
        if not os.path.exists(hp):
            per_page[rel] = ["PAGE FILE MISSING IN DIST"]
            all_ok = False
            continue
        html = open(hp, encoding="utf-8", errors="replace").read()
        visible = strip_html(html)
        metas = extract_metas(html)
        probs = check_page_structure(html, metas) + extract_schema_errors(html)
        banned = check_banned_language(html, visible)
        if banned:
            probs.append(f"banned language: {banned}")
        score, failed_items = compute_seo_score(
            html, metas, page.get("topic") or page.get("name", ""), visible, page=page)
        result.setdefault("scores", {})[rel] = score
        if score < NO_SCORE_FLOOR:
            probs.append(f"SEO score {score} < {NO_SCORE_FLOOR} hard floor — no-ship")
        elif score < SCORE_FLOOR:
            probs.append(f"SEO score {score} < {SCORE_FLOOR} ship floor")
        # substance floor (hubs only)
        if page.get("kind") == "hub" or page.get("page_type") == "hub":
            facts = page.get(METRO_FACTS_KEYS[0]) or counts_path_facts(counts_path)
            metro_tokens = page.get("metro_tokens") or metro_tokens_from_counts(counts_path)
            probs += check_substance_floor(html, facts or [], metro_tokens or [])
        if probs:
            per_page[rel] = probs
            all_ok = False

    result["failed_pages"] = per_page
    result["pass"] = all_ok
    ev = write_evidence(gate, result, os.path.join(os.path.dirname(manifest_path), "verify"))
    print(f"[{gate}] {'PASS' if all_ok else 'FAIL'} — {len(pages)} pages, evidence: {ev}")
    if not all_ok:
        for rel, probs in per_page.items():
            for p in probs:
                print(f"  FAIL {rel}: {p}")
    return result, (0 if all_ok else (3 if result["scores"] else 1))


def counts_path_facts(counts_path):
    try:
        c = load_json(counts_path)
        return c.get("metro_unique_facts")
    except Exception:
        return None


def metro_tokens_from_counts(counts_path):
    try:
        c = load_json(counts_path)
        cities = c.get("ut_by_city") or c.get("cities") or {}
        return list(cities.keys()) + [c.get("metro_name", "")]
    except Exception:
        return []


def run_gate_g4(gate, dist, manifest_path, counts_path, siteguru_path):
    """G4: SiteGuru page reports show zero new errors vs persisted baseline."""
    result = {"pass": False, "problems": []}
    sg = load_json(siteguru_path)
    baseline = sg.get("baseline", {})
    current = sg.get("current", {})
    expected_noindex = sg.get("staging_noindex_expected", False)
    for url, base_issues in baseline.items():
        cur_issues = current.get(url, [])
        new = [i for i in cur_issues if i not in base_issues]
        if expected_noindex:
            new = [i for i in new if "noindex" not in json.dumps(i).lower()]
        if new:
            result["problems"].append(f"{url}: new issues {new}")
    result["pass"] = not result["problems"]
    ev = write_evidence("G4", result, os.path.join(os.path.dirname(manifest_path), "verify"))
    print(f"[G4] {'PASS' if result['pass'] else 'FAIL'} — evidence: {ev}")
    return result, (0 if result["pass"] else 1)


def run_gate_g05(research_dir, counts_path, unit_slug):
    """G0.5-research gate: fail-closed artifact + counts check for a unit's RESEARCH stage.
    Checks (per plan §4.2): every declared RESEARCH artifact exists by exact path and is
    non-empty; per-type counts present in counts.json; source files dated <=35 days."""
    import time
    result = {"gate": "G0.5", "unit": unit_slug, "pass": False, "problems": []}
    checks = []

    declared = [
        f"{research_dir}/raw.csv",
        f"{research_dir}/registry-raw.csv",
    ]
    for path in declared:
        if not os.path.exists(path) or os.path.getsize(path) < 32:
            result["problems"].append(f"declared RESEARCH artifact missing/empty: {path}")
        else:
            checks.append({"path": path, "exists": True, "bytes": os.path.getsize(path)})

    counts = load_json(counts_path) if os.path.exists(counts_path) else {}
    by_type = counts.get("by_type")
    if not isinstance(by_type, dict) or not by_type:
        result["problems"].append("counts.json missing per-type counts ('by_type' dict)")
    else:
        checks.append({"by_type": by_type})
    # Source freshness: any source-file mtime >35 days old is stale
    now = time.time()
    if os.path.isdir(research_dir):
        for f in os.listdir(research_dir):
            p = os.path.join(research_dir, f)
            if os.path.isfile(p) and f.startswith("source-"):
                age_days = (now - os.path.getmtime(p)) / 86400
                if age_days > 35:
                    result["problems"].append(f"source file stale ({age_days:.0f}d): {f}")
    result["checks"] = checks
    result["pass"] = not result["problems"]

    os.makedirs(f"{research_dir}/../verify", exist_ok=True)
    with open(f"{research_dir}/../verify/preflight-G0.5.json", "w") as fh:
        json.dump(result, fh, indent=2)
    return result, (0 if result["pass"] else 1)


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    gate = sys.argv[1].upper()
    dist, manifest, counts = sys.argv[2], sys.argv[3], sys.argv[4]
    extra = sys.argv[5] if len(sys.argv) > 5 else None
    if gate in ("G2.5", "G3"):
        res, rc = run_gate(gate, dist, manifest, counts, extra)
    elif gate == "G4":
        if not extra:
            print("G4 requires siteguru.json path")
            return 2
        res, rc = run_gate_g4(gate, dist, manifest, counts, extra)
    elif gate == "G0.5":
        # G0.5 arg mapping: dist=research_dir, manifest=counts.json, counts=unit_slug
        res, rc = run_gate_g05(dist, manifest, counts)
    else:
        print(f"unknown gate: {gate} (supported: G0.5, G2.5, G3, G4)")
        return 2
    label = {"G0.5": "G0.5", "G2.5": "G2.5", "G3": "G3", "G4": "G4"}.get(gate, gate)
    status = "PASS" if (res.get("pass") if isinstance(res, dict) else rc == 0) else "FAIL"
    print(f"[{label}] {status} — evidence: {json.dumps(res)[:600] if isinstance(res, dict) else res}")
    return rc


if __name__ == "__main__":
    sys.exit(main())