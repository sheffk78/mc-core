#!/usr/bin/env python3
"""AI Slop Checker for TrustParaTodos articles."""
import glob
import re

RED_FLAGS_EN = [
    "i hope this email finds you well",
    "i hope this finds you well",
    "i'd be delighted",
    "feel free to reach out",
    "feel free to",
    "delve into",
    "moreover",
    "furthermore",
    "let's dive in",
    "without further ado",
    "it's important to note",
    "in conclusion",
    "in summary",
    "in a nutshell",
    "game-changer",
    "revolutionary",
    "tap into",
    "leverage",
    "utilize",
    "utilizing",
    "embark on",
    "pivotal",
    "intricate",
    "elucidate",
    "illuminate",
    "unveil",
    "landscape",
    "paradigm shift",
    "synergy",
    "seamlessly",
    "effortlessly",
    "supercharge",
    "turbocharge",
    "passion",
    "hustle",
    "grind",
    "crush it",
    "nail it",
    "insanely",
    "incredibly",
    "absolutely",
    "undoubtedly",
]

GENERIC_SPANISH_INDICATORS = [
    (r"\bes importante?\b", "es importante -- generic filler"),
    (r"\bmuy importante\b", "muy importante -- vague emphasis"),
    (r"\bbasically\b", "basically -- filler"),
    (r"\bbasica?mente\b", "basicamente -- filler"),
]

def check_article(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---')
    body = parts[2] if len(parts) >= 3 else content
    lines = body.split('\n')

    issues = []

    for phrase in RED_FLAGS_EN:
        if phrase in body.lower():
            for i, line in enumerate(lines, 1):
                if phrase.lower() in line.lower():
                    issues.append({'type': 'RED_FLAG', 'sev': 'HIGH', 'phrase': phrase, 'line': i})
                    break

    for pattern, label in GENERIC_SPANISH_INDICATORS:
        match = re.search(pattern, body.lower())
        if match:
            line_num = body[:match.start()].count('\n') + 1
            issues.append({'type': label, 'sev': 'LOW', 'phrase': label, 'line': line_num})

    em_count = body.count('\u2014')
    if em_count > 0:
        issues.append({'type': 'EM_DASH', 'sev': 'LOW', 'phrase': 'em dashes', 'line': 0, 'count': em_count})

    high = len([i for i in issues if i['sev'] == 'HIGH'])
    low = len([i for i in issues if i['sev'] == 'LOW'])
    clean = high == 0
    score = max(0, 100 - (high * 20 + low * 5))

    return {
        'file': filepath,
        'title': filepath.split('/')[-1].replace('.md', '').replace('-', ' ').title(),
        'word_count': len(body.split()),
        'high': high,
        'low': low,
        'score': score,
        'clean': clean,
        'issues': issues
    }

articles = sorted(glob.glob('/Users/socializerender/.openclaw/workspace/Kit/life/brands/TrustParaTodos/content/articles/*.md'))

print("=" * 60)
print("AI SLOP CHECK - TrustParaTodos (Spanish-tuned)")
print("=" * 60)

all_pass = True
for article in articles:
    r = check_article(article)
    status = "PASS" if r['clean'] else "NEEDS WORK"
    if not r['clean']:
        all_pass = False

    print()
    print("FILE:", r['title'])
    print("  Words:", r['word_count'], "| High:", r['high'], "| Low:", r['low'],
          "| Score:", r['score'], "/100 |", status)

    if r['issues']:
        for issue in r['issues']:
            icon = "HIGH" if issue['sev'] == 'HIGH' else "LOW"
            print("  [" + icon + "] Line", issue['line'], "-", issue['type'], "-", issue['phrase'])

print()
print("=" * 60)
if all_pass:
    print("ALL CLEAR - Shipable at 80%+ quality")
else:
    print("FIX HIGH issues before publishing")
print("=" * 60)