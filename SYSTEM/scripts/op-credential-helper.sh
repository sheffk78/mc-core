#!/usr/bin/env bash
# =============================================================================
# op-credential-helper.sh — 1Password credential retrieval for Hermes Agent
# =============================================================================
# Security model:
#   - Credentials are NEVER printed to stdout (which would appear in chat/logs)
#   - Credentials are written to a temporary file with mode 0600
#   - The temp file path is printed to stdout (safe to display)
#   - Caller MUST delete the temp file after use
#   - All op CLI output goes directly to the file, never to terminal
#
# Usage:
#   ./op-credential-helper.sh <domain-or-url>
#
# Output (to stdout):
#   FOUND <temp_file_path> <item_title>
#   NOT_FOUND
#   ERROR <message>
#
# The temp file contains JSON with username/password fields from 1Password.
# Caller reads the file, injects credentials via computer_use type actions,
# then deletes the file immediately.
#
# Requirements:
#   - op CLI installed and authenticated (service account or interactive)
#   - OP_SERVICE_ACCOUNT_TOKEN env var set (for service accounts)
# =============================================================================

set -euo pipefail

VAULT="${OP_VAULT:-OpenClaw}"
INPUT="${1:-}"

if [ -z "$INPUT" ]; then
    echo "ERROR: No domain or URL provided. Usage: $0 <domain-or-url>"
    exit 1
fi

# Normalize input to a domain for matching
DOMAIN=$(echo "$INPUT" | sed -E 's|https?://||; s|/.*||; s|^www\.||' | tr '[:upper:]' '[:lower:]')

if [ -z "$DOMAIN" ]; then
    echo "ERROR: Could not extract domain from input: $INPUT"
    exit 1
fi

# Create a secure temp file — macOS mktemp needs the XXXXXX at the end without extension
TEMP_FILE=$(mktemp /tmp/op_creds_XXXXXX)
chmod 600 "$TEMP_FILE"

# Trap to clean up temp file on any error
cleanup() { rm -f "$TEMP_FILE"; }
trap cleanup ERR

# Step 1: List ALL credential items. We deliberately do NOT filter by --categories here:
# (a) the op CLI rejects many category names (e.g. API_CREDENTIAL -> "Unknown item category"),
#     and (b) API tokens/keys often have NO url, so they must be matched by title/name instead
#     of by domain. Pull everything and match on BOTH domain and title below.
ITEMS_JSON=$(op item list --vault "$VAULT" --format json 2>/dev/null)

if [ -z "$ITEMS_JSON" ]; then
    echo "ERROR: Failed to retrieve items from 1Password. Is op authenticated?"
    rm -f "$TEMP_FILE"
    trap - ERR
    exit 1
fi

# Step 2: Use Python to find the matching item by domain
# The item list already includes URLs, so no per-item fetching needed
MATCH_RESULT=$(echo "$ITEMS_JSON" | python3 -c "
import sys, json
from urllib.parse import urlparse

domain = '$DOMAIN'
items = json.load(sys.stdin)

def extract_domain(url):
    try:
        parsed = urlparse(url if '://' in url else 'https://' + url)
        return parsed.netloc.lower().replace('www.', '')
    except:
        return ''

def norm(s):
    return (s or '').lower().strip()

needle = domain  # normalized lowercase user input

# ── Collect ALL candidates, then pick the best ──────────────────────────────
# Multiple items can substring-match a brand name (e.g. 'trustoffice' matches a
# LOGIN item, a webhook secret, and stale API credentials). Picking the first
# substring hit returns the wrong secret. Score every candidate:
#   exact title match      = 100
#   exact URL/domain match = 80
#   subdomain URL match    = 70
#   partial URL match      = 50
#   substring title match  = 30
# LOGIN category gets +10 (a real login beats API credentials at equal specificity).
best = None  # (score, id, title)

def consider(score, item):
    global best
    cat_boost = 10 if ((item.get('category') or '').upper() == 'LOGIN') else 0
    cand = (score + cat_boost, item['id'], item['title'])
    if best is None or cand[0] > best[0]:
        best = cand

for item in items:
    urls = [u.get('href', '') for u in item.get('urls', [])]
    if domain and norm(item['title']) == domain:
        consider(100, item)
    for url in urls:
        url_domain = extract_domain(url)
        if not url_domain:
            continue
        if url_domain == domain:
            consider(80, item)
        elif domain.endswith('.' + url_domain) or url_domain.endswith('.' + domain):
            consider(70, item)
        elif domain in url_domain or url_domain in domain:
            consider(50, item)
    if domain and domain in norm(item['title']):
        consider(30, item)

if best:
    print(f'{best[1]}|||{best[2]}')
else:
    print('NOT_FOUND')
" 2>/dev/null)

if [ -z "$MATCH_RESULT" ] || [ "$MATCH_RESULT" = "NOT_FOUND" ]; then
    echo "NOT_FOUND"
    rm -f "$TEMP_FILE"
    trap - ERR
    exit 0
fi

# Parse match result
ITEM_ID=${MATCH_RESULT%%|||*}
ITEM_TITLE=${MATCH_RESULT##*|||}

if [ -z "$ITEM_ID" ]; then
    echo "NOT_FOUND"
    rm -f "$TEMP_FILE"
    trap - ERR
    exit 0
fi

# Step 3: Retrieve the item and extract credential fields in Python (category-agnostic).
# Avoids op --fields quirks: API_CREDENTIAL items have a `credential` field while LOGIN items
# use username/password, so we read the FULL item and pluck whichever of those exist.
# The token/secret goes ONLY into the 0600 temp file - never to stdout.
set +e
op item get "$ITEM_ID" --vault "$VAULT" --format json 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
fields = d.get('fields', [])
by_label = {f.get('label', ''): f.get('value', '') for f in fields}
keep = {}
for lbl in ('username', 'password', 'credential'):
    if lbl in by_label:
        keep[lbl] = by_label[lbl]
if not keep:
    sys.exit(1)
# Prefer the secret-bearing field: credential/password holds the actual token; username may be empty.
for pref in ('credential', 'password', 'username'):
    if pref in keep and keep[pref]:
        chosen = {pref: keep[pref]}
        break
else:
    chosen = keep
print(json.dumps({'label': list(chosen), 'value': next(iter(chosen.values()))}))
" > "$TEMP_FILE"
RC=$?
set -e

if [ $RC -ne 0 ] || [ ! -s "$TEMP_FILE" ]; then
    echo "ERROR: Failed to retrieve credentials for item: $ITEM_TITLE"
    rm -f "$TEMP_FILE"
    trap - ERR
    exit 1
fi

# Disable trap and output the safe result (path only, no secrets)
trap - ERR
echo "FOUND $TEMP_FILE $ITEM_TITLE"