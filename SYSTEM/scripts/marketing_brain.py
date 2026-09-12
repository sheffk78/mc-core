#!/usr/bin/env python3
"""
Shared marketing brain helper — load, record insights, and prune brand brains.
Used by all marketing skills to read/write BRAND-BRAIN.md consistently.

Usage:
  from marketing_brain import load_brand_brain, record_insight, prune_brand_brain
  
  brain = load_brand_brain("TrustOffice")
  record_insight("TrustOffice", "winning_patterns", "Hook X got 4.2% CTR", source="competitor-radar")
  prune_brand_brain("TrustOffice")
"""

import os
import re
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE = Path.home() / ".openclaw/workspace"
BRANDS_DIR = WORKSPACE / "Kit/life/brands"
CACHE_DIR = WORKSPACE / "SYSTEM/cache/marketing"

# Discord channel registry
DISCORD_CHANNELS = {
    "True Joy Birthing": "1530040643798438079",  # #truejoybirthing-main
    "TrustOffice": "1479343804527153262",          # #trustoffice-main
    "WingPoint": None,                              # #wingpoint-trust — fill in
    "TrustMinutes": None,                           # #trustminutes — fill in
    "AeriusView": None,                             # #aerius-view — fill in
    "SocializeVideo": None,
    "StenoDesk": None,
}

def get_discord_channel(brand: str):
    """Get Discord channel ID for a brand."""
    return DISCORD_CHANNELS.get(brand)

def get_brain_path(brand: str) -> Path:
    """Get the path to a brand's BRAND-BRAIN.md."""
    return BRANDS_DIR / brand / "marketing/BRAND-BRAIN.md"

def get_standards_path(brand: str) -> Path:
    """Get the path to a brand's QUALITY-STANDARDS.md."""
    return BRANDS_DIR / brand / "marketing/QUALITY-STANDARDS.md"

def load_brand_brain(brand: str):
    """Load brand brain content. Returns None if not found."""
    path = get_brain_path(brand)
    if path.exists():
        return path.read_text()
    return None

def load_brand_brain_sections(brand: str) -> dict:
    """Load brand brain and parse into sections by ## headers."""
    content = load_brand_brain(brand)
    if not content:
        return {}
    
    sections = {}
    current_header = "_header"
    current_lines = []
    
    for line in content.split("\n"):
        if line.startswith("## "):
            if current_header:
                sections[current_header] = "\n".join(current_lines)
            current_header = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    
    if current_header:
        sections[current_header] = "\n".join(current_lines)
    
    return sections

def record_insight(brand: str, category: str, insight: str, source: str = None, confidence: str = "observed_once"):
    """
    Add an entry to the brand brain under the specified category.
    
    Categories: winning_patterns, losing_patterns, customer_language, 
                competitive_context, strategic_notes, channel_performance, recent_insights
    
    Confidence levels: observed_once, confirmed_pattern, jeff_directive
    
    Returns True if successfully recorded, False if brain doesn't exist.
    """
    path = get_brain_path(brand)
    if not path.exists():
        return False
    
    content = path.read_text()
    timestamp = datetime.now().strftime("%Y-%m-%d")
    source_tag = f" (source: {source})" if source else ""
    conf_tag = f" [{confidence}]" if confidence != "observed_once" else ""
    
    # Map category to section header
    section_map = {
        "winning_patterns": "Winning Patterns",
        "losing_patterns": "Losing Patterns",
        "customer_language": "Customer Language",
        "competitive_context": "Competitive Context",
        "strategic_notes": "Strategic Notes",
        "channel_performance": "Channel Performance",
        "recent_insights": "Recent Insights",
    }
    
    section_name = section_map.get(category, category)
    
    # Find the section and insert the entry
    # Look for ### subsection or just append under the section
    pattern = f"## {section_name}"
    if pattern not in content:
        # Add as new section at end
        content += f"\n\n## {section_name}\n- {timestamp}: {insight}{source_tag}{conf_tag}\n"
    else:
        # Insert after the section header, before the next ## 
        lines = content.split("\n")
        insert_idx = None
        for i, line in enumerate(lines):
            if line.strip() == pattern:
                # Find the last entry in this section (before next ## or end)
                insert_idx = i + 1
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith("## "):
                        insert_idx = j
                        break
                    if lines[j].strip().startswith("- "):
                        insert_idx = j + 1
                break
        
        if insert_idx is not None:
            lines.insert(insert_idx, f"- {timestamp}: {insight}{source_tag}{conf_tag}")
            content = "\n".join(lines)
    
    # Update the "Last updated" header
    content = re.sub(
        r"Last updated: \d{4}-\d{2}-\d{2}",
        f"Last updated: {timestamp}",
        content
    )
    
    # Atomic write
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content)
    tmp.rename(path)
    return True

