---
name: tjb-city-orchestrator
description: >-
  Single command to build, upgrade, or finish any TJB city page.
  Given a slug, detects current state (new / partially built / deployed
  needs enrichment / deployed needs video / needs outreach / needs SEO),
  then executes the remaining pipeline stages in order with all hard gates.
triggers:
  - work on city
  - build city
  - finish city
  - process city
  - pick up city
---

# TJB City Orchestrator — End-to-End State Machine

**One command:** `work on {slug}` → Kit detects state → executes remaining stages.

## State Detection Algorithm

Run this immediately on a slug to determine what's done and what's not:

```python
# Probe checklist — run in this order, stop at first gap
def probe_city(slug):
    site_root = os.path.expanduser('~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/projects/truejoybirthing-website')
    remotion_root = '/Users/socializerender/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion'
    
    states = {}
    
    # 1. Does the city exist in cities.ts?
    cities_file = f'{site_root}/src/data/cities.ts'
    exists = grep_for_slug(cities_file, slug)
    
    if not exists:
        states['stage'] = 'new'
        return states
    
    # 2. What fields are populated?
    block = get_city_block(cities_file, slug)
    states['has_local_doulas'] = 'localDoulas:' in block
    states['has_hospitals'] = 'hospitalDetails:' in block
    states['has_hero'] = 'heroImage:' in block
    states['has_og'] = 'ogImage:' in block
    states['has_cost_faq'] = 'costLow:' in block and 'costHigh:' in block
    states['has_medicaid'] = 'medicaidNote:' in block
    
    # 3. Provider enrichment state
    provider_count = count_providers(block)
    photo_count = count_provider_photos(block)
    desc_count = count_descriptions(block)
    cost_range_count = count_cost_ranges(block)
    
    states['provider_count'] = provider_count
    states['providers_have_photos'] = photo_count >= provider_count * 0.8  # 80% threshold
    states['providers_have_descriptions'] = desc_count >= provider_count * 0.8
    states['providers_have_cost_ranges'] = cost_range_count >= provider_count * 0.8
    
    # 4. Hospital enrichment
    hospital_count = count_hospitals(block)
    thumbnail_count = count_hospital_thumbnails(block)
    states['hospitals_have_photos'] = thumbnail_count >= hospital_count
    
    # 5. Preflight / deployed
    import subprocess
    preflight = subprocess.run(
        ['npx', 'tsx', 'scripts/preflight.ts', slug],
        capture_output=True, text=True, cwd=site_root
    )
    states['preflight_passes'] = preflight.returncode == 0
    
    # Check live
    live = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
         f'https://truejoybirthing.com/birth-support/{slug}/'],
        capture_output=True, text=True
    )
    states['is_deployed'] = live.stdout.strip() == '200'
    
    # 6. Video state
    states['has_scene_data'] = os.path.exists(f'{remotion_root}/src/data/{slug}-data.ts')
    states['is_registered'] = f'id="{slug}' in open(f'{remotion_root}/src/Root.tsx').read()
    states['has_render'] = bool(glob.glob(f'{remotion_root}/out/*{slug}*city-guide*.mp4'))
    youtube_id_file = f'{remotion_root}/out/{slug}-youtube-id.txt'
    states['has_youtube_id'] = os.path.exists(youtube_id_file)
    
    embed_file = f'{site_root}/src/data/video-embeds.ts'
    states['has_embed'] = slug in open(embed_file).read() if os.path.exists(embed_file) else False
    
    # 7. Outreach state
    # Check mail server (IMAP) for sent messages to providers in this city
    # Check doula-outreach-tracker for records
    tracker_file = f'{site_root}/../Kit/life/brands/TrueJoyBirthing/web-strategy/DOULA-OUTREACH-TRACKER.md'
    if os.path.exists(tracker_file):
        tracker = open(tracker_file).read()
        states['outreach_done'] = slug in tracker and 'sent' in tracker.lower()
    else:
        states['outreach_done'] = False
    
    # Determine stage
    if not states['has_local_doulas']:
        states['stage'] = 'needs_research'
    elif not states['providers_have_photos'] or not states['hospitals_have_photos']:
        states['stage'] = 'needs_enrichment'
    elif not states['has_hero'] or not states['has_og']:
        states['stage'] = 'needs_images'
    elif not states['preflight_passes']:
        states['stage'] = 'needs_preflight'
    elif not states['is_deployed']:
        states['stage'] = 'needs_deploy'
    elif not states['has_render'] or not states['has_youtube_id']:
        states['stage'] = 'needs_video'
    elif not states['has_embed']:
        states['stage'] = 'needs_embed'
    elif not states['outreach_done']:
        states['stage'] = 'needs_outreach'
    else:
        states['stage'] = 'complete'
    
    return states
```

