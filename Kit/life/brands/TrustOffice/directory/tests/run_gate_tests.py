#!/usr/bin/env python3
"""Replay harness for the directory pipeline gates (build-standard L5).
Runs the full positive+negative gate matrix and asserts via exit codes AND
evidence JSONs. Exit 0 = all gates behave. Re-run on any script/model change.
Run: python3 tests/run_gate_tests.py   (calls tests/make_fixtures.py first)
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FX = os.path.join(HERE, "fixtures")
SCRIPT = os.path.join(BASE, "scripts", "directory-preflight.py")
PLAN = os.path.join(BASE, "..", "reports", "directory-pilot-plan-2026-09-17.md")

subprocess.run([sys.executable, os.path.join(HERE, "make_fixtures.py")], check=True)

def gate(name, dist, manifest, sitemap=None, research=False):
    args = [sys.executable, SCRIPT, name]
    if research:
        args += [dist, manifest, "salt-lake-city-provo-ut"]
    else:
        args += [f"{FX}/{dist}", f"{FX}/{manifest}", f"{FX}/counts.json"]
        if sitemap:
            args.append(f"{FX}/{sitemap}")
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode

checks = []
def check(label, ok):
    checks.append((label, bool(ok)))
    print(f"{'✓' if ok else '✗ FAIL'} {label}")

# G2.5: good page passes, bad page fails
check("G2.5 good page exit 0", gate("G2.5", "dist", "pages-manifest.json") == 0)
bad_rc = gate("G2.5", "dist-bad", "pages-manifest.json")
bad_ev = json.load(open(f"{FX}/verify/preflight-G2-5.json"))
check("G2.5 bad page fails (nonzero)", bad_rc != 0)
check("G2.5 bad page evidence non-pass", bad_ev["pass"] is False and bad_ev["failed_pages"])

# G3: complete sitemap passes; sitemap missing the manifest URL fails
check("G3 full sitemap exit 0", gate("G3", "dist", "pages-manifest.json", "sitemap-good.xml") == 0)
g3_rc = gate("G3", "dist", "pages-manifest.json", "sitemap-bad.xml")
g3_ev = json.load(open(f"{FX}/verify/preflight-G3.json"))
check("G3 missing-URL fails", g3_rc != 0 and any("sitemap missing" in p for p in g3_ev["problems"]))

# G0.5: honest state of real SLC research (bar pass pending → FAIL, never silent-pass)
g05 = gate("G0.5", os.path.join(BASE, "artifacts", "salt-lake-city-provo-ut", "research"),
           os.path.join(BASE, "artifacts", "salt-lake-city-provo-ut", "research", "counts.json"),
           research=True)
check("G0.5 real SLC fail-closed (exit 1)", g05 == 1)

# Plan wiring: canonical tokens present
plan = open(PLAN).read()
for token in ["GENERATE → G1.5", "SEO-PREFLIGHT → G2.5", "waiting_for", "reads_from",
              "Build-standard scorecard", "crawl-freshness", "monthly LLM cron"]:
    check(f"plan has: {token}", token in plan)

failed = [k for k, v in checks if not v]
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks pass")
if failed:
    print("FAILED:", failed)
sys.exit(1 if failed else 0)