#!/bin/bash
# ════════════════════════════════════════════════════════════════════════════
# TJB Pre-Render Gate — Hard enforcement, not suggestions
#
# Run BEFORE every render. Exits non-zero if ANY gate fails.
# Blocks the render command entirely.
#
# Usage:
#   bash scripts/pre-render-gate.sh {slug}       — targeted check for one city
#   bash scripts/pre-render-gate.sh              — full audit (all cities)
#
# Exit codes:
#   0 — All gates passed, render safe to proceed
#   1 — One or more gates failed, do NOT render
# ════════════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTION_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SLUG="${1:-}"
FAILED=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

gate_pass()   { echo -e "  ${GREEN}✅${NC} $1"; }
gate_fail()   { echo -e "  ${RED}❌${NC} $1"; FAILED=1; }
gate_warn()   { echo -e "  ${YELLOW}⚠️${NC} $1"; }
gate_header() { echo ""; echo "─── $1 ───"; }

echo "═══════════════════════════════════════════"
echo "  TJB PRE-RENDER GATE"
echo "  Target: ${SLUG:-ALL CITIES (full audit)}"
echo "  Time:   $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "═══════════════════════════════════════════"

# ── G1: Working directory ──────────────────────────────────────
gate_header "G1: Working Directory"
if [[ "$PWD" == "$REMOTION_DIR" ]]; then
  gate_pass "Working directory: $REMOTION_DIR"
else
  gate_fail "Must be $REMOTION_DIR, got $PWD"
fi

# ── G2: Data validation ────────────────────────────────────────
gate_header "G2: Scene Data Validation"
TSX=$(command -v tsx 2>/dev/null || command -v npx 2>/dev/null)
if [[ -f "$SCRIPT_DIR/validate-data.ts" ]]; then
  # When a target slug is given, validate ONLY that city so a per-city render
  # is never blocked by unrelated cities' pre-existing errors.
  if [[ -n "$SLUG" ]]; then
    if tsx "$SCRIPT_DIR/validate-data.ts" --slug="$SLUG" 2>&1 | sed 's/^/  /'; then
      gate_pass "validate-data.ts exit 0 (scoped to $SLUG)"
    else
      gate_fail "validate-data.ts failed for $SLUG — fix data errors before rendering"
    fi
  else
    if tsx "$SCRIPT_DIR/validate-data.ts" 2>&1 | sed 's/^/  /'; then
      gate_pass "validate-data.ts exit 0"
    else
      gate_fail "validate-data.ts failed — fix data errors before rendering"
    fi
  fi
else
  gate_warn "validate-data.ts not found — skipping G2"
fi

# ── G3: Audio sync validation ──────────────────────────────────
gate_header "G3: Audio Sync Validation"
if [[ -n "$SLUG" ]]; then
  # Map slug to data file and audio dir
  DATA_FILE="$REMOTION_DIR/src/data/${SLUG}-data.ts"
  AUDIO_DIR="$REMOTION_DIR/public/audio/${SLUG}/"
  
  if [[ ! -f "$DATA_FILE" ]]; then
    gate_fail "Data file not found: src/data/${SLUG}-data.ts"
  elif [[ ! -d "$AUDIO_DIR" ]]; then
    gate_fail "Audio directory not found: public/audio/${SLUG}/"
  else
    VALIDATOR_SCRIPT="$REMOTION_DIR/../skills/tjb-video-sync-validator/scripts/validate-sync.py"
    if [[ -f "$VALIDATOR_SCRIPT" ]]; then
      if python3 "$VALIDATOR_SCRIPT" --dir "$AUDIO_DIR" --data "$DATA_FILE" 2>&1 | sed 's/^/  /'; then
        gate_pass "Audio sync: all scenes aligned"
      else
        gate_fail "Audio sync FAILED — fix duration_seconds before rendering"
      fi
    else
      # Fallback: do a basic ffprobe check inline
      echo "  ⏳ Running inline audio check..."
      MASTER="$AUDIO_DIR/${SLUG}-master.wav"
      if [[ ! -f "$MASTER" ]]; then
        MASTER="$AUDIO_DIR/denver-master.wav"
      fi
      if [[ -f "$MASTER" ]]; then
        AUDIO_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MASTER" 2>/dev/null || echo "0")
        SCENE_SUM=$(python3 "$SCRIPT_DIR/sum-scene-durations.py" "$DATA_FILE")
        echo "  Master audio: ${AUDIO_DUR}s  Scene sum: ${SCENE_SUM}s"
        DIFF=$(python3 -c "print(abs(float('${AUDIO_DUR}' or 0) - float('${SCENE_SUM}' or 0)))")
        if python3 -c "exit(0 if ${DIFF} < 2.0 else 1)"; then
          gate_pass "Audio sync: master WAV ${AUDIO_DUR}s ≈ data ${SCENE_SUM}s"
        else
          gate_fail "Audio sync: ${AUDIO_DUR}s audio vs ${SCENE_SUM}s data — drift > 2s"
        fi
      else
        gate_warn "No master WAV found for $SLUG — audio sync cannot be verified"
      fi
    fi
  fi
