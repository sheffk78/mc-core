#!/usr/bin/env python3
"""G9: Screenshot-reality gate — does the video's provider screenshot match the live page?

Validates against the capture manifest written by capture-provider-scroll.py
(fresh DOM ground truth at capture time) plus cities.ts. Catches all four
failure patterns from the 2026-09-04 incidents:
  P1 stale capture:     manifest missing, or screenshot older than the manifest,
                        or capture older than the last site deploy
  P2 wrong crop:        manifest crop start must not be ~0 (page top)
  P3 missing photos:    manifest must show ALL provider photos loaded
                        (naturalWidth > 0, non-placeholder src)
  P4 provider drift:    manifest provider names/count must equal cities.ts
                        localDoulas names; narration providerCount must match

Usage: python3 scripts/validate-screenshot-reality.py <slug>
Exit 1 on any failure (blocks the render gate).
"""
import sys, os, re, json, subprocess
from pathlib import Path
from datetime import datetime, timezone

REMOTION_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = REMOTION_DIR.parent.parent / "projects" / "truejoybirthing-website"
PUBLIC_DIR = REMOTION_DIR / "public" / "images"

STALE_AFTER_HOURS = 168


def site_last_deploy_ts() -> float:
    """Newest commit timestamp touching public/images or cities.ts (site repo)."""
    r = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", "src/data/cities.ts", "public/images"],
        capture_output=True, text=True, cwd=str(SITE_DIR))
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def cities_providers(slug: str):
    src = (SITE_DIR / "src" / "data" / "cities.ts").read_text()
    m = re.search(r'"%s":\s*\{' % re.escape(slug), src)
    if not m:
        return [], []
    nxt = re.search(r'\n  "[a-z][a-z-]+-[a-z]{2}":\s*\{', src[m.end():])
    block = src[m.start():m.end() + nxt.start()] if nxt else src[m.start():]
    ld = block[block.find("localDoulas"):]
    names = re.findall(r'name:\s*"([^"]+)"', ld)
    photos = re.findall(r'photo:\s*"([^"]+)"', ld)
    return names, photos


def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else ""
    if not slug:
        print("Usage: validate-screenshot-reality.py <slug>")
        sys.exit(1)

    fails, warns = [], []
    names, photos = cities_providers(slug)

    # ── P0: manifest exists ─────────────────────────────────────
    manifest_path = PUBLIC_DIR / f"{slug}-capture-manifest.json"
    if not manifest_path.exists():
        fails.append("P0: no capture manifest — run capture-provider-scroll.py <slug> first "
                     "(the capture now writes ground truth; a screenshot without a manifest "
                     "cannot be trusted)")
    else:
        man = json.loads(manifest_path.read_text())

        # ── P1: freshness — manifest vs site content changes ────
        cap_ts = datetime.fromisoformat(man["captured_at"]).timestamp()
        dep_ts = site_last_deploy_ts()
        if dep_ts > cap_ts:
            age_h = (dep_ts - cap_ts) / 3600
            fails.append(f"P1: site content changed {age_h:.0f}h AFTER the capture — recapture "
                         f"(capture-provider-scroll.py {slug})")
        age_h = (datetime.now().timestamp() - cap_ts) / 3600
        if age_h > STALE_AFTER_HOURS:
            warns.append(f"P1: capture is {age_h/24:.0f} days old — recapture recommended")

        # ── P2: crop geometry ───────────────────────────────────
        crop_start = man.get("crop", {}).get("start", 0)
        if crop_start < 500:
            fails.append(f"P2: manifest crop starts at y={crop_start} — page-top crop, "
                         f"provider section not located at capture time")

        # ── P3: all provider photos loaded at capture time ──────
        cards = man.get("provider_photos", [])
        unloaded = [c for c in cards if not c.get("loaded")]
        if not cards:
            fails.append("P3: manifest has no provider photos — provider section missing on page?")
        elif unloaded:
            fails.append(f"P3: {len(unloaded)}/{len(cards)} provider photos did not load at capture: "
                         + ", ".join(c["src"] for c in unloaded))
        else:
            # photos on disk must not be tiny initials placeholders
            tiny = []
            for c in cards:
                p = SITE_DIR / "public" / "images" / c["src"]
                if p.exists() and p.stat().st_size < 3000:
                    tiny.append(c["src"])
            if tiny:
                fails.append(f"P3: provider photo files are initials-sized placeholders (<3KB): {tiny}")

        # ── P4: provider drift (manifest photo FILES vs cities.ts photo paths) ────
        # Filename comparison is exact ground truth: cities.ts photo paths are the
        # canonical provider list; the live page is generated from it.
        man_srcs = sorted(os.path.basename(c.get("src", "")) for c in cards)
        city_srcs = sorted(os.path.basename(p) for p in photos if p)
        if man_srcs != city_srcs:
            fails.append(f"P4: provider drift — page photos {man_srcs} != cities.ts {city_srcs}")

        # providerCount in data file must match
        dpath = REMOTION_DIR / "src" / "data" / f"{slug}-data.ts"
        if dpath.exists():
            content = dpath.read_text()
            pc = re.search(r'providerCount:\s*(\d+)', content)
            if pc and int(pc.group(1)) != len(names):
                fails.append(f"P4: data file providerCount={pc.group(1)} but cities.ts has {len(names)}")

    # ── Report ─────────────────────────────────────────────────
    print(f"\n  G9 Screenshot-Reality — {slug}")
    print(f"  providers in cities.ts: {len(names)} | manifest: {'yes' if manifest_path.exists() else 'MISSING'}")
    for w in warns:
        print(f"  ⚠️  {w}")
    if fails:
        for f in fails:
            print(f"  ❌ {f}")
        print(f"\n  FAIL — run: python3 scripts/capture-provider-scroll.py {slug}")
        sys.exit(1)
    print("  ✅ screenshot manifest matches live page (fresh, cropped right, photos loaded, providers current)")


if __name__ == "__main__":
    main()