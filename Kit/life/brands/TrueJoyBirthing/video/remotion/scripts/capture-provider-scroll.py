#!/usr/bin/env python3
"""
Capture the provider directory section from a live TJB city page
for use in the ProviderScrollSlide video scene.

The ProviderScrollSlide is FULL-WIDTH (1920×1080, no phone frame).
This script captures a full-page screenshot and crops to the provider
section, saving as {slug}-fullpage-scroll.png.

Usage:
    python3 scripts/capture-provider-scroll.py <slug>

Output:
    Remotion public/images/{slug}-fullpage-scroll.png (cropped)

Auto-updates:
    - Estimates maxScroll = screenshot_height - 1080 (video frame)
    - Reports recommended duration_seconds based on scroll speed

Requires:
    pip install playwright Pillow
    playwright install chromium
"""

import asyncio
import re
import sys
import os
from datetime import datetime, timezone
import json
import time
from pathlib import Path

from PIL import Image

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


REMOTION_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = REMOTION_DIR / "public" / "images"


async def capture(slug: str) -> dict:
    """Full-page capture then crop to provider section."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        # Inject a script BEFORE the page loads that intercepts lazy loading.
        # This runs before any page script, so we can override the loading attribute
        # on every img element as it's created, forcing all images to load immediately.
        await page.add_init_script("""
            // Force all images to load eagerly, overriding lazy loading
            const observer = new MutationObserver((mutations) => {
                for (const mutation of mutations) {
                    for (const node of mutation.addedNodes) {
                        if (node.tagName === 'IMG') {
                            node.loading = 'eager';
                            node.removeAttribute('loading');
                        }
                        if (node.querySelectorAll) {
                            node.querySelectorAll('img[loading="lazy"]').forEach(img => {
                                img.loading = 'eager';
                                img.removeAttribute('loading');
                            });
                        }
                    }
                }
            });
            observer.observe(document.documentElement, { childList: true, subtree: true });
        """)

        import os as _os
        url = _os.environ.get("TJB_CAPTURE_BASE", "https://truejoybirthing.com") + f"/birth-support/{slug}/"
        print(f"  Navigating to {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)

        # Wait for page to render. Astro pages hydrate and create img elements
        # after DOMContentLoaded, so we need to wait for content to appear.
        for attempt in range(10):
            await page.wait_for_timeout(2000)
            img_count = await page.evaluate("document.querySelectorAll('img').length")
            h2_count = await page.evaluate("document.querySelectorAll('h2').length")
            print(f"  Wait attempt {attempt+1}: {img_count} images, {h2_count} h2 headings")
            if img_count > 0 and h2_count > 0:
                break
        else:
            print("  WARNING: Page may not have fully rendered")

        # CRITICAL FIX: Remove loading="lazy" from ALL images, then force a
        # fresh fetch by clearing and re-setting src on every non-placeholder
        # image. This is the ONLY reliable way to get Chromium headless to
        # paint lazy-loaded images in screenshots. Without this, images report
        # naturalWidth > 0 but render as grey/blank in the screenshot.
        removed = await page.evaluate("""() => {
            let count = 0;
            document.querySelectorAll('img').forEach(img => {
                if (img.hasAttribute('loading')) {
                    img.removeAttribute('loading');
                    count++;
                }
            });
            return count;
        }""")
        print(f"  Removed loading attribute from {removed} images")

        reset_count = await page.evaluate("""() => {
            let count = 0;
            document.querySelectorAll('img').forEach(img => {
                if (img.src.includes('placeholder')) return;
                const src = img.src;
                img.src = '';
                img.src = src;
                count++;
            });
            return count;
        }""")
        print(f"  Reset src on {reset_count} non-placeholder images to force fresh fetch")

        # Wait for all images to finish loading
        await page.evaluate("""() => {
            return Promise.all(Array.from(document.querySelectorAll('img')).map(img => {
                if (img.src.includes('placeholder')) return Promise.resolve();
                if (img.complete && img.naturalWidth > 0) return Promise.resolve();
                return new Promise(resolve => {
                    img.onload = img.onerror = () => resolve();
                    setTimeout(resolve, 15000);
                });
            }));
        }""")
        await page.wait_for_timeout(2000)

        # Scroll to each non-placeholder provider image individually to trigger
        # lazy loading. This is CRITICAL: Chromium headless does not fetch lazy-
        # loaded images until they are scrolled into view. Setting loading="eager"
        # or removing the attribute is NOT enough — Chromium still defers the fetch.
        provider_imgs = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('img'))
                .filter(img => {
                    const src = img.getAttribute('src') || '';
                    return (src.includes('/images/doulas/') || src.includes('/images/provider') || src.includes('/images/providers/')) && !src.includes('placeholder');
                })
                .map(img => ({
                    src: img.getAttribute('src'),
                    top: img.getBoundingClientRect().top + window.scrollY,
                }));
        }""")
        print(f"  Found {len(provider_imgs)} non-placeholder provider images")
        for img_data in provider_imgs:
            target_y = max(0, img_data['top'] - 400)
            await page.evaluate(f"window.scrollTo(0, {target_y})")
            await page.wait_for_timeout(2000)

        # Wait for all non-placeholder images to finish loading and decoding
        print("  Waiting for all images to decode...")
        await page.evaluate("""() => {
            return Promise.all(Array.from(document.querySelectorAll('img')).map(img => {
                if (img.src.includes('placeholder')) return Promise.resolve();
                if (img.complete && img.naturalWidth > 0) return img.decode().catch(() => Promise.resolve());
                return new Promise(resolve => {
                    img.onload = () => { img.decode().then(resolve).catch(resolve); };
                    img.onerror = resolve;
                    setTimeout(resolve, 15000);
                });
            }));
        }""")
        await page.wait_for_timeout(2000)

        # Final check: count loaded vs unloaded
        counts = await page.evaluate('''() => {
            const imgs = document.querySelectorAll('img');
            let loaded = 0, unloaded = 0;
            const unloadedSrcs = [];
            imgs.forEach(img => {
                if (img.naturalWidth > 0) loaded++;
                else { unloaded++; unloadedSrcs.push(img.getAttribute('src')); }
            });
            return { total: imgs.length, loaded, unloaded, unloadedSrcs };
        }''')
        print(f"  Image status: {counts['loaded']}/{counts['total']} loaded, {counts['unloaded']} failed")
        if counts['unloadedSrcs']:
            non_placeholder_failed = [s for s in counts['unloadedSrcs'] if 'placeholder' not in s]
            if non_placeholder_failed:
                print(f"  WARNING: Non-placeholder images failed to load: {non_placeholder_failed}")
            else:
                print(f"  (All failures are placeholder SVGs — expected)")

        # Find provider section heading bounds
        bounds = await page.evaluate('''() => {
            const h2s = document.querySelectorAll('h2');
            let providerH2 = null, hospitalH2 = null;
            for (const h of h2s) {
                const text = h.textContent;
                if (text.includes('Doulas') && text.includes('Midwives') && text.includes('Serving')) providerH2 = h;
                if (text.startsWith('Hospitals')) hospitalH2 = h;
            }
            if (!providerH2) {
                // Fallback: find any h2 containing "Doula"
                for (const h of h2s) {
                    if (h.textContent.includes('Doula')) providerH2 = h;
                }
            }
            if (!providerH2) return null;
            const pb = providerH2.getBoundingClientRect();
            const hb = hospitalH2 ? hospitalH2.getBoundingClientRect() : null;
            return {
                startY: Math.round(window.scrollY + pb.top - 60),
                endY: hb ? Math.round(window.scrollY + hb.top + 100) : null,
                label: providerH2.textContent
            };
        }''')

        if not bounds:
            print("ERROR: Could not find provider section heading")
            await browser.close()
            return None

        # ── Provider-card ground truth (P3 manifest) ─────────────
        # Read provider names + photo-load status straight from the DOM so the
        # gate can verify the screenshot really contains them.
        provider_cards = await page.evaluate('''() => {
            const cards = [];
            // Provider cards: elements containing a provider img inside the
            // provider section. Match the site's markup: img src contains
            // /images/doulas/, /images/provider, /images/providers/
            document.querySelectorAll('img').forEach(img => {
                const src = img.getAttribute('src') || '';
                if (!(src.includes('/images/doulas/') || src.includes('/images/provider'))) return;
                if (src.includes('placeholder')) return;
                // climb to the card container and read the name
                let card = img.closest('div');
                let name = null;
                for (let up = 0; up < 6 && card; up++) {
                    const m = card.textContent.match(/([A-Z][a-z]+(?:\s+[A-Z][a-zA-Z'-]+){1,2})/);
                    if (m && m[1].length > 5) { name = m[1]; break; }
                    card = card.parentElement;
                }
                // trim credential words that leak into the match
                if (name) {
                    name = name.replace(/\s+(DONA|Certified|Birth|Postpartum|Doula|Midwife).*$/i, '').trim();
                }
                cards.push({
                    src: src.split('/').pop(),
                    loaded: img.naturalWidth > 0,
                    name: name,
                });
            });
            return cards;
        }''')
        loaded_photos = [c for c in provider_cards if c['loaded']]
        print(f"  Provider photos loaded: {loaded_photos.__len__()}/{provider_cards.__len__()}")
        for c in provider_cards:
            if not c['loaded']:
                print(f"  ❌ PHOTO NOT LOADED: {c['src']} (initials placeholder risk)")

        print(f"  Provider heading: \"{bounds['label']}\"")
        print(f"  Crop range: y={bounds['startY']} to y={bounds['endY'] or 'page_end'}")

        # Get page height
        page_height = await page.evaluate("document.body.scrollHeight")
        print(f"  Full page height: {page_height}px")

        # Scroll to top before taking full-page screenshot
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)

        # Take a full-page screenshot. This is more reliable than viewport
        # stitching for lazy-loaded images: Chromium handles painting all
        # elements at once, so images that were decoded during scrolling stay
        # painted. Viewport stitching evicts images from the paint cache when
        # they scroll out of view, causing them to appear grey even though
        # they report naturalWidth > 0.
        raw_path = PUBLIC_DIR / f"{slug}-fullpage-raw.png"
        PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(raw_path), full_page=True)
        print(f"  Full-page screenshot: {raw_path}")

        await browser.close()

        return {
            "raw_path": str(raw_path),
            "crop_start": bounds["startY"],
            "crop_end": bounds["endY"],
            "provider_cards": provider_cards,
            "section_label": bounds["label"],
        }


