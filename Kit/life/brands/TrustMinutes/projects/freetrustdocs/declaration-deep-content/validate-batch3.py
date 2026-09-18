#!/usr/bin/env python3
"""Validator for the 8 state deep-content files: schema, word counts, banned phrases."""
import json, os, re, sys

DD = '/Users/socializerender/.openclaw/workspace/Kit/life/brands/TrustMinutes/projects/freetrustdocs/declaration-deep-content'
STATES = [
    ('Kentucky', 'kentucky'), ('Louisiana', 'louisiana'), ('Maine', 'maine'),
    ('Maryland', 'maryland'), ('Massachusetts', 'massachusetts'),
    ('Michigan', 'michigan'), ('Minnesota', 'minnesota'), ('Mississippi', 'mississippi'),
]
BANNED = ['demand the full trust instrument', 'demanding the full trust instrument',
          'demands the full trust documents', 'materially deficient', 'reject it and demand',
          'you should', 'you must', 'consider consulting']
RANGES = {'how_it_works': (130, 170), 'common_mistakes': (100, 140), 'state_notes': (120, 170)}
FAQ_A = (60, 90)

rows, fails = [], 0
for st, slug in STATES:
    path = f'{DD}/declaration-deep-{slug}.json'
    if not os.path.exists(path):
        rows.append((slug, 'MISSING FILE')); fails += 1; continue
    try:
        d = json.load(open(path))
    except Exception as e:
        rows.append((slug, f'JSON-ERROR: {e}')); fails += 1; continue
    errs = []
    if d.get('state') != st: errs.append(f"state {d.get('state')!r} != {st!r}")
    if d.get('document') != 'declaration-of-trust': errs.append('doc field')
    b = d.get('blocks', {})
    if set(b.keys()) != {'how_it_works', 'faq', 'common_mistakes', 'state_notes'}:
        errs.append(f'block keys {sorted(b.keys())}')
    for k, (lo, hi) in RANGES.items():
        n = len(b.get(k, '').split())
        if not (lo <= n <= hi): errs.append(f'{k}={n}w not {lo}-{hi}')
    faq = b.get('faq', [])
    if len(faq) != 4: errs.append(f'faq len {len(faq)} != 4')
    for i, item in enumerate(faq):
        if not isinstance(item, dict) or set(item.keys()) != {'q', 'a'}:
            errs.append(f'faq[{i}] keys')
            continue
        n = len(item['a'].split())
        if not (FAQ_A[0] <= n <= FAQ_A[1]): errs.append(f'faq[{i}].a={n}w not 60-90')
    blob = json.dumps(d).lower()
    hits = [p for p in BANNED if p in blob]
    if hits: errs.append(f'banned: {hits}')
    raw = json.dumps(d, ensure_ascii=False)
    if '\u2014' in raw or '\u2013' in raw: errs.append('em/en-dash')
    if re.search(r'[\U0001F300-\U0001FAFF\u2600-\u27BF]', raw): errs.append('emoji')
    # statute sanity: citations must appear in the spec for that state
    spec = json.load(open(f'{DD}/INPUT-SPEC-48.json'))[st]
    allowed = json.dumps(spec, ensure_ascii=False)
    content = ' '.join([b.get('how_it_works', ''), b.get('common_mistakes', ''), b.get('state_notes', '')] +
                       [f.get('a', '') for f in faq])
    cited = set(re.findall(r'(?:§+ ?)?\d+(?:[.,\-–]\d+)+(?:[.,]\d+)?', content))
    bad = [c for c in cited if c and c not in allowed]
    if bad: errs.append(f'uncited-statutes: {bad[:6]}')
    rows.append((slug, 'PASS' if not errs else '; '.join(errs)))
    if errs: fails += 1

for slug, r in rows:
    print(f'{slug:16s} {r}')
print(f'\n{len(rows)} files, {fails} failing')
sys.exit(1 if fails else 0)