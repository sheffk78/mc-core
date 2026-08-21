# TJB Batch Pipeline Redesign v2 — End-to-End Audit & Action Plan

**Created:** June 23, 2026
**Status:** Final — supersedes v1 (`batch-pipeline-redesign.md`)
**Audience:** Pipeline operators, skill maintainers, Hermes agent

---

## Executive Summary

The TJB batch pipeline processes 131 cities through 6 stages: enrichment → images → video → deploy → verify → outreach. Batch 1 (9 cities, `batch-2026-06-23-A`) revealed systemic failures: cities with zero image fields deployed to production, wrong-city image references (Miami → Phoenix), missing thumbnails, and no pre-batch gate. A batch readiness gate was built (`tjb-batch-readiness-gate.py`, D1-D8), and 122 non-batch cities were frozen to `queued`. However, the gate is not yet enforced by any worker script, the queue-init doesn't add batch fields to new cities, and there is no batch lifecycle management tooling. This document defines the complete fix.

---

## Part 1: Structural Changes to Prevent Data Gaps

### 1.1 The Core Problem: Optimistic Flags vs. Verified Data

The pipeline queue tracks `has_hero`, `has_og`, `has_support` as boolean flags, but these are set **optimistically** — they reflect whether the image generation *step ran*, not whether the actual `heroImage:` / `ogImage:` / `supportSceneImage:` fields exist in `cities.ts` or whether the referenced files are valid. This is the root cause of all Batch 1 failures.

**Fix:** The `data_complete` field (already added to the queue) must become the **single source of truth** for pipeline advancement. It is set exclusively by `tjb-batch-readiness-gate.py` and cannot be set by any worker or manual process.

### 1.2 The Five Structural Gaps (Current State)

| # | Gap | Impact | Status |
|---|-----|--------|--------|
| 1 | **No worker enforcement of `data_complete`** | Images/video/deploy workers process any city in their stage regardless of `data_complete` | **NOT IMPLEMENTED** — workers check stage only |
| 2 | **No batch lifecycle management** | No script to compose a batch, activate it, freeze/unfreeze cities, or mark a batch complete | **NOT IMPLEMENTED** |
| 3 | **Queue-init missing batch fields** | New cities added via `tjb-queue-init.py` don't get `data_complete`, `batch_ready`, `batch_id`, `batch_assigned_at` | **NOT IMPLEMENTED** |
| 4 | **No cross-city image reference validation** | Miami pointed to Phoenix's hero/OG; Seattle had stale `-v3` reference. Gate checks file existence but not slug match | **NOT IMPLEMENTED** in gate |
| 5 | **Audit script doesn't report batch status** | `tjb-batch-pipeline-audit.py` has no concept of `data_complete`, `batch_ready`, or `batch_id` | **NOT IMPLEMENTED** |

### 1.3 Required Structural Changes

#### Change 1: Worker-level `data_complete` enforcement (HARD BLOCK)

Every worker script (images, video, deploy) must check `data_complete` before processing a city. If `data_complete: false`, the city is bounced back to `enrichment` with a failure reason.

**Current state of `tjb-images-worker.py` (line 44-48):**
```python
def pick_cities(queue):
    img_cities = [(s, d) for s, d in queue['cities'].items()
                  if d['stage'] == 'images' and d.get('retry_count', 0) < 3]
```

**Required change:**
```python
def pick_cities(queue):
    img_cities = [(s, d) for s, d in queue['cities'].items()
                  if d['stage'] == 'images'
                  and d.get('retry_count', 0) < 3
                  and d.get('data_complete', False)]  # HARD GATE
    # Log any blocked cities
    blocked = [(s, d) for s, d in queue['cities'].items()
               if d['stage'] == 'images' and not d.get('data_complete', False)]
    for slug, d in blocked:
        print(f"  BLOCKED: {slug} has data_complete=false — bounced to enrichment")
        queue['cities'][slug]['stage'] = 'enrichment'
        queue['cities'][slug]['failed_reason'] = 'Blocked by data_complete gate'
```

This same pattern must be added to:
- `tjb-images-worker.py` — check before rendering hero/OG
- Video worker (if it exists as a Python script; the shell worker needs the same check)
- Deploy worker (must not deploy a city with `data_complete: false`)
- Any future workers

