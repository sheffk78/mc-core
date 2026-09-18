#!/usr/bin/env python3
"""Batch curl-verify statute URLs: HTTP status + statute-number text match."""
import subprocess, re, sys, json, html as htmlmod

try:
    import pypdf, io
except ImportError:
    pypdf = None

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def curl(url, timeout=45):
    """Return (status, body_bytes)."""
    p = subprocess.run(
        ["curl", "-sS", "-L", "--max-time", str(timeout), "-A", UA,
         "-o", "-", "-w", "\n__STATUS__%{http_code}__END__", url],
        capture_output=True)
    out = p.stdout
    m = re.search(rb"\n__STATUS__(\d{3})__END__$", out)
    status = int(m.group(1)) if m else 0
    body = out[:m.start()] if m else out
    return status, body

def text_of(body):
    try:
        s = body.decode("utf-8", "ignore")
    except Exception:
        s = ""
    s = htmlmod.unescape(s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def check(name, url, patterns, out):
    status, body = curl(url)
    txt = text_of(body)
    # PDFs: extract text properly instead of raw byte search (streams are compressed)
    if pypdf is not None and body[:5] == b"%PDF-":
        try:
            reader = pypdf.PdfReader(io.BytesIO(body))
            txt = text_of("".join((pg.extract_text() or "") for pg in reader.pages).encode())
        except Exception as e:
            print(f"   pdf-extract failed: {e}")
    found = {}
    for pat in patterns:
        rx = re.compile(pat)
        m = rx.search(txt)
        ctx = ""
        if m:
            ctx = txt[max(0, m.start()-80):m.end()+120]
        found[pat] = ctx
    hit = any(found[p] for p in patterns)
    out[name] = {"url": url, "status": status, "hit": hit, "ctx": found}
    print(f"{name}: {status} hit={hit} len={len(body)}")
    for p, c in found.items():
        if c:
            print(f"   [{p}] ...{c[:180]}...")

if __name__ == "__main__":
    out = {}
    jobs = json.load(open(sys.argv[1]))
    for j in jobs:
        try:
            check(j["name"], j["url"], j["patterns"], out)
        except Exception as e:
            out[j["name"]] = {"url": j["url"], "error": str(e)}
            print(f"{j['name']}: ERROR {e}")
    json.dump(out, open(sys.argv[2], "w"), indent=1)