#!/usr/bin/env python3
"""
Shared quality gate helper — run automated checks on marketing content.
Used by content skills before shipping.

Usage:
  from marketing_quality_gate import run_quality_gate, QualityResult
  
  result = run_quality_gate(content, "TrustOffice", "blog")
  if result.has_failures():
      print(result.report())
      # Block shipment
  else:
      # Ship it
"""

import re
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path.home() / ".openclaw/workspace"
BRANDS_DIR = WORKSPACE / "Kit/life/brands"
GATE_LOG_DIR = WORKSPACE / "SYSTEM/cache/marketing/quality-gate-logs"

# Discord 2000 char limit safety margin
DISCORD_MAX = 1900

class CheckResult:
    def __init__(self, name, status, detail, fix=None):
        self.name = name
        self.status = status  # 'pass', 'warn', 'fail'
        self.detail = detail
        self.fix = fix

class QualityResult:
    def __init__(self, brand, content_type, results):
        self.brand = brand
        self.content_type = content_type
        self.results = results
        self.timestamp = datetime.now().isoformat()
    
    def has_failures(self):
        return any(r.status == "fail" for r in self.results)
    
    def has_warnings(self):
        return any(r.status == "warn" for r in self.results)
    
    def report(self):
        lines = [f"## Quality Gate Report — {self.brand} {self.content_type}", ""]
        for r in self.results:
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}[r.status]
            lines.append(f"{icon} {r.name}: {r.detail}")
            if r.fix and r.status in ("warn", "fail"):
                lines.append(f"   Fix: {r.fix}")
        
        if self.has_failures():
            lines.append(f"\n### Required Fixes Before Publishing:")
            for r in self.results:
                if r.status == "fail" and r.fix:
                    lines.append(f"1. {r.fix}")
        
        return "\n".join(lines)