#### Change 2: Batch lifecycle management script

A new script `tjb-batch-manager.py` is needed to handle the full batch lifecycle:

```
python3 ~/.hermes/scripts/tjb-batch-manager.py compose --size 10
    → Selects the 10 highest-priority cities with batch_ready=true but batch_id=null
    → Assigns batch_id (format: batch-YYYY-MM-DD-X)
    → Sets batch_assigned_at timestamp
    → Reports the batch composition

python3 ~/.hermes/scripts/tjb-batch-manager.py freeze
    → Sets stage="queued" for all cities with batch_id=null (freezes non-batch cities)

python3 ~/.hermes/scripts/tjb-batch-manager.py status <batch_id>
    → Shows per-city status across all stages for the batch
    → Reports which cities are complete, in-progress, or blocked

python3 ~/.hermes/scripts/tjb-batch-manager.py complete <batch_id>
    → Verifies all cities pass both readiness gate + quality gate
    → If all pass, marks batch as complete
    → Activates next batch (compose + unfreeze)
```

#### Change 3: Queue-init batch fields

`tjb-queue-init.py` line 95-120 creates city entries without the new batch fields. Add:

```python
return {
    'slug': slug,
    'stage': 'enrichment',
    # ... existing fields ...
    # NEW: batch gate fields
    'data_complete': False,
    'data_complete_checked_at': None,
    'data_complete_failures': [],
    'batch_ready': False,
    'batch_id': None,
    'batch_assigned_at': None,
}
```

#### Change 4: Cross-city image reference validation in gate

Add a D9 check to `tjb-batch-readiness-gate.py`:

```python
# ── D9: Image references match city slug ──
hero = extract_field_value(block, 'heroImage')
if hero and slug not in hero:
    # Allow generic hero names but flag cross-city references
    other_slug = re.search(r'/([a-z]+-[a-z]+)-birth-doula', hero)
    if other_slug and other_slug.group(1) != slug:
        errors.append(f"D9: heroImage references another city: {hero} (expected {slug})")

og = extract_field_value(block, 'ogImage')
if og and slug not in og:
    # OG images use full URLs: https://truejoybirthing.com/images/og-city-{slug}.webp
    if 'og-city-' in og:
        ref_slug = re.search(r'og-city-([a-z]+-[a-z]+)', og)
        if ref_slug and ref_slug.group(1) != slug:
            errors.append(f"D9: ogImage references another city: {og}")

support = extract_field_value(block, 'supportSceneImage')
if support and slug.split('-')[0] not in support:
    # Support scenes use city name: {city}-support-scene.webp
    # This is a warning, not a hard error — some cities share support scenes
    warnings.append(f"D9: supportSceneImage may not be city-specific: {support}")
```

Also add stale version detection:
```python
# Check for stale version suffixes (-v3, -v2) that should have been cleaned up
if hero and re.search(r'-v\d+\.webp$', hero):
    warnings.append(f"D9: heroImage has version suffix: {hero} — verify this is current")
```

#### Change 5: Audit script batch awareness

`tjb-batch-pipeline-audit.py` must be updated to:

1. Report `data_complete` status per city (pass/fail/not-checked)
2. Group cities by `batch_id` in addition to stage
3. Show which cities are `batch_ready` but unassigned to a batch
4. Flag cities where `data_complete: false` but `stage` is past `enrichment` (violation)

---

## Part 2: Gate Architecture — Where to Block vs. Warn

### 2.1 Gate Hierarchy