def process(raw_path: str, output_path: str, crop_start: int, crop_end):
    """Crop to provider section and save."""
    img = Image.open(raw_path)
    w, h = img.size
    end = crop_end if crop_end else h
    # Ensure crop bounds are within image
    start = max(0, crop_start)
    end = min(end, h)
    cropped = img.crop((0, start, w, end))
    cropped.save(output_path)
    scrollable = cropped.height - 1080
    print(f"  Cropped: {output_path} ({cropped.size[0]}x{cropped.size[1]})")
    print(f"  maxScroll (scrollable area): {scrollable}px")

    # Recommend duration
    for dur, label in [(10, "fast (~300px/s, dense text suffers)"),
                       (12, "good (~230px/s, recommended minimum)"),
                       (14, "relaxed (~195px/s, recommended for text-heavy)"),
                       (18, "slow (~145px/s, only if narration is long)")]:
        speed = scrollable / dur
        print(f"    {dur}s = {speed:.0f} px/s — {label}")

    # Remove raw
    Path(raw_path).unlink(missing_ok=True)
    return scrollable


def update_data_file(slug: str, screenshot_path: str, max_scroll: int, provider_count: int):
    """Update the scene data file with new screenshot path and maxScroll."""
    data_path = REMOTION_DIR / "src" / "data" / f"{slug}-data.ts"
    if not data_path.exists():
        print(f"  Data file {data_path} not found — skipping auto-update")
        return

    content = data_path.read_text()

    # Replace screenshotPath
    content = re.sub(
        r'(screenshotPath:\s*)"[^"]*"',
        f'\\g<1>"{screenshot_path}"',
        content
    )

    # Replace maxScroll if present
    if "maxScroll:" in content:
        content = re.sub(
            r'(maxScroll:\s*)\d+',
            f'\\g<1>{max_scroll}',
            content
        )

    # Update provider count
    content = re.sub(
        r'(providerCount:\s*)\d+',
        f'\\g<1>{provider_count}',
        content
    )

    data_path.write_text(content)
    print(f"  Data file updated: {data_path}")
    print(f"    screenshotPath: {screenshot_path}")
    print(f"    maxScroll: {max_scroll}")
    print(f"    providerCount: {provider_count}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/capture-provider-scroll.py <slug>")
        print("  Also supports: python3 scripts/capture-provider-scroll.py <slug> --fullpage-only")
        sys.exit(1)

    slug = sys.argv[1]
    fullpage_only = "--fullpage-only" in sys.argv

    result = await capture(slug)
    if not result:
        sys.exit(1)

    # Crop the full-page screenshot to the provider section
    out_name = f"{slug}-fullpage-scroll.png"
    out_path = str(PUBLIC_DIR / out_name)
    max_scroll = process(
        raw_path=result["raw_path"],
        output_path=out_path,
        crop_start=result["crop_start"],
        crop_end=result["crop_end"],
    )

    if fullpage_only:
        print(f"\nDone (fullpage only): {out_path}")
        print("  Next step: open the fullpage scroll, manually adjust crop if needed,")
        print("  then run without --fullpage-only to update the data file.")
        return

    # Count provider cards from the cities.ts data
    provider_count = 0
    cities_path = Path.home() / "Projects" / "truejoybirthing-website" / "src" / "data" / "cities.ts"
    if cities_path.exists():
        cities_content = cities_path.read_text()
        # Find the slug position, then find localDoulas after it
        slug_pos = cities_content.find(f'"{slug}"')
        if slug_pos >= 0:
            ld_pos = cities_content.find('localDoulas:', slug_pos)
            if ld_pos >= 0:
                bracket_start = cities_content.find('[', ld_pos)
                if bracket_start >= 0:
                    # Track bracket depth to find the matching close
                    depth = 0
                    i = bracket_start
                    while i < len(cities_content):
                        if cities_content[i] == '[':
                            depth += 1
                        elif cities_content[i] == ']':
                            depth -= 1
                            if depth == 0:
                                break
                        i += 1
                    doulas_block = cities_content[bracket_start+1:i]
                    provider_count = len(re.findall(r'name:\s*"', doulas_block))
    if provider_count == 0:
        print("  WARNING: Could not count providers from cities.ts")
        provider_count = 12  # Safe fallback for known cities

    # Update data file
    update_data_file(slug, f"images/{out_name}", max_scroll, provider_count)

    # ── Write capture manifest (ground truth for the G9 gate) ────
    manifest = {
        "slug": slug,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "live_url": (os.environ.get("TJB_CAPTURE_BASE", "https://truejoybirthing.com") + f"/birth-support/{slug}/"),
        "screenshot": out_name,
        "crop": {"start": result["crop_start"], "end": result["crop_end"]},
        "section_label": result.get("section_label"),
        "provider_photos": result.get("provider_cards", []),
        "provider_count": provider_count,
    }
    manifest_path = REMOTION_DIR / "public" / "images" / f"{slug}-capture-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    unloaded = [c for c in result.get("provider_cards", []) if not c["loaded"]]
    if unloaded:
        print(f"\n❌ CAPTURE FAILED GATE: {len(unloaded)} provider photo(s) did NOT load:")
        for c in unloaded:
            print(f"   {c['src']}")
        print("   The video would show initials placeholders. Fix image loading and re-capture.")
        sys.exit(1)
    print(f"  Manifest written: {manifest_path.name}")

    print(f"\nDone: {out_path}")
    print("  Capture a still from the remotion composition to send to Jeff for approval.")
    print("  Get approval before running the full render.")


if __name__ == "__main__":
    asyncio.run(main())