### Stage Determination

| Probe Result | Stage | What To Do |
|---|---|---|
| Slug not in cities.ts | `new` | Full build: research → data entry → images → preflight → deploy → video → embed → outreach |
| No localDoulas | `needs_research` | Research providers, hospitals, birth centers; write data to cities.ts |
| <80% photos/descriptions/cost ranges | `needs_enrichment` | Run provider enrichment pipeline (load tjb-provider-enrichment) |
| No heroImage or ogImage | `needs_images` | Generate hero silhouette + OG image per Pattern B v2 |
| preflight.ts fails | `needs_preflight` | Run `tjb-page-preflight`; fix the returned failures |
| Not live (not 200) | `needs_deploy` | npm build → `bash scripts/deploy.sh {slug}` |
| No rendered video or YouTube ID | `needs_video` | Full video pipeline: scene data → TTS → render → upload → thumbnail |
| No embed | `needs_embed` | Add YouTube embed → deploy |
| No outreach sent | `needs_outreach` | Write + send provider emails |
| All pass | `complete` | Report: nothing to do |

---

## Execution Order (Dependency Graph)

```
needs_research ──→ needs_enrichment ──→ needs_images ──→ needs_preflight ──→ needs_deploy
                      │                                                    │
                      └── needs_images ────────────────────────────────────┘
                                                                           │
                                                                           ▼
                                                                      needs_video ──→ needs_embed ──→ needs_outreach
                                                                                                      │
                                                                                                      ▼
                                                                                                 complete
```

**Hard rule: Never skip a stage.** If `needs_enrichment` but also `needs_images`, do enrichment first — providers need photos before hero image generation.

**Hard rule: One city at a time.** Never start work on a second city while the first has any pending verification, unverified uploads, or pending Jeff review.

---

## Model Routing Per Stage

All stages use the model configuration in `SYSTEM/ROUTER-RULES.md`.

| Stage | Execution | Why |
|---|---|---|
| **State detection** | GLM-5.2 | File ops, curl — no reasoning needed |
| **needs_research** | GLM-5.2 | Web access for provider research |
| → review | GLM-5.2 subagent via delegate_task | Verify accuracy, completeness |
| **needs_enrichment** | Load `tjb-provider-enrichment` skill | Tier 0-1 first (curl+grep), subagent as fallback |
| → review | GLM-5.2 subagent via delegate_task | Verify photos exist, descriptions clean, cost ranges correct |
| **needs_images** | GLM-5.2 | Needs image gen API |
| → review | GLM-5.2 subagent via delegate_task | Verify silhouette pattern, size, quality, and canonical OG filename |
| **needs_preflight** | GLM-5.2 | Script execution |
| → Fix failures | GLM-5.2 subagent via delegate_task | For preflight failures needing reasoning |
| **needs_deploy** | GLM-5.2 | npm build, `bash scripts/deploy.sh {slug}` |
| → Verify live | GLM-5.2 | curl check |
| **needs_video** | Load `tjb-city-video-pipeline` skill | Full video pipeline |
| Scene data creation | GLM-5.2 subagent via delegate_task | Narrative quality, scene structure |
| TTS generation | GLM-5.2 | Needs Mistral API |
| Render | GLM-5.2 | npx remotion render |
| → review | GLM-5.2 subagent via delegate_task | Review stills, check all gates |
| **needs_embed** | GLM-5.2 | File op to video-embeds.ts, deploy |
| **needs_outreach** | Load `tjb-provider-outreach-email` skill | Full outreach pipeline |
| Email writing | GLM-5.2 subagent via delegate_task | Personalization, quality |
| Email review | GLM-5.2 subagent via delegate_task | 8-point quality checklist |
| Sending | GLM-5.2 | Mail server (Postmark outbound relay), from `shelbi@truejoybirthing.com` |