def prune_brand_brain(brand: str) -> dict:
    """
    Prune a brand brain: move insights older than 90 days from Recent Insights 
    to permanent sections. Deduplicate. Return stats.
    """
    path = get_brain_path(brand)
    if not path.exists():
        return {"error": "brain not found"}
    
    content = path.read_text()
    cutoff = datetime.now() - timedelta(days=90)
    
    # Parse recent insights
    lines = content.split("\n")
    moved = 0
    removed = 0
    new_lines = []
    in_recent = False
    entries_to_move = []
    
    for line in lines:
        if line.startswith("## Recent Insights"):
            in_recent = True
            new_lines.append(line)
            continue
        elif line.startswith("## ") and in_recent:
            in_recent = False
            # Process entries to move
            for entry in entries_to_move:
                # Parse the entry to determine target section
                # Entry format: "- 2026-08-10: insight text (source: X) [confidence]"
                moved += 1
            new_lines.extend([])  # Don't add moved entries back
            continue
        
        if in_recent and line.strip().startswith("- "):
            # Check date
            date_match = re.match(r"- (\d{4}-\d{2}-\d{2}):", line)
            if date_match:
                entry_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                if entry_date < cutoff:
                    entries_to_move.append(line)
                    removed += 1
                    continue  # Skip adding to new_lines
        new_lines.append(line)
    
    # Deduplicate: remove consecutive duplicate lines
    deduped = []
    for line in new_lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)
    
    # Write back
    content = "\n".join(deduped)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content)
    tmp.rename(path)
    
    return {"moved": moved, "removed": removed, "deduplicated": len(new_lines) - len(deduped)}

def get_brand_brain_freshness(brand: str) -> dict:
    """Check when each section of the brand brain was last updated."""
    sections = load_brand_brain_sections(brand)
    if not sections:
        return {"exists": False}
    
    # Extract dates from entries
    freshness = {"exists": True}
    for header, content in sections.items():
        dates = re.findall(r"(\d{4}-\d{2}-\d{2})", content)
        if dates:
            latest = max(dates)
            days_ago = (datetime.now() - datetime.strptime(latest, "%Y-%m-%d")).days
            freshness[header] = {"last_entry": latest, "days_ago": days_ago}
        else:
            freshness[header] = {"last_entry": None, "days_ago": None}
    
    return freshness

def list_brands_with_brains() -> list:
    """List all brands that have a BRAND-BRAIN.md."""
    brands = []
    if not BRANDS_DIR.exists():
        return brands
    for brand_dir in BRANDS_DIR.iterdir():
        if brand_dir.is_dir():
            brain = brand_dir / "marketing/BRAND-BRAIN.md"
            if brain.exists():
                brands.append(brand_dir.name)
    return brands

def list_brands_with_configs(config_name: str) -> list:
    """List brands that have a specific marketing config file."""
    brands = []
    if not BRANDS_DIR.exists():
        return brands
    for brand_dir in BRANDS_DIR.iterdir():
        if brand_dir.is_dir():
            config = brand_dir / "marketing" / config_name
            if config.exists():
                brands.append(brand_dir.name)
    return brands

def ensure_cache_dir(skill_name: str) -> Path:
    """Ensure cache directory exists for a skill."""
    cache = CACHE_DIR / skill_name
    cache.mkdir(parents=True, exist_ok=True)
    return cache

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: marketing_brain.py <command> [args]")
        print("Commands: list_brands, freshness <brand>, record <brand> <category> <insight>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "list_brands":
        print("Brands with brains:", list_brands_with_brains())
    elif cmd == "freshness":
        print(get_brand_brain_freshness(sys.argv[2]))
    elif cmd == "record":
        record_insight(sys.argv[2], sys.argv[3], sys.argv[4])
        print("Recorded.")