def load_standards(brand: str) -> dict:
    """Load brand quality standards from QUALITY-STANDARDS.md and parse into sections."""
    path = BRANDS_DIR / brand / "marketing/QUALITY-STANDARDS.md"
    if not path.exists():
        return {}
    
    content = path.read_text()
    sections = {}
    current = "_header"
    current_lines = []
    
    for line in content.split("\n"):
        if line.startswith("## "):
            if current:
                sections[current] = "\n".join(current_lines)
            current = line[2:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    sections[current] = "\n".join(current_lines)
    return sections

# --- Automated (deterministic) checks ---

def check_word_count(content, standards, content_type):
    """Check minimum word count for blog posts."""
    if content_type != "blog":
        return CheckResult("Word Count", "pass", "N/A for non-blog content")
    
    words = len(content.split())
    min_words = 1500  # default
    # Try to parse from standards
    blog_section = standards.get("Blog Posts", "")
    match = re.search(r"(\d+)\s*words?", blog_section, re.I)
    if match:
        min_words = int(match.group(1))
    
    if words < min_words * 0.8:
        return CheckResult("Word Count", "fail", f"{words} words (minimum: {min_words})",
                          f"Expand to {min_words}+ words")
    elif words < min_words:
        return CheckResult("Word Count", "warn", f"{words} words (minimum: {min_words})",
                          f"Add {min_words - words} more words to hit minimum")
    return CheckResult("Word Count", "pass", f"{words} words")

def check_meta_description(content, standards, content_type):
    """Check for meta description in frontmatter."""
    if content_type != "blog":
        return CheckResult("Meta Description", "pass", "N/A")
    
    # Check YAML frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            fm = content[3:end]
            if "description:" in fm or "metaDescription:" in fm:
                # Check length
                match = re.search(r'description:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
                if match:
                    desc = match.group(1)
                    if len(desc) > 160:
                        return CheckResult("Meta Description", "warn", f"{len(desc)} chars (max 160)")
                    return CheckResult("Meta Description", "pass", f"{len(desc)} chars")
    return CheckResult("Meta Description", "fail", "Missing meta description in frontmatter",
                      "Add description field to YAML frontmatter (120-160 chars)")

def check_forbidden_phrases(content, standards, content_type):
    """Check for forbidden phrases from standards."""
    copy_section = standards.get("Copy Rules", "")
    # Extract forbidden phrases (lines starting with "avoid" or in quotes)
    forbidden = []
    for line in copy_section.split("\n"):
        if "avoid" in line.lower() or "forbidden" in line.lower():
            # Extract quoted phrases
            phrases = re.findall(r'["\'](.+?)["\']', line)
            forbidden.extend(phrases)
    
    if not forbidden:
        return CheckResult("Forbidden Phrases", "pass", "No forbidden phrases defined")
    
    found = [p for p in forbidden if p.lower() in content.lower()]
    if found:
        return CheckResult("Forbidden Phrases", "fail", f"Found: {', '.join(found)}",
                          f"Remove: {', '.join(found)}")
    return CheckResult("Forbidden Phrases", "pass", f"Checked {len(forbidden)} phrases, none found")

def check_heading_structure(content, standards, content_type):
    """Check heading structure for blog posts."""
    if content_type != "blog":
        return CheckResult("Heading Structure", "pass", "N/A")
    
    h1_count = len(re.findall(r'^#\s+', content, re.MULTILINE))
    h2_count = len(re.findall(r'^##\s+', content, re.MULTILINE))
    
    if h1_count == 0 and h2_count == 0:
        # Might be in frontmatter, check body
        body = content.split("---", 2)[-1] if content.startswith("---") else content
        h1_count = len(re.findall(r'^#\s+', body, re.MULTILINE))
        h2_count = len(re.findall(r'^##\s+', body, re.MULTILINE))
    
    issues = []
    if h1_count == 0:
        issues.append("missing H1")
    if h1_count > 1:
        issues.append(f"{h1_count} H1s (should be 1)")
    if h2_count < 2:
        issues.append(f"only {h2_count} H2s (need at least 2)")
    
    if issues:
        return CheckResult("Heading Structure", "warn", "; ".join(issues))
    return CheckResult("Heading Structure", "pass", f"1 H1, {h2_count} H2s")

def check_image_alt_text(content, standards, content_type):
    """Check that images have alt text."""
    images = re.findall(r'!\[([^\]]*)\]\([^)]+\)', content)
    if not images:
        return CheckResult("Image Alt Text", "pass", "No images found")
    
    missing = sum(1 for alt in images if not alt.strip())
    if missing > 0:
        return CheckResult("Image Alt Text", "warn", f"{missing}/{len(images)} images missing alt text",
                          f"Add alt text to {missing} images")
    return CheckResult("Image Alt Text", "pass", f"All {len(images)} images have alt text")

def check_cta_presence(content, standards, content_type):
    """Check for CTA in blog posts and emails."""
    if content_type not in ("blog", "email"):
        return CheckResult("CTA", "pass", "N/A")
    
    cta_indicators = ["book", "sign up", "get started", "learn more", "contact", "try", "start", "schedule", "demo"]
    has_cta = any(indicator in content.lower() for indicator in cta_indicators)
    
    if has_cta:
        return CheckResult("CTA", "pass", "CTA detected")
    return CheckResult("CTA", "fail", "No CTA found in content",
                      "Add a call-to-action (book a demo, sign up, learn more, etc.)")

def check_internal_links(content, standards, content_type):
    """Check for internal links in blog posts."""
    if content_type != "blog":
        return CheckResult("Internal Links", "pass", "N/A")
    
    # Look for markdown links that aren't external
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    internal = [l for l in links if not l[1].startswith("http") and not l[1].startswith("mailto:")]
    
    if len(internal) >= 2:
        return CheckResult("Internal Links", "pass", f"{len(internal)} internal links")
    elif len(internal) == 1:
        return CheckResult("Internal Links", "warn", "Only 1 internal link (need 2+)",
                          "Add at least 1 more internal link")
    return CheckResult("Internal Links", "warn", "No internal links found",
                      "Add at least 2 internal links to other site content")

def check_email_subject(content, standards, content_type):
    """Check email subject line."""
    if content_type != "email":
        return CheckResult("Subject Line", "pass", "N/A")
    
    # Subject is usually first line or in frontmatter
    subject = ""
    if content.startswith("Subject:") or content.startswith("subject:"):
        subject = content.split("\n")[0].split(":", 1)[1].strip()
    elif content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            fm = content[3:end]
            match = re.search(r'subject:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
            if match:
                subject = match.group(1)
    
    if not subject:
        return CheckResult("Subject Line", "warn", "No subject line detected")
    
    if len(subject) > 50:
        return CheckResult("Subject Line", "warn", f"{len(subject)} chars (recommended <50)")
    return CheckResult("Subject Line", "pass", f"{len(subject)} chars")

def check_ad_naming(content, standards, content_type):
    """Check ad naming conventions."""
    if content_type != "ad":
        return CheckResult("Ad Naming", "pass", "N/A")
    
    ad_section = standards.get("Ad Naming", standards.get("Ads", ""))
    # Look for naming convention pattern
    naming_match = re.search(r'(\w+_\w+_\w+)', ad_section)
    if not naming_match:
        return CheckResult("Ad Naming", "pass", "No naming convention defined")
    
    # Check if content contains a name following the convention
    # This is a simplified check
    return CheckResult("Ad Naming", "pass", "Naming convention defined — verify manually")

# --- Main entry point ---

AUTOMATED_CHECKS = [
    check_word_count,
    check_meta_description,
    check_forbidden_phrases,
    check_heading_structure,
    check_image_alt_text,
    check_cta_presence,
    check_internal_links,
    check_email_subject,
    check_ad_naming,
]

def run_quality_gate(content: str, brand: str, content_type: str, jeff_override: bool = False) -> QualityResult:
    """
    Run automated quality checks on content.
    
    content: The content to check (markdown, email text, ad copy)
    brand: Brand name (e.g., "TrustOffice")
    content_type: "blog", "email", "social", "ad"
    jeff_override: If True, failures are downgraded to warnings
    
    Returns QualityResult with all check results.
    """
    standards = load_standards(brand)
    results = []
    
    if not standards:
        results.append(CheckResult("Standards File", "warn", 
                                   f"No QUALITY-STANDARDS.md found for {brand}",
                                   f"Create Kit/life/brands/{brand}/marketing/QUALITY-STANDARDS.md"))
    else:
        for check_fn in AUTOMATED_CHECKS:
            try:
                result = check_fn(content, standards, content_type)
                if jeff_override and result.status == "fail":
                    result = CheckResult(result.name, "warn", 
                                        f"[OVERRIDE] {result.detail}", result.fix)
                results.append(result)
            except Exception as e:
                results.append(CheckResult(check_fn.__name__, "warn", f"Check error: {e}"))
    
    quality_result = QualityResult(brand, content_type, results)
    
    # Log the result
    log_result(brand, content_type, quality_result)
    
    return quality_result

def log_result(brand: str, content_type: str, result: QualityResult):
    """Log quality gate result for trend analysis."""
    GATE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = GATE_LOG_DIR / f"{brand.lower().replace(' ', '-')}.json"
    
    log_entry = {
        "timestamp": result.timestamp,
        "content_type": content_type,
        "pass_count": sum(1 for r in result.results if r.status == "pass"),
        "warn_count": sum(1 for r in result.results if r.status == "warn"),
        "fail_count": sum(1 for r in result.results if r.status == "fail"),
        "checks": [{"name": r.name, "status": r.status, "detail": r.detail} for r in result.results]
    }
    
    logs = []
    if log_path.exists():
        try:
            logs = json.loads(log_path.read_text())
        except:
            logs = []
    
    logs.append(log_entry)
    # Keep last 100 entries
    logs = logs[-100:]
    log_path.write_text(json.dumps(logs, indent=2))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: marketing_quality_gate.py <content_file> <brand> <content_type> [--override]")
        sys.exit(1)
    
    content = Path(sys.argv[1]).read_text()
    brand = sys.argv[2]
    content_type = sys.argv[3]
    override = "--override" in sys.argv
    
    result = run_quality_gate(content, brand, content_type, jeff_override=override)
    print(result.report())
    sys.exit(1 if result.has_failures() else 0)