---

## Hard Gates Per Stage

### needs_research → needs_enrichment
- [ ] Providers found: at least 3 for a mid-sized city, 1 for a small city
- [ ] Hospitals identified: at least 1 with L&D services
- [ ] Data written to cities.ts using proper format (never write_file or heredoc — use patch only)
- [ ] GLM-5.2 review: verify data accuracy, no duplicated providers, correct state

### needs_enrichment → needs_images
- [ ] G14: Every provider has `photo:` field (empty string OK, field must exist)
- [ ] G15: Every hospital has `thumbnail:` field
- [ ] Provider photos sourced: at least 1 real headshot (rest can be initials)
- [ ] Provider descriptions: no scraped artifacts (G9 passes)
- [ ] Cost ranges: provider-attributed amounts must be sourced. If unavailable, render only a clearly labeled city-level market range; never attribute it to the provider. "Contact for pricing" is allowed when no provider price is published.
- [ ] Hospital photos: real exterior images (no logos, no AI)
- [ ] Hospital NICUs: not bare claims — have source qualifiers
- [ ] Medicaid note: starts with "Yes —" or "No —" (S7)
- [ ] GLM-5.2 review: everything reviewed before proceeding

### needs_images → needs_preflight
- [ ] G13: Hero image is pregnant mom silhouette, NOT skyline
- [ ] G4: OG image exists ≥30KB, follows the canonical Pattern B (text left + hero silhouette right)
- [ ] OG image uses the canonical filename; no `-v2` suffix
- [ ] Hero image saved to BOTH `public/images/` AND `public/images/heroes/`
- [ ] GLM-5.2 review: visual verification of both images

### needs_preflight → needs_deploy
- [ ] `npx tsx scripts/validate-city-data.ts` exits 0
- [ ] `tjb-page-preflight` S1–S8 ship-blockers all pass
- [ ] FAQ↔data consistency check passes
- [ ] No scraped description artifacts
- [ ] Every provider has a `photo` field
- [ ] Build check: `npm run build` exits 0
- [ ] GLM-5.2 review: comprehensive gap analysis

### needs_deploy → needs_video
- [ ] Live check: curl returns 200
- [ ] OG image loads from live page
- [ ] Hero image loads from live page
- [ ] Visual verification: navigate to live page, use browser_vision
- [ ] No broken images, no "Photo coming soon" placeholders

### needs_video → needs_embed
- [ ] Scene data created with full state names (not abbreviations)
- [ ] Hook narration starts with "Congratulations!" (not "Awesome")
- [ ] All TTS uses same voice (Shelbi/Voxtral, voice ID 331c27cd-...)
- [ ] Pre-render gate: `bash scripts/pre-render-gate.sh {slug}` exits 0
- [ ] Stills captured and visually verified before rendering
- [ ] Render completed: video file exists > 10MB
- [ ] YouTube thumbnail generated: `render-yt-thumbnail.cjs`
- [ ] YouTube upload: public + embeddable=True
- [ ] CITY_META entry exists in upload-youtube.py
- [ ] Post-upload QA: watch video, check provider scroll shows real photos
- [ ] Video has correct provider scroll screenshot (cropped, no menu overlay)

### needs_embed → needs_outreach
- [ ] embed: video-embeds.ts updated
- [ ] deploy: page rebuilt and deployed
- [ ] Verify: curl live page, grep for youtube.com/embed/{video_id}
- [ ] VideoObject schema: `grep -c "duration" dist/birth-support/{slug}/index.html` ≥ 1

### needs_outreach → complete
- [ ] Provider emails found (curl+grep, JSON-LD, domain inference — not paid tools first)
- [ ] Email addresses syntactically verified (email-validator library)
- [ ] Drafts written by GLM-5.2 with personalization
- [ ] 8-point quality checklist passed (GLM-5.2 review)
- [ ] Emails sent via mail server (Postmark outbound relay) from shelbi@truejoybirthing.com
- [ ] Gmail, Google Workspace OAuth, Zapier Gmail, and SMTP are forbidden for TJB provider outreach
- [ ] 15s delays between sends
- [ ] Tracker updated with sends
- [ ] Bounces logged, alternative emails attempted