```
┌──────────────────────────────────────────────────────────────────────┐
│                         PIPELINE GATES                                │
│                                                                      │
│  G0 (Pre-batch)     → G1-G22 (Preflight)     → G23 (Post-deploy)     │
│  Readiness Gate        Build-time checks        Quality Gate          │
│  D1-D8 + D9           preflight.ts              tjb-quality-gate.py  │
│  BLOCK = no entry     BLOCK = no deploy          BLOCK = rework       │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 Blocking vs. Warning Matrix

| Gate | Check | Type | Rationale |
|------|-------|------|-----------|
| **D1** | All 16 required city fields present | **BLOCK** | Missing field = broken page |
| **D2** | heroImage file exists ≥10KB | **BLOCK** | No hero = broken page |
| **D2a** | heroImage is silhouette (PIL check) | **BLOCK** | Skyline hero = wrong visual |
| **D3** | ogImage file exists ≥10KB | **BLOCK** | No OG = bad social sharing |
| **D4** | supportSceneImage is city-specific | **BLOCK** | Generic = wrong content |
| **D5** | Provider has all 9 required fields | **BLOCK** | Missing field = broken card |
| **D5w** | Provider photo is empty | **WARN** | No photo is valid (grey initials) |
| **D5w** | Provider description is generic | **BLOCK** | Generic = bad SEO/UX |
| **D6** | Hospital thumbnail field + file exists | **BLOCK** | Missing = "Photo coming soon" |
| **D7** | Birth center thumbnail field + file exists | **BLOCK** | Missing = "Photo coming soon" |
| **D8** | medicaidNote exists | **BLOCK** | Missing = no insurance info |
| **D9** | Image references match city slug | **BLOCK** | Cross-city ref = wrong city's images |
| **D9w** | Image has stale version suffix (-v3) | **WARN** | May be intentional |
| **D9w** | supportSceneImage may not be city-specific | **WARN** | Some cities share scenes |
| **Q1** | Hero silhouette (post-deploy) | **BLOCK** | Defense-in-depth |
| **Q2** | OG image >20KB (post-deploy) | **BLOCK** | Too small = text-only fallback |
| **Q3** | Support scene is city-specific | **BLOCK** | Defense-in-depth |
| **Q4** | Provider descriptions non-generic | **BLOCK** | Defense-in-depth |
| **Q5** | Hospital images are landscape | **WARN** | Square may be logo |
| **Q6** | nearbyCities links return 200 | **BLOCK** | Dead links = bad UX/SEO |
| **Q7** | Birth center thumbnail fields | **BLOCK** | Defense-in-depth |

### 2.3 Gate Timing

| Transition | Gate | Script | Exit 0 = proceed |
|------------|------|--------|------------------|
| enrichment → gpt_review | (none — enrichment worker decides) | — | — |
| gpt_review → data_complete_check | GPT-5.5 5-check review | `tjb-gpt-review-worker.py` | — |
| **data_complete_check → batch_ready** | **G0: D1-D9** | **`tjb-batch-readiness-gate.py`** | **All D1-D8 pass, D9 no blocks** |
| batch_ready → images | Batch assignment | `tjb-batch-manager.py compose` | City assigned to active batch |
| images → video | Image files exist | `tjb-images-worker.py` | hero + OG rendered |
| video → deploy | Video rendered + uploaded | video worker | MP4 exists, YouTube ID present |
| deploy → verify | Build passes + HTTP 200 | `tjb-deploy-worker.py` | `npm run build` exit 0 |
| verify → outreach | G1-G22 preflight + Q1-Q7 quality | `tjb-quality-gate.py` | All BLOCK checks pass |
| outreach → complete | Emails sent | outreach worker | outreach_done = true |

---

## Part 3: The Ideal Batch Workflow (Step by Step)

### Phase 0: Batch Composition

```bash
# 1. Run readiness gate on all queued cities to update data_complete status
python3 ~/.hermes/scripts/tjb-batch-readiness-gate.py --queue

# 2. Compose the next batch — picks top N cities with batch_ready=true, batch_id=null
python3 ~/.hermes/scripts/tjb-batch-manager.py compose --size 10
# Output: batch-2026-06-24-A with 10 cities listed

# 3. Freeze all non-batch cities
python3 ~/.hermes/scripts/tjb-batch-manager.py freeze
# All cities with batch_id=null → stage="queued"
```

### Phase 1: Data Completeness Verification

```bash
# 4. Run readiness gate on the new batch — verify ALL pass before proceeding
python3 ~/.hermes/scripts/tjb-batch-readiness-gate.py --batch batch-2026-06-24-A
# Exit 0 = all pass. Exit 1 = some cities fail — fix before proceeding.

# 5. If any city fails, fix the specific D-code failures:
#    D1 missing field → enrichment fix
#    D2/D3/D4 image issues → image generation
#    D5 provider issues → enrichment fix
#    D6/D7 thumbnail issues → photo sourcing
#    D8 medicaidNote → research
#    D9 cross-city reference → fix cities.ts reference
# After fixing, re-run step 4 until all pass.
```

### Phase 2: Image Generation

```bash
# 6. Move batch cities to images stage
python3 ~/.hermes/scripts/tjb-batch-manager.py activate batch-2026-06-24-A
# Sets stage="images" for all cities in the batch

