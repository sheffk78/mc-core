import json, os, sys

base = "/Users/socializerender/.openclaw/workspace/Kit/life/brands/TrustMinutes/projects/freetrustdocs/declaration-deep-content"

states = ["Alabama","Alaska","Arizona","Arkansas","Colorado","Connecticut","Delaware","District of Columbia"]
slugs = ["alabama","alaska","arizona","arkansas","colorado","connecticut","delaware","district-of-columbia"]

schema_keys = {"state", "document", "blocks"}
block_keys = {"how_it_works", "faq", "common_mistakes", "state_notes"}
faq_keys = {"q", "a"}

BANNED = [
    "demand the full trust instrument",
    "demanding the full trust instrument",
    "demands the full trust documents",
    "materially deficient",
    "reject it and demand",
    "you should",
    "you must",
    "consider consulting",
]

WCOUNT = {
    "how_it_works": (130, 170),
    "faq_answer": (60, 90),
    "common_mistakes": (100, 140),
    "state_notes": (120, 170),
}

results = []
all_pass = True

for state, slug in zip(states, slugs):
    path = f"{base}/declaration-deep-{slug}.json"
    if not os.path.exists(path):
        print(f"FAIL | {state} | FILE MISSING")
        all_pass = False
        continue

    with open(path) as f:
        data = json.load(f)

    issues = []

    # Schema check
    if set(data.keys()) != schema_keys:
        issues.append(f"top-level keys: {set(data.keys())} != {schema_keys}")
    if data.get("state") != state:
        issues.append(f"state field: '{data.get('state')}' != '{state}'")
    if data.get("document") != "declaration-of-trust":
        issues.append(f"document field: '{data.get('document')}'")
    blocks = data.get("blocks", {})
    if set(blocks.keys()) != block_keys:
        issues.append(f"block keys: {set(blocks.keys())} != {block_keys}")
    faqs = blocks.get("faq", [])
    if len(faqs) != 4:
        issues.append(f"faq count: {len(faqs)} != 4")
    for i, faq in enumerate(faqs):
        if set(faq.keys()) != faq_keys:
            issues.append(f"faq[{i}] keys: {set(faq.keys())}")

    # Word counts
    def wc(text):
        return len(text.split())

    hw_wc = wc(blocks.get("how_it_works", ""))
    lo, hi = WCOUNT["how_it_works"]
    if not (lo <= hw_wc <= hi):
        issues.append(f"how_it_works: {hw_wc} words (range {lo}-{hi})")

    for i, faq in enumerate(faqs):
        a_wc = wc(faq.get("a", ""))
        lo, hi = WCOUNT["faq_answer"]
        if not (lo <= a_wc <= hi):
            issues.append(f"faq[{i}] answer: {a_wc} words (range {lo}-{hi})")

    cm_wc = wc(blocks.get("common_mistakes", ""))
    lo, hi = WCOUNT["common_mistakes"]
    if not (lo <= cm_wc <= hi):
        issues.append(f"common_mistakes: {cm_wc} words (range {lo}-{hi})")

    sn_wc = wc(blocks.get("state_notes", ""))
    lo, hi = WCOUNT["state_notes"]
    if not (lo <= sn_wc <= hi):
        issues.append(f"state_notes: {sn_wc} words (range {lo}-{hi})")

    # Banned phrases (case-insensitive)
    full_text = json.dumps(data).lower()
    for phrase in BANNED:
        if phrase.lower() in full_text:
            issues.append(f"BANNED PHRASE: '{phrase}'")

    # Emoji check
    import re
    emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251\U0001f900-\U0001f9FF\U0001fa00-\U0001fa6f\U0001fa70-\U0001faff\U00002600-\U000026FF]")
    if emoji_pattern.search(blocks.get("how_it_works","")) or emoji_pattern.search(blocks.get("common_mistakes","")) or emoji_pattern.search(blocks.get("state_notes","")):
        issues.append("EMOJI DETECTED")

    # Em-dash check
    if "\u2014" in blocks.get("how_it_works","") or "\u2014" in blocks.get("common_mistakes","") or "\u2014" in blocks.get("state_notes",""):
        issues.append("EM-DASH DETECTED")

    status = "PASS" if not issues else "FAIL"
    if issues:
        all_pass = False
    results.append((state, status, issues))

print(f"{'State':<25} {'Status':<6} Issues")
print("-" * 80)
for state, status, issues in results:
    issue_str = "; ".join(issues) if issues else "none"
    print(f"{state:<25} {status:<6} {issue_str}")

print()
print("OVERALL:", "ALL PASS" if all_pass else "SOME FAILURES")
sys.exit(0 if all_pass else 1)