#!/usr/bin/env python3
"""
Archive Indexer — scans a folder and generates/appends a LEDGER.jsonl entry.
Designed to be run by Bedrock (local model) after archiving files.

Usage:
  python3 archive-index.py /Volumes/RENDER DISK/archive/new-folder-name
  python3 archive-index.py --reindex  # Re-scan all folders and rebuild ledger
  python3 archive-index.py --index /Volumes/RENDER DISK/archive/new-folder

This script:
1. Scans the target folder (file count, types, sizes, dates, key files, READMEs)
2. Sends metadata to Bedrock for description + topic generation
3. Appends the enriched entry to /Volumes/RENDER DISK/archive/LEDGER.jsonl

For --reindex: rebuilds the entire ledger from scratch by scanning all folders.
"""

import json
import os
import re
import sys
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path

LEDGER_PATH = "/Volumes/RENDER DISK/archive/LEDGER.jsonl"
BEDROCK_URL = "http://127.0.0.1:11434/api/generate"
BEDROCK_MODEL = "bedrock:latest"


def scan_folder(folder_path):
    """Scan a folder and return metadata dict."""
    if not os.path.isdir(folder_path):
        print(f"ERROR: {folder_path} is not a directory", file=sys.stderr)
        return None
    
    entry_id = os.path.basename(folder_path)
    file_count = 0
    file_types = set()
    key_files = []
    top_contents = []
    total_size = 0
    earliest = None
    latest = None
    
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            fp = os.path.join(root, f)
            file_count += 1
            ext = os.path.splitext(f)[1].lower().lstrip('.')
            if ext:
                file_types.add(ext)
            rel = os.path.relpath(fp, folder_path)
            depth = rel.count(os.sep)
            if depth <= 1 and ext in ('md', 'txt', 'json', 'py', 'sh', 'yaml', 'yml'):
                key_files.append(rel)
            if depth == 0:
                top_contents.append(f)
            try:
                sz = os.path.getsize(fp)
                total_size += sz
            except:
                pass
            try:
                mtime = os.path.getmtime(fp)
                if earliest is None or mtime < earliest:
                    earliest = mtime
                if latest is None or mtime > latest:
                    latest = mtime
            except:
                pass
        if file_count > 50000:
            break
    
    # Read README
    readme_content = ""
    for kf in key_files[:5]:
        if 'readme' in kf.lower() or kf.lower().endswith('.md'):
            try:
                with open(os.path.join(folder_path, kf), 'r', errors='ignore') as rf:
                    readme_content = rf.read(500)
                break
            except:
                pass
    
    # Determine brand from folder name
    name_lower = entry_id.lower()
    brand = "unknown"
    if 'trustoffice' in name_lower or 'trust' in name_lower:
        brand = "TrustOffice"
    elif 'wingpoint' in name_lower or 'wp-' in name_lower:
        brand = "WingPoint"
    elif 'aeriusview' in name_lower:
        brand = "AeriusView"
    elif 'truejoy' in name_lower or 'tjb' in name_lower or 'city' in name_lower:
        brand = "TrueJoyBirthing"
    elif 'socialize' in name_lower or 'sv-' in name_lower:
        brand = "SocializeVideo"
    elif 'ollama' in name_lower or 'distill' in name_lower or 'abliterated' in name_lower:
        brand = "Infrastructure"
    elif 'home' in name_lower or 'workspace' in name_lower:
        brand = "Workspace"
    elif 'mission' in name_lower or 'plugin' in name_lower:
        brand = "System"
    elif 'qnap' in name_lower:
        brand = "Infrastructure"
    elif 'generate_amended' in name_lower or 'leland' in name_lower:
        brand = "WingPoint"
    
    # Format size
    if total_size > 1e12:
        size_str = f"{total_size/1e12:.1f}TB"
    elif total_size > 1e9:
        size_str = f"{total_size/1e9:.1f}GB"
    elif total_size > 1e6:
        size_str = f"{total_size/1e6:.1f}MB"
    else:
        size_str = f"{total_size/1e3:.1f}KB"
    
    date_earliest = datetime.fromtimestamp(earliest).strftime('%Y-%m-%d') if earliest else None
    date_latest = datetime.fromtimestamp(latest).strftime('%Y-%m-%d') if latest else None
    
    return {
        "id": entry_id,
        "path": folder_path,
        "brand": brand,
        "purpose": "",
        "size_bytes": total_size,
        "size_human": size_str,
        "file_count": file_count,
        "file_types": sorted(list(file_types))[:15],
        "key_files": key_files[:10],
        "top_contents": top_contents[:10],
        "date_earliest": date_earliest,
        "date_latest": date_latest,
        "readme_excerpt": readme_content[:300] if readme_content else None,
        "indexed_at": datetime.now().isoformat()
    }


