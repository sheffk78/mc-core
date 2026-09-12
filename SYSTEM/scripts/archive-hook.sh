#!/bin/bash
# archive-hook.sh — Post-archive indexing hook
# Called after files are moved to /Volumes/RENDER DISK/archive/
# Automatically indexes the new folder and appends to LEDGER.jsonl
#
# Usage: archive-hook.sh "/Volumes/RENDER DISK/archive/new-folder-name"
#
# This script is designed to be called by:
# - Kit after archiving files (manual or scripted)
# - Bedrock when it manages archive operations
# - Any archive workflow that moves files to RENDER DISK

set -e

ARCHIVE_ROOT="/Volumes/RENDER DISK/archive"
INDEXER="$HOME/.openclaw/workspace/SYSTEM/scripts/archive-index.py"

if [ $# -lt 1 ]; then
  echo "Usage: archive-hook.sh <folder-path>"
  echo "  folder-path: The archive folder to index"
  exit 1
fi

FOLDER="$1"

# Verify RENDER DISK is mounted
if [ ! -d "$ARCHIVE_ROOT" ]; then
  echo "ERROR: RENDER DISK not mounted at /Volumes/RENDER DISK"
  exit 2
fi

# Verify folder exists
if [ ! -d "$FOLDER" ]; then
  echo "ERROR: Folder not found: $FOLDER"
  exit 1
fi

# Verify it's inside the archive
case "$FOLDER" in
  "$ARCHIVE_ROOT"/*) ;;
  *)
    echo "WARNING: Folder is not inside $ARCHIVE_ROOT"
    echo "         Indexing anyway, but ledger entry may have non-standard path"
    ;;
esac

echo "Post-archive indexing: $FOLDER"
python3 "$INDEXER" "$FOLDER"

echo "Archive hook complete."