# 7. Run the images worker (or let cron handle it)
python3 ~/.hermes/scripts/tjb-images-worker.py
# Worker checks data_complete=true for each city before rendering

# 8. After images are done, verify files exist
python3 ~/.hermes/scripts/tjb-batch-readiness-gate.py --batch batch-2026-06-24-A --filter D2,D3,D4
# All should still pass (now files are on disk)
```

### Phase 3: Video Production

```bash
# 9. Cities auto-advance to video stage after images_done
# Run the video worker or handle in-session
python3 ~/.hermes/scripts/tjb-video-worker.py
# Or for in-session: load tjb-city-video-pipeline skill, produce per city

# 10. Verify all videos are done
python3 ~/.hermes/scripts/tjb-batch-manager.py status batch-2026-06-24-A
# Check: all cities show video_done=true
```

### Phase 4: Deploy

```bash
# 11. Build the site
cd ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/projects/truejoybirthing-website
npm run build

# 12. Run preflight on all batch cities
for slug in <batch_cities>; do
    npx tsx scripts/preflight.ts $slug
done

# 13. Deploy
./scripts/deploy.sh
# Or: npx wrangler pages deploy dist

# 14. Verify HTTP 200 on all batch city pages
for slug in <batch_cities>; do
    curl -sL -o /dev/null -w "%{http_code} $slug\n" \
        "https://truejoybirthing.com/birth-support/$slug/"
done
```

### Phase 5: Post-Deploy Verification

```bash
# 15. Run the quality gate on all batch cities
python3 ~/.hermes/scripts/tjb-quality-gate.py --batch batch-2026-06-24-A
# All BLOCK checks must pass. WARN checks are reported but don't block.

# 16. Re-run readiness gate (defense-in-depth)
python3 ~/.hermes/scripts/tjb-batch-readiness-gate.py --batch batch-2026-06-24-A

# 17. Visual spot-check (optional but recommended for first batch of a new pattern)
# Navigate to each city page in browser, verify:
# - Hero renders (not grey box)
# - Provider photos show (not grey initials)
# - Hospital thumbnails show (not "Photo coming soon")
# - Birth center thumbnails show
# - OG image preview is Pattern B (not text-only)
```

### Phase 6: Outreach

```bash
# 18. Send provider outreach emails
python3 ~/.hermes/scripts/tjb-outreach-worker.py
# Or in-session per city using tjb-provider-outreach-email skill

# 19. Mark batch complete
python3 ~/.hermes/scripts/tjb-batch-manager.py complete batch-2026-06-24-A
# Verifies: readiness gate pass + quality gate pass + all cities in outreach/complete stage
# If pass: activates next batch
```

### Batch Workflow Summary Diagram

```
compose → readiness check → [fix failures] → activate → images → video → build → preflight → deploy → HTTP 200 → quality gate → outreach → complete → next batch
                                ↑                                                                ↑
                                └─── FAIL → back to enrichment ───────────────────────────────────┘