else
  # Full audit mode: check all cities
  for data_file in "$REMOTION_DIR/src/data/"*-data.ts; do
    base=$(basename "$data_file" -data.ts)
    slug=$(echo "$base" | sed 's/_/-/g')
    audio_dir="$REMOTION_DIR/public/audio/${slug}/"
    if [[ -d "$audio_dir" ]]; then
      master="$audio_dir/${slug}-master.wav"
      [[ ! -f "$master" ]] && master="$audio_dir/denver-master.wav"
      if [[ -f "$master" ]]; then
        adur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$master" 2>/dev/null || echo "0")
        tdata=$(python3 "$SCRIPT_DIR/sum-scene-durations.py" "$data_file")
        if python3 -c "exit(0 if abs(float('${adur:-0}') - float('${tdata:-0}')) < 2.0 else 1)" 2>/dev/null; then
          echo "  ✓ $slug: audio=${adur}s data=${tdata}s"
        else
          gate_fail "$slug: audio=${adur}s vs data=${tdata}s — drift > 2s"
        fi
      fi
    fi
  done
fi

# ── G4: Math.round check ──────────────────────────────────────
gate_header "G4: No Math.round() in Frame Calculations"
MATH_ROUND_LINES=$(grep -n 'Math.round.*duration_seconds' "$REMOTION_DIR/src/Root.tsx" 2>/dev/null || true)
if [[ -z "$MATH_ROUND_LINES" ]]; then
  gate_pass "All compositions use Math.ceil() for frame calculation"
else
  gate_fail "Math.round() found in frame calculations — must use Math.ceil()"
  echo "$MATH_ROUND_LINES" | sed 's/^/  → /'
fi

# ── G5: Audio path consistency ─────────────────────────────────
gate_header "G5: Audio Path Consistency"

if [[ -n "$SLUG" ]]; then
  # Targeted: check a specific composition
  if grep -q "$SLUG" "$REMOTION_DIR/src/Root.tsx" 2>/dev/null; then
    AUDIO_PATH=$(grep -A5 "$SLUG" "$REMOTION_DIR/src/Root.tsx" 2>/dev/null | grep "audioPath" || echo "")
    if echo "$AUDIO_PATH" | grep -q "denver-master"; then
      gate_fail "Audio path for $SLUG still uses 'denver-master.wav' — should be '${SLUG}-master.wav'"
    else
      gate_pass "Audio path for $SLUG looks correct"
    fi
  else
    gate_warn "Composition for $SLUG not found in Root.tsx — may need registration"
  fi
else
  # Full audit: any audioPath using denver-master but NOT under denver-co?
  LEAKS=$(grep "audioPath.*denver-master" "$REMOTION_DIR/src/Root.tsx" | grep -v "denver-co" || true)
  if [[ -z "$LEAKS" ]]; then
    gate_pass "No denver-master.wav leaks in non-Denver compositions"
  else
    gate_fail "Non-Denver compositions using denver-master.wav — will play wrong audio"
    echo "$LEAKS" | sed 's/^/  → /'
  fi
fi

# ── G6: Composition registration check ────────────────────────
gate_header "G6: Composition Registration"
MISSING=0
for data_file in "$REMOTION_DIR/src/data/"*-data.ts; do
  base=$(basename "$data_file" -data.ts)
  [[ "$base" == "types" || "$base" == "denver-example" ]] && continue
  # When a target slug is given, only check that city's composition.
  [[ -n "$SLUG" && "$base" != "$SLUG" ]] && continue
  # Root.tsx imports data files by path: "from './data/tacoma-wa-data'"
  import_path="./data/${base}-data"
  if ! grep -q "$import_path" "$REMOTION_DIR/src/Root.tsx" 2>/dev/null; then
    gate_fail "Data file $base-data.ts has NO matching import in Root.tsx"
    MISSING=1
  fi
done
if [[ "$MISSING" -eq 0 ]]; then
  gate_pass "All data files have matching imports in Root.tsx"
fi

# ── G7: Content accuracy vs cities.ts ─────────────────────────
gate_header "G7: Content Accuracy (Scene Data vs Page Data)"

