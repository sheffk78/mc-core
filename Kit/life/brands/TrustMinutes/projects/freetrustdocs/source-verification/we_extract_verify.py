#!/usr/bin/env python3
"""Verify statute URLs using web_extract (bypasses Cloudflare via Hermes fetcher)."""
import sys, json, re
from hermes_tools import web_extract, read_file

jobs = json.load(open(sys.argv[1]))
try:
    out = json.load(open(sys.argv[2]))
except Exception:
    out = {}

urls = [j["url"] for j in jobs]
res = web_extract(urls, char_limit=20000)
by_url = {r["url"]: r for r in res["results"]}
for j in jobs:
    r = by_url.get(j["url"])
    name = j["name"]
    if not r:
        out[name] = {"url": j["url"], "status": "no-result"}
        print(f"{name}: NO RESULT")
        continue
    content = r.get("content") or ""
    err = r.get("error")
    found = {}
    for pat in j["patterns"]:
        m = re.search(pat, content, re.I)
        found[pat] = content[max(0, m.start()-120):m.end()+160].replace("\n", " ") if m else ""
    hit = any(found.values())
    out[name] = {"url": j["url"], "status": 200 if (content and not err) else 0,
                 "error": err, "len": len(content), "hit": hit, "ctx": found}
    print(f"{name}: content_len={len(content)} err={err} hit={hit}")
    for p, c in found.items():
        if c:
            print(f"   [{p}] ...{c[:220]}...")
json.dump(out, open(sys.argv[2], "w"), indent=1)