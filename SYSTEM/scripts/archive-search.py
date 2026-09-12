#!/usr/bin/env python3
"""
Archive Search — query the archive ledger on RENDER DISK.
Designed to be called by Bedrock (local model) or Kit directly.

Usage:
  python3 archive-search.py "wingpoint tax"
  python3 archive-search.py --brand AeriusView
  python3 archive-search.py --brand AeriusView "fake data"
  python3 archive-search.py --date 2026-08
  python3 archive-search.py --list
  python3 archive-search.py --json "query terms"

The ledger lives at /Volumes/RENDER DISK/archive/LEDGER.jsonl
Each line is a JSON object with: id, path, brand, purpose, description, topics,
size_human, file_count, file_types, key_files, date_earliest, date_latest, etc.

Exit codes: 0 = results found, 1 = no results, 2 = ledger missing, 3 = bad args
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path

LEDGER_PATH = "/Volumes/RENDER DISK/archive/LEDGER.jsonl"


def load_ledger():
    """Load all entries from the ledger file."""
    if not os.path.exists(LEDGER_PATH):
        print(f"ERROR: Ledger not found at {LEDGER_PATH}", file=sys.stderr)
        print("The RENDER DISK may not be mounted. Check /Volumes/RENDER DISK/", file=sys.stderr)
        sys.exit(2)
    
    entries = []
    with open(LEDGER_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def search_entries(entries, query=None, brand=None, date=None, file_type=None):
    """Search ledger entries by text query, brand, date prefix, or file type."""
    results = []
    
    query_lower = query.lower().strip() if query else None
    brand_lower = brand.lower() if brand else None
    date_lower = date.lower() if date else None
    ft_lower = file_type.lower() if file_type else None
    
    for e in entries:
        matched = False
        score = 0
        
        # Brand filter (exact match, case-insensitive)
        if brand_lower:
            if e.get('brand', '').lower() != brand_lower:
                continue
        
        # Date filter (prefix match on date_earliest or date_latest)
        if date_lower:
            de = (e.get('date_earliest') or '').lower()
            dl = (e.get('date_latest') or '').lower()
            if not (de.startswith(date_lower) or dl.startswith(date_lower)):
                continue
        
        # File type filter
        if ft_lower:
            if ft_lower not in [ft.lower() for ft in e.get('file_types', [])]:
                continue
        
        # Text query scoring
        if query_lower:
            # Search in description, topics, id, purpose, key_files
            searchable_fields = [
                e.get('id', ''),
                e.get('description', ''),
                e.get('purpose', ''),
                e.get('brand', ''),
                ' '.join(e.get('topics', [])),
                ' '.join(e.get('key_files', [])),
                ' '.join(e.get('top_contents', [])),
                ' '.join(e.get('file_types', [])),
                e.get('readme_excerpt', '') or '',
            ]
            full_text = ' '.join(searchable_fields).lower()
            
            # Score by number of query terms found
            query_terms = query_lower.split()
            for term in query_terms:
                if term in full_text:
                    score += 1
                    matched = True
            
            # Bonus for exact phrase match
            if query_lower in full_text:
                score += 5
            
            # Bonus for topic match
            topics = [t.lower() for t in e.get('topics', [])]
            for term in query_terms:
                if term in topics:
                    score += 3
            
            if not matched and score == 0:
                continue
        else:
            # No query — just filtering by brand/date/filetype
            matched = True
            score = 1
        
        if matched or score > 0:
            results.append((score, e))
    
    # Sort by score descending
    results.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in results]


def format_result(e, verbose=False):
    """Format a single entry for display."""
    lines = [
        f"━━━ {e['id']}",
        f"  Path: {e['path']}",
        f"  Brand: {e.get('brand', 'unknown')}",
        f"  Description: {e.get('description', 'N/A')}",
        f"  Topics: {', '.join(e.get('topics', []))}",
        f"  Size: {e.get('size_human', '?')} | Files: {e.get('file_count', 0)}",
        f"  Date: {e.get('date_earliest', '?')} → {e.get('date_latest', '?')}",
    ]
    if verbose:
        lines.append(f"  File types: {', '.join(e.get('file_types', []))}")
        lines.append(f"  Key files: {', '.join(e.get('key_files', [])[:10])}")
        if e.get('readme_excerpt'):
            lines.append(f"  README excerpt: {e['readme_excerpt'][:200]}...")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Search the archive ledger on RENDER DISK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  archive-search.py "wingpoint tax"
  archive-search.py --brand AeriusView
  archive-search.py --brand TrustOffice --date 2026-08
  archive-search.py --json "aeriusview fake data"
  archive-search.py --list
  archive-search.py --verbose "city videos"
        """
    )
    parser.add_argument('query', nargs='?', default=None, help='Text search query')
    parser.add_argument('--brand', '-b', default=None, help='Filter by brand (TrustOffice, AeriusView, WingPoint, etc.)')
    parser.add_argument('--date', '-d', default=None, help='Filter by date prefix (e.g., 2026-08)')
    parser.add_argument('--filetype', '-f', default=None, help='Filter by file extension (e.g., py, mp4)')
    parser.add_argument('--list', '-l', action='store_true', help='List all archive entries (no search)')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show full details')
    parser.add_argument('--stats', '-s', action='store_true', help='Show archive statistics')
    
    args = parser.parse_args()
    
    entries = load_ledger()
    
    # Stats mode
    if args.stats:
        total_size = sum(e.get('size_bytes', 0) for e in entries)
        brands = {}
        for e in entries:
            b = e.get('brand', 'unknown')
            brands[b] = brands.get(b, 0) + 1
        
        print(f"Archive Statistics")
        print(f"  Total entries: {len(entries)}")
        if total_size > 1e12:
            print(f"  Total size: {total_size/1e12:.1f}TB")
        elif total_size > 1e9:
            print(f"  Total size: {total_size/1e9:.1f}GB")
        print(f"  By brand:")
        for b, c in sorted(brands.items(), key=lambda x: -x[1]):
            print(f"    {b}: {c} entries")
        print(f"  Ledger: {LEDGER_PATH}")
        return 0
    
    # List mode
    if args.list:
        if args.json:
            print(json.dumps(entries, indent=2, ensure_ascii=False))
        else:
            print(f"Archive Ledger — {len(entries)} entries\n")
            for e in entries:
                print(format_result(e, verbose=args.verbose))
                print()
        return 0
    
    # Search mode
    if not args.query and not args.brand and not args.date and not args.filetype:
        print("No search criteria provided. Use --help for usage.", file=sys.stderr)
        return 3
    
    results = search_entries(entries, query=args.query, brand=args.brand, date=args.date, file_type=args.filetype)
    
    if not results:
        print("No matching archive entries found.")
        return 1
    
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(f"Found {len(results)} matching archive entr{'y' if len(results)==1 else 'ies'}:\n")
        for e in results:
            print(format_result(e, verbose=args.verbose))
            print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())