AUDIT_SCRIPT="$SCRIPT_DIR/audit-video-quality.py"
if [[ -f "$AUDIT_SCRIPT" ]]; then
  if [[ -n "$SLUG" ]]; then
    # Targeted: audit single city
    AUDIT_OUTPUT=$(python3 "$AUDIT_SCRIPT" --slug "$SLUG" 2>&1 || true)
    HIGH_COUNT=$(echo "$AUDIT_OUTPUT" | grep -c '\[high' || true)
    MED_COUNT=$(echo "$AUDIT_OUTPUT" | grep -c '\[medium' || true)
    
    if [[ "$HIGH_COUNT" -eq 0 && "$MED_COUNT" -eq 0 ]]; then
      gate_pass "Content accuracy: no issues for $SLUG"
    elif [[ "$HIGH_COUNT" -gt 0 ]]; then
      gate_fail "Content accuracy: $HIGH_COUNT high-severity issue(s) for $SLUG — fix before rendering"
      echo "$AUDIT_OUTPUT" | grep '\[high' | sed 's/^/  → /'
    else
      gate_warn "Content accuracy: $MED_COUNT medium issue(s) for $SLUG — review before rendering"
      echo "$AUDIT_OUTPUT" | grep '\[medium' | sed 's/^/  → /'
    fi
  else
    # Full audit
    AUDIT_OUTPUT=$(python3 "$AUDIT_SCRIPT" --all 2>&1 | head -10 || true)
    HIGH_TOTAL=$(echo "$AUDIT_OUTPUT" | grep -oE '[0-9]+ high severity' | grep -oE '^[0-9]+' || echo "0")
    if [[ "$HIGH_TOTAL" -eq 0 ]]; then
      gate_pass "Content accuracy: no high-severity issues across all cities"
    else
      gate_fail "Content accuracy: $HIGH_TOTAL high-severity issue(s) across all cities — run audit-video-quality.py --all for details"
    fi
  fi
else
  gate_warn "audit-video-quality.py not found — skipping G7 content accuracy check"
fi

# ── G7b: Screenshot-reality (stale capture / wrong crop / missing photos / drift) ──
gate_header "G7b: Screenshot Reality (video screenshot vs live page)"
if [[ -n "$SLUG" ]]; then
  REALITY_SCRIPT="$SCRIPT_DIR/validate-screenshot-reality.py"
  if [[ -f "$REALITY_SCRIPT" ]]; then
    if python3 "$REALITY_SCRIPT" "$SLUG" > "$SCRIPT_DIR/.g7b-$SLUG.log" 2>&1; then
      gate_pass "Screenshot matches live page (fresh capture, provider crop, photos loaded, providers current)"
    else
      gate_fail "Screenshot does NOT match live page — recapture before rendering (capture-provider-scroll.py $SLUG)"
      grep -E '❌|⚠️' "$SCRIPT_DIR/.g7b-$SLUG.log" | sed 's/^/  → /'
    fi
  else
    gate_warn "validate-screenshot-reality.py not found — skipping G7b screenshot-reality check"
  fi
else
  gate_pass "Screenshot-reality check skipped in full audit mode (per-city only)"
fi

# ── G8: Chapter timestamp sanity ───────────────────────────────
gate_header "G8: Chapter Timestamp Sanity"
if [[ -n "$SLUG" ]]; then
  DATA_FILE="$REMOTION_DIR/src/data/${SLUG}-data.ts"
  if [[ -f "$DATA_FILE" ]]; then
    # Sum all scene durations (exclude video_metadata.duration_seconds)
    TOTAL_SECONDS=$(python3 -c "
import re
content = open('$DATA_FILE').read()
# Scene duration lines come after 'duration_seconds' preceded by whitespace on its own line (scene-level)
# Metadata duration is 'video_metadata' block's duration_seconds; exclude it by only summing
# durations that appear inside scene blocks (scene_id ... duration_seconds ... scene_type).
scenes = re.findall(r'scene_id:.*?duration_seconds:\s*([\d.]+)', content, re.S)
total = sum(float(d) for d in scenes)
print(f'{total:.1f}')
" 2>/dev/null || echo "0")
    
    if python3 -c "exit(0 if float('$TOTAL_SECONDS') > 0 else 1)" 2>/dev/null; then
      MINS=$(python3 -c "m=int(${TOTAL_SECONDS}//60); s=int(${TOTAL_SECONDS}%60); print(f'{m}:{s:02d}')" 2>/dev/null)
      gate_pass "Total duration: ${MINS} (${TOTAL_SECONDS}s) — use this for YouTube description chapters"
    else
      gate_fail "Could not compute total duration from $DATA_FILE"
    fi
  else
    gate_fail "Data file not found: src/data/${SLUG}-data.ts"
  fi
else
  gate_pass "Chapter timestamp check skipped in full audit mode"
fi

# ── Summary ────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
if [ "$FAILED" -eq 0 ]; then
  echo -e "  ${GREEN}ALL GATES PASSED${NC} — render safe to proceed"
  echo "═══════════════════════════════════════════"
  exit 0
else
  echo -e "  ${RED}SOME GATES FAILED — fix before rendering${NC}"
  echo "═══════════════════════════════════════════"
  exit 1
fi