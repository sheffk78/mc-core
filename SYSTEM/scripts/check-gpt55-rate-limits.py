#!/usr/bin/env python3
"""Check recent Hermes logs for GPT-5.5 / OpenAI Codex rate-limit signals."""
from __future__ import annotations

from pathlib import Path
import re

LOG_DIR = Path.home() / ".hermes" / "logs"
PATTERNS = re.compile(r"(openai-codex|gpt-5\.5|codex).{0,160}(?:(?<![\d,])429(?![\d,])|rate[- ]?limit(?:ed|s)?|too many requests|quota exceeded|usage limit|session usage limit|exhausted)|(?:(?<![\d,])429(?![\d,])|rate[- ]?limit(?:ed|s)?|too many requests|quota exceeded|usage limit|session usage limit|exhausted).{0,160}(openai-codex|gpt-5\.5|codex)", re.I)

hits = []
for path in sorted(LOG_DIR.glob("*.log")):
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except Exception:
        continue
    for idx, line in enumerate(lines[-2000:], 1):
        if PATTERNS.search(line):
            hits.append((path.name, idx, line.strip()[:500]))

if not hits:
    print("OK: no recent GPT-5.5/OpenAI Codex rate-limit signals found in Hermes logs.")
else:
    print(f"RATE_LIMIT_SIGNALS: {len(hits)} recent GPT-5.5/OpenAI Codex hit(s)")
    for name, idx, line in hits[-20:]:
        print(f"{name}:{idx}: {line}")