```

---

## Part 4: What's Missing from Current Tooling

### 4.1 Scripts That Need to Be Created

| Script | Purpose | Priority |
|--------|---------|----------|
| `tjb-batch-manager.py` | Batch lifecycle: compose, freeze, activate, status, complete | **P0 — blocking** |
| `tjb-batch-remediation-report.py` | Generate categorized report of all missing fields across all 131 cities | P1 |
| `tjb-batch-update-images.py` | Batch update cities.ts with corrected image paths from a JSON report | P1 |
| `tjb-cross-city-image-check.py` | Standalone check for cross-city image references (D9 logic as standalone) | P2 |

### 4.2 Scripts That Need to Be Modified

| Script | Change Required | Priority |
|--------|----------------|----------|
| `tjb-images-worker.py` | Add `data_complete` check in `pick_cities()`. Bounce failures to enrichment. | **P0** |
| `tjb-queue-init.py` | Add 6 batch fields (`data_complete`, `data_complete_checked_at`, `data_complete_failures`, `batch_ready`, `batch_id`, `batch_assigned_at`) to new city entries | **P0** |
| `tjb-batch-readiness-gate.py` | Add D9: cross-city image reference validation + stale version suffix detection | **P0** |
| `tjb-batch-pipeline-audit.py` | Add `data_complete`/`batch_ready`/`batch_id` reporting. Flag stage-`data_complete` violations. | P1 |
| `tjb-quality-gate.py` | Add `--batch <batch_id>` mode (currently only `--all` and single slug) | P1 |
| Video worker (if Python) | Add `data_complete` check | **P0** |
| Deploy worker | Add `data_complete` check before deploying | **P0** |

### 4.3 Skills That Need to Be Updated

| Skill | Change Required | Priority |
|-------|----------------|----------|
| `tjb-city-pipeline/SKILL.md` | Add G0 gate to gate table, add batch lifecycle section, add D9 cross-city reference check | **P0** |
| `tjb-city-orchestrator/SKILL.md` | Add batch readiness gate to routing logic, add batch composition step before "work on next" | **P0** |
| `tjb-page-preflight/SKILL.md` | Reference the pre-batch gate as the first check | P1 |

### 4.4 Tooling Gaps Identified

1. **No batch composition logic** — The system can check if a city is ready, but has no way to select which cities form a batch. Currently this is manual.

2. **No batch freeze/unfreeze automation** — The 122 frozen cities were frozen manually by editing the queue JSON. There's no script to manage this.

3. **No batch completion verification** — No single command to verify that all cities in a batch are truly complete (readiness gate + quality gate + outreach).

4. **No cross-city image integrity check** — The readiness gate checks if image files exist but doesn't verify the image path contains the city slug. This allowed Miami → Phoenix.

5. **No stale version detection** — Seattle had a `-v3` OG reference that was stale. No automated detection for this.

6. **No "diff and verify" after cities.ts edits** — When image paths are added/changed in cities.ts, there's no automated step to re-run the readiness gate on just the changed cities.

7. **No batch-level HTTP 200 check** — The quality gate checks individual cities but doesn't have a batch-level "are all pages live?" command.

8. **No remediation tracking** — For the 122 frozen cities, there's no tracking of which remediation passes (hero images, OG images, thumbnails) have been completed vs. not.

9. **No enrichment → readiness gate handoff** — The enrichment worker sets `enriched_at` and `gpt_reviewed` but doesn't automatically run the readiness gate. A city can sit in `gpt_review` stage with `data_complete: false` indefinitely.

10. **No "queue drift" detection** — Queue has 131 cities, cities.ts has 135. No script reconciles this.

---

## Part 5: Handling the 122 Frozen Cities

### 5.1 Current State of Frozen Cities

All 122 non-batch cities have:
- `stage: "queued"` (frozen)
- `data_complete: false`
- `batch_ready: false`
- `batch_id: null`

Most were previously deployed (they have `deployed_at`, `images_done: true`, `outreach_done: true`) but their data was never verified against the D1-D8 gates.

### 5.2 Remediation Strategy

The 122 cities need to pass through the readiness gate before they can re-enter the pipeline. The remediation follows a prioritized, batch-by-failure-type approach:

#### Step 1: Categorize all failures

```bash
# Run readiness gate on all 122 frozen cities to get current failure state
python3 ~/.hermes/scripts/tjb-batch-readiness-gate.py --queue --json > frozen-city-gate-report.json

