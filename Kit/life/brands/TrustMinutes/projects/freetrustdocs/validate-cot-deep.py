#!/usr/bin/env python3
# FreeTrustDocs parent-side validator for declaration deep-content files.
# Re-checks every drafter's output independently (producer != checker): schema,
# word counts, banned phrases, state-name match, statute-number sanity.
import json, glob, os, re, sys

P = '/Users/socializerender/.openclaw/workspace/Kit/life/brands/TrustMinutes/projects/freetrustdocs'
DD = f'{P}/state-deep-content'
BANNED = ['demand the full', 'demanding the full', 'demands the full',
          'materially deficient', 'reject it and demand',
          'you should', 'you must', 'consider consulting']
RANGES = {'how_it_works': (130, 170), 'common_mistakes': (100, 140), 'state_notes': (120, 170)}
FAQ_A = (60, 90)

spec48 = json.load(open(f'{DD}/INPUT-SPEC-COT-48.json'))
spec3 = json.load(open(f'{P}/declaration-deep-content/INPUT-SPEC.json'))
spec = {**{k: v for k, v in spec3.items()}}  # COT spec + original UT/CA/TX spec
spec.update(spec48)
research = json.load(open(f'{P}/all-states-research.json'))
rs = {s['state']: s for s in research['states']}

files = sorted(glob.glob(f'{DD}/state-deep-*.json'))
rows, fails = [], 0
for f in files:
    name = os.path.basename(f)
    if name == 'state-deep-texas.json' and False:
        pass
    slug = name.replace('state-deep-', '').replace('.json', '')
    try:
        d = json.load(open(f))
    except Exception as e:
        rows.append((slug, f'JSON-ERROR {e}')); fails += 1; continue
    errs = []
    if d.get('document') != 'certificate-of-trust': errs.append('doc field')
    st = d.get('state', '')
    # state name must match slug
    want = slug.replace('-', ' ').title().replace('District Of Columbia', 'District of Columbia')
    if st != want: errs.append(f'state-name {st!r} != {want!r}')
    b = d.get('blocks', {})
    for k, (lo, hi) in RANGES.items():
        n = len(b.get(k, '').split())
        if not (lo <= n <= hi): errs.append(f'{k} {n}w not {lo}-{hi}')
    faq = b.get('faq', [])
    if len(faq) != 4: errs.append(f'faq len {len(faq)}')
    for i, f2 in enumerate(faq):
        n = len(f2.get('a', '').split())
        if not (FAQ_A[0] <= n <= FAQ_A[1]): errs.append(f'faq[{i}].a {n}w')
    blob = json.dumps(d).lower()
    hits = [p for p in BANNED if p in blob]
    if hits: errs.append(f'banned: {hits}')
    if '—' in json.dumps(d, ensure_ascii=False): errs.append('em-dash')
    if re.search(r'[\U0001F300-\U0001FAFF]', json.dumps(d, ensure_ascii=False)): errs.append('emoji')
    # statute sanity: every section number cited in content should appear in spec or research record
    content = ' '.join([b.get('how_it_works',''), b.get('common_mistakes',''), b.get('state_notes','')] +
                       [f2.get('a','') for f2 in faq])
    cited = {re.sub(r'\s+', '', re.sub(r'^§+\s*', '', c)) for c in re.findall(r'(?:§+ ?)?\d+(?:[.,–-]\d+)+(?:[.,]\d+)?', content)}
    allowed = re.sub(r'\s+', '', json.dumps({**spec.get(st, {}), **{k: v for k, v in rs.get(st, {}).items() if isinstance(v, str)}}, ensure_ascii=False))
    bad = [c for c in cited if c and c not in allowed]
    if bad: errs.append(f'uncited-statutes: {bad[:4]}')
    rows.append((slug, 'PASS' if not errs else '; '.join(errs)))
    if errs: fails += 1

for slug, r in rows:
    print(f'{slug:24s} {r}')
print(f'\n{len(rows)} files, {fails} failing')
sys.exit(1 if fails else 0)