#!/usr/bin/env python3
"""Validate FreeTrustDocs declaration-of-trust deep content files.

Checks per file: schema, word counts, banned phrases, emoji, em-dashes,
JSON parse. Prints a PASS/FAIL table and exits nonzero on any FAIL.
"""
import json
import re
import sys

DIR = "/Users/socializerender/.openclaw/workspace/Kit/life/brands/TrustMinutes/projects/freetrustdocs/declaration-deep-content"

STATES = ["Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas"]
SLUGS = ["florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas"]

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


def wc(s: str) -> int:
    return len(s.split())


def check(slug: str, state: str):
    fails = []
    path = f"{DIR}/declaration-deep-{slug}.json"
    try:
        with open(path) as f:
            doc = json.load(f)
    except Exception as e:
        return [f"JSON parse error: {e}"], None

    if doc.get("state") != state:
        fails.append(f"state != {state}")
    if doc.get("document") != "declaration-of-trust":
        fails.append("document != declaration-of-trust")

    blocks = doc.get("blocks", {})
    if set(blocks.keys()) != {"how_it_works", "faq", "common_mistakes", "state_notes"}:
        fails.append(f"block keys wrong: {sorted(blocks.keys())}")

    hiw = blocks.get("how_it_works", "")
    if not (130 <= wc(hiw) <= 170):
        fails.append(f"how_it_works wc {wc(hiw)} not in 130-170")

    faq = blocks.get("faq", [])
    if len(faq) != 4:
        fails.append(f"faq has {len(faq)} items, need 4")
    for i, item in enumerate(faq):
        if "q" not in item or "a" not in item:
            fails.append(f"faq[{i}] missing q/a")
        else:
            if not (60 <= wc(item["a"]) <= 90):
                fails.append(f"faq[{i}].a wc {wc(item['a'])} not in 60-90")

    cm = blocks.get("common_mistakes", "")
    if not (100 <= wc(cm) <= 140):
        fails.append(f"common_mistakes wc {wc(cm)} not in 100-140")

    sn = blocks.get("state_notes", "")
    if not (120 <= wc(sn) <= 170):
        fails.append(f"state_notes wc {wc(sn)} not in 120-170")

    full = json.dumps(doc)
    for b in BANNED:
        if b in full.lower():
            fails.append(f"banned phrase: {b!r}")
    if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", full):
        fails.append("emoji found")
    if "\u2014" in full or "\u2013" in full:
        fails.append("em/en dash found")
    if re.search(r"\b(you|your)\b", full.lower()):
        fails.append("second-person (you/your) found")

    return fails, doc


def main():
    results = []
    for slug, state in zip(SLUGS, STATES):
        fails, _ = check(slug, state)
        results.append((slug, state, fails))

    print(f"{'State':<12} {'Status':<7} {'Details'}")
    print("-" * 70)
    all_pass = True
    for slug, state, fails in results:
        status = "PASS" if not fails else "FAIL"
        if fails:
            all_pass = False
        detail = "; ".join(fails) if fails else ""
        print(f"{state:<12} {status:<7} {detail}")

    if all_pass:
        print("\nALL 8 PASS")
        sys.exit(0)
    else:
        print(f"\n{sum(1 for _,_,f in results if f)} FILE(S) FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()