# Generate categorized report
python3 ~/.hermes/scripts/tjb-batch-remediation-report.py --input frozen-city-gate-report.json
# Output: per-failure-code city lists
```

#### Step 2: Fix by failure type (not by city)

Fix the highest-volume, highest-impact failure type across all cities first. This allows batch processing with the same tool/prompt per pass.

| Pass | Failure Code | Estimated Cities | Method | Effort |
|------|-------------|-------------------|--------|--------|
| 1 | D1: Missing heroImage/ogImage/supportSceneImage | ~100+ | AI hero generation + Playwright OG render + AI support scene | ~23 hours |
| 2 | D6: Missing hospital thumbnails | ~60 cities, 280 entries | Wikimedia/hospital websites/Street View | ~47 hours |
| 3 | D7: Missing birth center thumbnails | ~30 cities, 68 entries | Birth center websites/email for permission | ~11 hours |
| 4 | D5: Generic provider descriptions | Unknown | Local model rewrite with city-specific context | ~5 hours |
| 5 | D8: Missing medicaidNote | Unknown | State Medicaid policy research | ~3 hours |
| 6 | D9: Cross-city image references | Unknown | Fix cities.ts paths to point to correct city | ~1 hour |

#### Step 3: After each pass, re-run the gate

```bash
# After fixing hero images for all cities in pass 1
python3 ~/.hermes/scripts/tjb-batch-readiness-gate.py --queue --filter D2
# Should show D2 passing for all fixed cities
```

#### Step 4: When a city passes ALL gates, mark it batch_ready

```bash
# The readiness gate automatically sets data_complete=true when D1-D8 pass
# Then check batch_ready = data_complete + enriched_at + gpt_reviewed
python3 ~/.hermes/scripts/tjb-batch-readiness-gate.py --queue
# Cities with data_complete=true AND enriched_at != null AND gpt_reviewed=true
# are now batch_ready=true
```

#### Step 5: Compose future batches from batch_ready pool

```bash
# Once enough cities are batch_ready, compose the next batch
python3 ~/.hermes/scripts/tjb-batch-manager.py compose --size 10
# Picks from the batch_ready pool, assigns batch_id, activates them
```

### 5.3 Special Handling: Already-Deployed Cities

Cities that are already live (deployed_at is set, page returns 200) but fail the readiness gate are in a special state — they're deployed with incomplete data. For these:

1. **Do NOT take them offline** — they're generating traffic. Fix in place.
2. **Prioritize by traffic/visibility** — fix high-traffic cities first.
3. **Fix data in cities.ts, then re-deploy** — the fix is invisible until the next deploy.
4. **Run quality gate after re-deploy** — verify the visual fixes took effect.

### 5.4 Estimated Timeline

| Phase | Cities | Throughput | Duration |
|-------|--------|------------|----------|
| Pass 1: Image fields | 100+ | 10/day | 10 days |
| Pass 2: Hospital thumbnails | 60 | 15/day | 4 days |
| Pass 3: Birth center thumbnails | 30 | 15/day | 2 days |
| Pass 4-6: Provider/medicaid/refs | 50 | 20/day | 2.5 days |
| **Total** | | | **~18-20 days** |

At 10 cities/day with focused work, all 122 frozen cities can reach `batch_ready` in approximately 3 weeks.

---

## Part 6: Implementation Priority Order

### Immediate (P0 — Do Now)

1. **Add `data_complete` check to `tjb-images-worker.py`** — Without this, the gate is advisory, not enforced. Any city in "images" stage still gets processed regardless of data completeness.

2. **Add batch fields to `tjb-queue-init.py`** — New cities entering the queue must have the batch fields initialized.

3. **Add D9 (cross-city image reference check) to `tjb-batch-readiness-gate.py`** — This is the check that would have caught Miami → Phoenix.

4. **Create `tjb-batch-manager.py`** — The batch lifecycle management script (compose, freeze, activate, status, complete).

5. **Add `data_complete` check to deploy worker** — No city should deploy without passing the gate.

### Short-term (P1 — This Week)

6. **Update `tjb-batch-pipeline-audit.py`** — Add batch awareness, data_complete reporting, stage-gate violation detection.

7. **Add `--batch` mode to `tjb-quality-gate.py`** — Allow batch-level quality gate runs.

8. **Create `tjb-batch-remediation-report.py`** — Categorized failure report for the 122 frozen cities.

9. **Update `tjb-city-pipeline/SKILL.md`** — Add G0 gate, batch lifecycle, D9 check.

10. **Update `tjb-city-orchestrator/SKILL.md`** — Add batch composition as the first step.

### Medium-term (P2 — Next Sprint)

11. **Create `tjb-batch-update-images.py`** — Batch cities.ts image path updates from JSON report.

12. **Add queue drift detection** — Reconcile queue count vs. cities.ts count.

13. **Add "diff and verify" hook** — After any cities.ts edit, auto-run readiness gate on changed cities.

14. **Add enrichment → readiness gate handoff** — After enrichment + GPT review, auto-run readiness gate.

---

## Part 7: Queue Schema (Final)

```json
{
  "cities": {
    "example-city-st": {
      "slug": "example-city-st",
      "stage": "queued",

      "enrichment_pass": 1,
      "priority": 50,
      "providers_total": 10,
      "providers_cached": 0,
      "photos_missing": 10,
      "cost_ranges_missing": 10,
      "hospitals_total": 0,
      "thumbnails_missing": 0,
      "has_hero": true,
      "has_og": true,
      "has_support": true,
      "has_video": false,
      "failed_at": null,
      "failed_reason": null,
      "retry_count": 0,
      "last_attempt_at": null,
      "enriched_at": null,
      "images_done": false,
      "video_done": false,
      "deployed_at": null,
      "outreach_done": false,
      "gpt_reviewed": false,

      "data_complete": false,
      "data_complete_checked_at": null,
      "data_complete_failures": [],
      "batch_ready": false,
      "batch_id": null,
      "batch_assigned_at": null
    }
  },
  "stages": ["queued", "enrichment", "gpt_review", "images", "video", "deploy", "verify", "outreach", "complete"],
  "metadata": {
    "version": 2,
    "created_at": "...",
    "last_updated": "...",
    "total_cities": 131,
    "active_batch": "batch-2026-06-23-A",
    "cities_in_progress": 9,
    "cities_complete": 0,
    "cities_frozen": 122
  }
}
```

### Stage Flow (Revised with Batch Gate)

```
                    ┌─────────────────────────────────────────────────┐
                    │                                                 │
