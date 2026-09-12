#!/usr/bin/env bash
# =============================================================================
# hindsight-brand-sync.sh — Sync brand MOC files into Hindsight hermes bank
#
# Ingests each brand's INDEX.md + BRAND-STATUS.md into the `hermes` bank (the
# bank auto-recall queries) with source tags so recall results point the agent
# at the correct .md file (e.g. 'source:TrustOffice/INDEX.md').
#
# HASH-AWARE: tracks a manifest of last-ingested content hashes. Files whose
# content hash is unchanged are skipped, so this script is idempotent and can be
# run frequently (launchd WatchPaths event trigger, cron, etc.) without wasting
# LLM tokens re-ingesting untouched files.
#
# DESIGNED FOR --no-agent / script-only cron mode: empty stdout (or the plain
# "Sync complete" summary) = expected output; errors print a clear message and
# exit non-zero.
# =============================================================================

set -uo pipefail

BRANDS_DIR="$HOME/.openclaw/workspace/Kit/life/brands"
HINDSIGHT_URL="http://localhost:9177/v1/default/banks/hermes/memories"
LOG_PREFIX="[hindsight-brand-sync]"
MANIFEST="$HOME/.openclaw/workspace/SYSTEM/state/hindsight-brand-sync-hashes.json"

mkdir -p "$(dirname "$MANIFEST")"

# Brand list as "name:prefix" pairs (name matches dir, prefix = tag prefix)
BRANDS="TrustOffice:trustoffice TrueJoyBirthing:tjb Wingpoint:wingpoint AeriusView:aeriusview TrustMinutes:trustminutes SocializeVideo:socializevideo StenoDesk:stenodesk"

# ---- Init manifest ----
remove_tmp_manifest() { rm -f "$MANIFEST.tmp" "$LOCK_FILE"; }
trap remove_tmp_manifest EXIT

# ---- Concurrency lock (launchd WatchPaths can fire bursts; prevent overlap) ----
LOCK_FILE="$HOME/.openclaw/workspace/SYSTEM/state/hindsight-brand-sync.lock"
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "$LOG_PREFIX SKIP: another sync (pid $LOCK_PID) still running"
        exit 0
    else
        echo "$LOG_PREFIX WARN: stale lock from pid $LOCK_PID — removing and continuing"
        rm -f "$LOCK_FILE"
    fi
fi
echo "$$" > "$LOCK_FILE"

# ---- Check daemon health (bounded) ----
if ! curl -sf --max-time 5 "http://localhost:9177/health" >/dev/null 2>&1; then
    echo "$LOG_PREFIX ERROR: Hindsight daemon not responding on port 9177 — sync aborted"
    exit 1
fi

# ---- Track daily sync runs to avoid redundant backstop work ----
TODAY=$(date +%Y-%m-%d)
LAST_SYNC_FILE="$HOME/.openclaw/workspace/SYSTEM/state/hindsight-brand-sync-lastdate"

# Load manifest into an associative array (skip if already synced today when
# called as a full backstop with no source-change signal)
SUCCESS=0
SKIPPED_UNCHANGED=0
SKIPPED_MISSING=0
FAILED=0
INGESTED_NAMES=()