### complete
|- [ ] City-priority-list.csv updated to Denver-level
|- [ ] CSV status reflects reality; the canonical preflight S1–S8 and pipeline checks are verified
|- [ ] Manual YouTube tasks listed for Jeff (end screen, pinned comment)
|- [ ] **Discord notification sent** via `tjb-page-complete-notify.py` (script fires automatically; non-fatal if webhook not set)

---

## Command Interface

```
work on {slug}              # Full pipeline — detect state, execute remaining stages
work on {slug} from video   # Force start at video pipeline (skip enrichment/images/deploy)
work on {slug} outreach     # Only do outreach — skip everything else
work on {slug} status       # Report stage without executing anything
work on next                # Pick highest priority city from queue, work on it
```

### When Jeff says "work on {slug}"

1. **Detect state** — run probe, determine stage
2. **Report stage** — tell Jeff: "City X is at stage `needs_enrichment`. Will enrich providers, then images, deploy, video, embed, outreach."
3. **Load correct skill** — for each stage, load the appropriate skill first
4. **Execute stages in order** — one stage at a time, hard gates enforced
5. **Report after each stage** — what was done, what gates passed
6. **Final report** — what was done this session, what's left (if any), manual tasks for Jeff

### When Jeff says "work on next"

1. Open `city-priority-list.csv`
2. Filter by `upgrade_status=needs-upgrade`
3. Pick highest ranked (lowest number)
4. Run state detection
5. Proceed as above

---

## Error Handling

| Failure | Action |
|---|---|
| Provider research finds 0 doulas | Flag city as "low provider density" — check nearby cities, consider merging |
| Provider photo can't be found | Leave `photo: ""` — template renders initials. Log for follow-up |
| Hospital photo can't be found | Leave `thumbnail: ""` — template shows placeholder. Log for follow-up |
- Preflight fails | Fix the specific failure returned by `tjb-page-preflight`; never skip gates
| Build fails | Check for untracked `.astro` files, then fix the error. If `npm run build` fails, stop |
- Deploy fails | Stop and use the canonical `bash scripts/deploy.sh {slug}` path; do not invoke Wrangler directly
| Render fails | Check data validation, audio files, composition ID. Stop and report the specific error |
| YouTube upload fails (no CITY_META) | Add CITY_META entry to upload-youtube.py, retry |
| Mail server send bounces | Try alternative email at same domain. If none, flag and move on. Use the mail server (IMAP mail.agentictrust.app:993 / Postmark outbound). See `Kit/life/EMAIL-REFERENCE.md`. |
| GLM-5.2 review fails | Fix the issues identified, re-run review. Do not proceed without passing |

**If a stage blocks**, stop, report the specific failure to Jeff, and do NOT continue to the next stage. Do not "skip and come back."

---

## Post-Completion Report

After all stages complete, produce a report with:

```
## {City} — Complete

### What was done this session
- {Stage 1 description}
- {Stage 2 description}
- ...

### Gates verified
- Canonical preflight S1–S8 and pipeline checks: all pass ✓
- GLM-5.2 review ✓
- Visual verification ✓

### CSV status
- upgrade_status: Denver-level
- video_status: live (public, embeddable)

### Manual tasks for Jeff
1. YouTube Studio → end screen (Subscribe + Playlist + Website)
2. YouTube Studio → pinned comment
```

**After producing the report, fire the Discord notification:**

```bash
python3 ~/.hermes/scripts/tjb-page-complete-notify.py \
  {slug} "{City}" "{State}" complete \
  "https://truejoybirthing.com/birth-support/{slug}/"
```

This posts an embed to `#truejoybirthing-web` with the city name, slug, and a clickable link to the live page. The script is non-fatal — if the webhook URL isn't set yet, it logs a warning and exits 0 so the pipeline never blocks on it.

---

## References

- Load `tjb-city-pipeline` for full build workflow
- Load `tjb-city-video-pipeline` for video production
- Load `tjb-page-preflight` for preflight gates
- Load `tjb-provider-enrichment` for provider enrichment
- Load `tjb-provider-outreach-email` for outreach
- Load `tjb-video-production` for Remotion/TTS pipeline