queued → enrichment → gpt_review → data_complete_check → batch_ready → [BATCH ASSIGNED] → images → video → deploy → verify → outreach → complete
                                          │                                              │
                                          │ FAIL                                         │
                                          └────→ back to enrichment ────────────────────┘
```

**Key invariants:**
- A city with `data_complete: false` CANNOT be in `images`, `video`, `deploy`, `verify`, or `outreach` stage
- A city with `batch_id: null` and `stage: "queued"` is frozen — no worker processes it
- A city with `batch_id: null` and `stage != "queued"` is a violation (should be queued or in an active batch)
- `batch_ready: true` requires `data_complete: true` AND `enriched_at != null` AND `gpt_reviewed: true`

---

## Part 8: Defense-in-Depth Verification

The pipeline has three layers of verification. Each catches different things:

| Layer | When | Script | Catches |
|-------|------|--------|---------|
| **Pre-batch (G0)** | Before entering pipeline | `tjb-batch-readiness-gate.py` (D1-D9) | Missing fields, missing files, wrong references, generic descriptions, wrong image type |
| **Build-time (G1-G22)** | Before deploy | `preflight.ts` | Build errors, schema issues, missing required props, broken links |
| **Post-deploy (Q1-Q7)** | After deploy, before outreach | `tjb-quality-gate.py` | Hero is silhouette, OG is Pattern B, support scene is city-specific, provider descriptions, hospital images, nearby links, birth center thumbnails |

**No layer is sufficient alone.** The pre-batch gate catches data gaps before they reach production. The build-time gate catches TypeScript/build errors. The post-deploy gate catches visual/content issues that only manifest after rendering.

---

## Summary of Changes from v1

| v1 Proposed | v2 Adds |
|-------------|---------|
| Batch readiness gate (D1-D8) | ✅ Built — add D9 (cross-city reference check) |
| Queue batch fields | ✅ Added — fix queue-init to include them for new cities |
| Worker enforcement | ❌ Not implemented — **P0: add to all workers** |
| Batch lifecycle management | ❌ Not addressed — **P0: create `tjb-batch-manager.py`** |
| Remediation plan for 130 deployed cities | ✅ Covered — refine with failure-type batching for 122 frozen |
| Stage flow revision | ✅ Covered — add `queued` stage, batch assignment step |
| Defense-in-depth (quality gate preserved) | ✅ Covered — formalize as 3-layer verification |
| — | **NEW:** Cross-city image reference validation (D9) |
| — | **NEW:** Stale version suffix detection |
| — | **NEW:** Batch invariants (data_complete stage constraints) |
| — | **NEW:** Audit script batch awareness |
| — | **NEW:** Queue drift detection |
| — | **NEW:** Enrichment → readiness gate handoff |
| — | **NEW:** Detailed implementation priority order |