def enrich_with_bedrock(entry):
    """Use Bedrock to generate description and topics for an entry."""
    context = f"""
Folder: {entry['id']}
Brand: {entry['brand']}
Size: {entry['size_human']}
Files: {entry['file_count']}
File types: {', '.join(entry['file_types'][:10])}
Key files: {', '.join(entry.get('key_files', [])[:8])}
Top contents: {', '.join(entry.get('top_contents', [])[:8])}
Date range: {entry.get('date_earliest', '?')} to {entry.get('date_latest', '?')}
"""
    if entry.get('readme_excerpt'):
        context += f"\nREADME excerpt:\n{entry['readme_excerpt']}\n"
    
    prompt = f"""{context}

Based on the above archive folder information, generate:
1. A concise description (1-2 sentences) of what this archive contains and why it was archived.
2. A list of 3-8 topic keywords for searchability.

Respond as JSON only:
{{"description": "...", "topics": ["topic1", "topic2", ...]}}"""

    try:
        resp = requests.post(BEDROCK_URL, json={
            "model": BEDROCK_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 300}
        }, timeout=180)
        
        if resp.status_code == 200:
            content = resp.json().get('response', '').strip()
            json_match = re.search(r'\{.*?"description".*?"topics".*?\]', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                entry['description'] = parsed.get('description', '')
                entry['topics'] = parsed.get('topics', [])
                return True
    except Exception as ex:
        print(f"  Bedrock enrichment failed: {ex}", file=sys.stderr)
    
    # Fallback: generate from metadata
    entry['description'] = f"{entry['brand']} archive — {entry['file_count']} files, {entry['size_human']}"
    entry['topics'] = [entry['brand'].lower()] if entry['brand'] != 'unknown' else []
    date_match = re.search(r'2026-(\d{2})', entry['id'])
    if date_match:
        entry['topics'].append(f"2026-{date_match.group(1)}")
    return False


def append_to_ledger(entry):
    """Append a single entry to the ledger."""
    with open(LEDGER_PATH, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f"  Appended to ledger: {entry['id']}")


def rebuild_ledger():
    """Re-scan all folders and rebuild the entire ledger."""
    archive_root = os.path.dirname(LEDGER_PATH)
    entries = []
    
    print(f"Rebuilding ledger from {archive_root}...")
    
    for entry_id in sorted(os.listdir(archive_root)):
        full = os.path.join(archive_root, entry_id)
        if not os.path.isdir(full) or entry_id == 'LEDGER.jsonl':
            continue
        
        print(f"  Scanning: {entry_id}...", end=' ')
        entry = scan_folder(full)
        if entry:
            print(f"{entry['size_human']} | {entry['file_count']} files")
            enrich_with_bedrock(entry)
            entries.append(entry)
    
    with open(LEDGER_PATH, 'w') as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    
    print(f"\nLedger rebuilt: {len(entries)} entries")
    return entries


def update_entry(entry_id, new_entry):
    """Update an existing entry in the ledger (by id)."""
    entries = []
    found = False
    
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    e = json.loads(line)
                    if e['id'] == entry_id:
                        entries.append(new_entry)
                        found = True
                    else:
                        entries.append(e)
    
    if not found:
        entries.append(new_entry)
    
    with open(LEDGER_PATH, 'w') as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    
    print(f"  {'Updated' if found else 'Added'} entry: {entry_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Archive Indexer — scan folders and maintain the LEDGER.jsonl",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  archive-index.py "/Volumes/RENDER DISK/archive/new-project-2026-08-27"
  archive-index.py --reindex
  archive-index.py --index "/Volumes/RENDER DISK/archive/some-folder"
        """
    )
    parser.add_argument('path', nargs='?', default=None, help='Folder to index')
    parser.add_argument('--index', dest='index_path', default=None, help='Folder to index (explicit flag)')
    parser.add_argument('--reindex', action='store_true', help='Rebuild entire ledger from scratch')
    parser.add_argument('--no-bedrock', action='store_true', help='Skip Bedrock enrichment (metadata only)')
    
    args = parser.parse_args()
    
    target = args.index_path or args.path
    
    if args.reindex:
        rebuild_ledger()
        return 0
    
    if not target:
        print("No folder path provided. Use --help for usage.", file=sys.stderr)
        return 1
    
    # Resolve path
    target = os.path.abspath(target)
    if not os.path.isdir(target):
        print(f"ERROR: {target} is not a directory", file=sys.stderr)
        return 1
    
    print(f"Indexing: {target}")
    entry = scan_folder(target)
    if not entry:
        return 1
    
    print(f"  {entry['size_human']} | {entry['file_count']} files | {entry['brand']}")
    
    if not args.no_bedrock:
        print("  Enriching with Bedrock...")
        enrich_with_bedrock(entry)
    else:
        entry['description'] = f"{entry['brand']} archive — {entry['file_count']} files, {entry['size_human']}"
        entry['topics'] = [entry['brand'].lower()] if entry['brand'] != 'unknown' else []
    
    update_entry(entry['id'], entry)
    print(f"  Done: {entry['id']}")
    print(f"  Description: {entry.get('description', 'N/A')}")
    print(f"  Topics: {entry.get('topics', [])}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())