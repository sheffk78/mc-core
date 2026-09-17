#!/usr/bin/env python3
"""Build deterministic fixtures for the directory gate tests.
Good page = aligned with canonical SEO requirements (proven in eval 2026-09-17).
Bad page = banned word in meta attribute + zero H1 + long meta (must fail G2.5).
Run: python3 tests/make_fixtures.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FX = os.path.join(HERE, "fixtures")
TOPIC = "trustee services salt lake city"

os.makedirs(f"{FX}/dist", exist_ok=True)
os.makedirs(f"{FX}/dist-bad", exist_ok=True)

SCHEMA = (
    '<script type="application/ld+json">[{"@type":"Organization","name":"TrustOffice",'
    '"url":"https://trustoffice.app/"},{"@type":"BreadcrumbList","itemListElement":[]},'
    '{"@type":"FAQPage","mainEntity":[]}]</script>'
)

GOOD = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{TOPIC.title()}: Find a Co-Trustee | TrustOffice</title>
<meta name="description" content="Trustee services Salt Lake City: fiduciary firms, SEC-registered advisers and Utah attorneys you can contact directly — independent, updated for 2026.">
<link rel="canonical" href="https://trustoffice.app/directory/salt-lake-city-ut/">
<meta property="og:url" content="https://trustoffice.app/directory/salt-lake-city-ut/">
{SCHEMA}
</head><body>
<h1>Trustee services in Salt Lake City</h1>
<p>{TOPIC} directory lists professionals who serve as co-trustee or successor trustee.
Salt Lake City is Utah's fiduciary center: the Utah State Bar, SEC-registered advisers
downtown, and Provo trust practices all serve Utah County families.</p>
<nav><a href="https://trustoffice.app/directory/">All metros</a></nav>
</body></html>"""

BAD = GOOD.replace("</title>", " — trusted and verified</title>").replace("<h1>", "<h2>").replace("</h1>", "</h2>")

open(f"{FX}/dist/test.html", "w").write(GOOD)
open(f"{FX}/dist-bad/test.html", "w").write(BAD)

manifest = {"pages": [{"path": "test.html", "url": "https://trustoffice.app/directory/salt-lake-city-ut/",
                       "slug": "salt-lake-city-ut", "topic": TOPIC, "metro_tokens": ["salt lake city", "utah"],
                       "page_type": "metro-hub"}]}
json.dump(manifest, open(f"{FX}/pages-manifest.json", "w"), indent=2)
# negative sitemap test: manifest missing its last page
bad_manifest = dict(manifest)
bad_manifest["pages"] = []
json.dump(bad_manifest, open(f"{FX}/pages-manifest-bad.json", "w"), indent=2)

urls = [p["url"] for p in manifest["pages"]]
open(f"{FX}/sitemap-good.xml", "w").write(
    '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>")
open(f"{FX}/sitemap-bad.xml", "w").write(
    '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    "<url><loc>https://trustoffice.app/other/</loc></url></urlset>")
open(f"{FX}/counts.json", "w").write(json.dumps({"by_type": {"adviser": 1}}))

print(f"fixtures written to {FX}")