ingest_file() {
    local BRAND="$1" PREFIX="$2" FILEPATH="$3" FILENAME="$4"
    local RELATIVE_PATH="${BRAND}/${FILENAME}"
    local KEY="${BRAND}/${FILENAME}"

    if [ ! -f "$FILEPATH" ]; then
        echo "$LOG_PREFIX SKIP: $RELATIVE_PATH not found"
        SKIPPED_MISSING=$((SKIPPED_MISSING + 1))
        return 0
    fi

    # Content hash
    local NEW_HASH
    NEW_HASH=$(shasum -a 256 "$FILEPATH" | awk '{print $1}')

    # Compare to manifest (read on demand)
    local OLD_HASH=""
    if [ -f "$MANIFEST" ]; then
        OLD_HASH=$(/usr/bin/python3 -c "
import json,sys
try:
    d=json.load(open('$MANIFEST'))
    print(d.get('$KEY',''))
except Exception:
    print('')
" 2>/dev/null)
    fi

    if [ -n "$OLD_HASH" ] && [ "$OLD_HASH" = "$NEW_HASH" ]; then
        echo "$LOG_PREFIX unchanged: $RELATIVE_PATH (skip)"
        SKIPPED_UNCHANGED=$((SKIPPED_UNCHANGED + 1))
        return 0
    fi

    local FILE_BASE
    FILE_BASE=$(echo "$FILENAME" | sed 's/\.md$//' | tr '[:upper:]' '[:lower:]')
    local DOC_ID="brand-${FILE_BASE}:${PREFIX}"

    if [ "$FILENAME" = "INDEX.md" ]; then
        local TAG_EXTRA="brand-index"
    else
        local TAG_EXTRA="brand-status"
    fi

    # Build JSON payload with Python for reliable escaping
    local PAYLOAD
    PAYLOAD=$(/usr/bin/python3 -c "
import json
with open('$FILEPATH','r') as f:
    content = f.read()
payload = {
    'items': [{
        'content': content,
        'context': 'Brand document: $RELATIVE_PATH',
        'document_id': '$DOC_ID',
        'tags': ['brand-document', 'brand-$PREFIX', 'source:$RELATIVE_PATH', '$TAG_EXTRA'],
        'metadata': {'source_file': '$RELATIVE_PATH', 'brand': '$BRAND', 'file_type': '$FILE_BASE'},
        'timestamp': 'unset',
        'update_mode': 'replace',
    }],
    'async': False,
}
print(json.dumps(payload))
")

    echo -n "$LOG_PREFIX ingesting $RELATIVE_PATH... "
    local RESPONSE
    RESPONSE=$(curl -sf --max-time 120 -X POST "$HINDSIGHT_URL" \
        -H 'Content-Type: application/json' \
        -d "$PAYLOAD" 2>&1) || {
        echo "FAILED (curl error)"
        FAILED=$((FAILED + 1))
        return 1
    }

    local OK_FLAG
    OK_FLAG=$(echo "$RESPONSE" | /usr/bin/python3 -c "import json,sys;print(str(json.load(sys.stdin).get('success',False)).lower())" 2>/dev/null || echo "false")

    if [ "$OK_FLAG" = "true" ]; then
        echo "OK"
        SUCCESS=$((SUCCESS + 1))
        INGESTED_NAMES+=("$KEY")
        # Record the hash in the manifest tmp (accumulate)
        /usr/bin/python3 -c "
import json
p='$MANIFEST'
try:
    d=json.load(open(p))
except Exception:
    d={}
d['$KEY']='$NEW_HASH'
d['last_sync']='$TODAY'
json.dump(d, open(p,'w'), indent=2)
"
    else
        echo "FAILED"
        FAILED=$((FAILED + 1))
    fi
    sleep 1
}

echo "$LOG_PREFIX Starting brand sync into hermes bank..."

for BRAND_PAIR in $BRANDS; do
    BRAND="${BRAND_PAIR%%:*}"
    PREFIX="${BRAND_PAIR##*:}"
    BRAND_PATH="$BRANDS_DIR/$BRAND"

    if [ ! -d "$BRAND_PATH" ]; then
        echo "$LOG_PREFIX SKIP: $BRAND directory not found"
        SKIPPED_MISSING=$((SKIPPED_MISSING + 1))
        continue
    fi

    ingest_file "$BRAND" "$PREFIX" "$BRAND_PATH/INDEX.md" "INDEX.md"
    ingest_file "$BRAND" "$PREFIX" "$BRAND_PATH/BRAND-STATUS.md" "BRAND-STATUS.md"
done

# Stamp last-sync date regardless (so backstop can detect "already ran today")
echo "$TODAY" > "$LAST_SYNC_FILE"

echo "$LOG_PREFIX Sync complete: $SUCCESS ingested, $SKIPPED_UNCHANGED unchanged, $SKIPPED_MISSING missing, $FAILED failed"

# Non-zero exit only if a hard failure occurred
[ "$FAILED" -eq 0 ]
