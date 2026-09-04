# Integrated City Video Pipeline — TJB

*Created: June 10, 2026*
*Purpose: Merge the city page build (Steps 1-7) with the YouTube city video production (Phase 2) into one seamless, Kit-executable pipeline.*

---

## Pipeline Overview

```
Phase 1: City Page Build (Steps 1-7)
  Queue → Research + Outreach → Write → Images → Build/Validate → Preflight → Deploy

Phase 2: City Video Production (Steps 8-20)
  Prerequisites → Scene Data → Assets → TTS → Durations → Master WAV → Sync Validate →
  Still Approval → Render → Thumbnail → YouTube Upload → Embed → Re-Deploy
```

---

# Phase 1: City Page Build

**Brief reference.** Full details in `tjb-city-pipeline` skill. Run these gates before Phase 2:

| Gate | What Passes | 
|------|-------------|
| G1-G7 | All 7 pipeline gates pass (structural + content depth) |
| G8 | Video embedded on city page or deferred with documented `video_status=deferred` in `city-priority-list.csv` |
| Page live | `curl -s -o /dev/null -w "%{http_code}" https://truejoybirthing.com/birth-support/{slug}/` returns 200 |
| Outreach | Listing notification emails queued/sent for all found providers |
| Trackers | Provider rows added to Google Sheet |

**🚫 Phase 2 must NOT start until ALL Phase 1 gates pass.** The video is an enhancement layer. It does NOT replace or shortcut any Phase 1 step.

**G8 is the completion gate for the full pipeline.** A city is not fully done until the video is embedded on the page OR explicitly deferred with a reason in the CSV. After Phase 2 completes, the `video_status` field in `city-priority-list.csv` (column 14) should be updated to `live`.

## Video Backlog — Priority Rule

When multiple cities are pending video production, process them in the **same priority order as the city build queue** — highest-ranked cities first. This means:

1. Sort `video_status=pending` cities by CSV `rank` (column 1, lowest = highest priority)
2. Process one per day (YouTube 1/day rule)
3. If a `pending` city fails prerequisites (city data too thin), set it to `deferred` and move to the next

The daily cron at 7:15 AM MT (`TJB Video Backlog Check`) surfaces all pending cities to Discord automatically.

---

# Phase 2: City Video Production

## Step 8 — Prerequisites Check

Before starting video production, verify:

- [ ] Shelbi voice ID confirmed: `331c27cd-1809-43c2-853d-4c167f184670`
- [ ] Remotion project exists at `Kit/life/brands/TrueJoyBirthing/video/remotion/`
- [ ] YouTube channel phone-verified at `https://www.youtube.com/verify` (one-time)
- [ ] YouTube OAuth token valid: `remotion/.youtube-oauth/token.json` exists
- [ ] MISTRAL_API_KEY set and valid
- [ ] City has ≥2 hospitals (video needs minimum content — skip if only 1 hospital with skeleton data)
- [ ] City has ≥1 provider with photo (provider grid needs at least 2 provider entries to look good — skip if 0 providers)
- [ ] City data has `costLow`, `costHigh`, `medicaidNote`
- [ ] Keyword-first title stays under 70 characters (count letters + spaces — it's for the YouTube title and the HTML <title>)
- [ ] Previously deployed city videos: ≤1 per day (YouTube algorithm spam rule) — check `video_status` in `city-priority-list.csv`

**If any check fails or the city data is too thin:** Set `video_status=deferred` in `city-priority-list.csv` with the reason, and move on.

---

## Step 9 — Create Scene Data File

### 9a. Create Scene Data Manually

**⚠️ `scripts/extract-city-video.py` does not yet exist.** Do not run it — it will fail. Scene data files must be created manually until this script is built.

**Reference:** Copy `remotion/src/data/denver-example.ts` as the template. It has all scene types including `tjb_city_hook`, `tjb_city_bridge`, `tjb_hospital_card`, `tjb_provider_grid`, `tjb_provider_portrait`, `tjb_app_feature`, `tjb_cost_reveal`, `tjb_insurance_branch`, `tjb_city_cta`.

**Manual creation workflow:**

1. Copy `src/data/denver-example.ts` → `src/data/{slug}-data.ts`
2. Replace city references (Denver → {City}, denver-co → {slug}, CO → {stateAbbr}, Colorado → {State})
3. Set hospital data: pull `hospitalDetails[]` from `cities.ts` and populate 1-3 hospital card scenes (max 3)
4. Set cost data: `costLow`, `costHigh` from `cities.ts`
5. Set medicaidNote: use `medicaidNote` from `cities.ts` to pick Branch A (covers) or Branch B (no coverage)
6. Use the approved narration templates below — do NOT rewrite from scratch
7. Set initial `duration_seconds` to the target durations in 9d (will be tuned after TTS)
8. Set `image_source` paths to the correct slug-prefixed image files

### 9b. Register in Root.tsx

Open `remotion/src/Root.tsx`. Add a new composition:

```typescript
<Composition
  id="{slug}-City-Guide"
  component={TJBCityVideo}
  durationInFrames={Math.ceil(totalDuration * 30)}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{
    data: {slug}Data,
    audioPath: `audio/${slug}/master.wav`,
  }}
/>
```

Import the data file at the top of Root.tsx:

```typescript
import { {slug}Data } from './data/{slug}-data';
```

### 9c. Approved Narration Templates (Mandatory)

These are locked. Do NOT rewrite from scratch. Replace `{City}`, `{State}`, `{slug}`, `{stateAbbr}` from cities.ts.

| Scene | Template |
|-------|----------|
| **Hook** | `"Just found out you're pregnant in {City}? Congratulations! Now you've got eighty tabs open on hospitals, doulas, midwives, insurance. Let's close every single one of them right now."` |
| **Bridge/Overview** | `"Here's what we're covering in this video: which hospitals welcome doulas and midwives, the doulas and midwives you can work with in {City}, what everything costs including midwifery care, how {State} Medicaid can help, and a free app that builds your birth plan step by step. Let's start with where you can deliver."` |
| **Hospital Card** | `"First up, {HospitalName}. This is where many {City} families deliver. {NICU/info/description}. {Additional context}. They {doula policy}."` (1-2 sentences per hospital, max 3) |
| **Provider Grid** | `"{City} has {N} doulas and midwives — birth doulas, postpartum specialists, lactation support, overnight care."` (Shows ALL provider photos in a grid sweep. No names, no details — just faces. {N} = providerCount.) |
| **Provider Named** | (Only after opt-in) `"{Name} is a {credential} at {Practice}. They support families in {City} with {services}. {Personal detail}.` (Uses ProviderPortraitSlide with photo + name + cost range + service tags.) |
| **App Feature** | `"Here's the part every midwife should know about. The True Joy Birthing app is completely free — no account, no catch. Nine guided sections walk you through your entire birth plan. You can find and message doulas and midwives near you right inside the app. Then export your plan as a PDF to share with your provider. It's the tool every {City} mom needs in her pocket."` |
| **Cost Reveal** | `"Let's talk money. Hiring a doula in {City} typically costs between ${costLow} and ${costHigh}. Midwifery care runs $5,000 to $8,000 for a full birth. Many private insurance plans cover midwives, and more doulas now offer payment plans. Here's where it gets better — {State} Medicaid {covers/does not cover} doula care."` (MUST mention both doula AND midwife ranges) |
| **Insurance — Branch A (covers)** | `"Great news: {State} Medicaid covers doula care. That means if you're on Medicaid, your doula may be covered. Midwives — both CNMs and certain CPMs — are also covered in many plans. Check with your provider and your doula or midwife to make sure."` |
| **Insurance — Branch B (no coverage)** | `"{State} Medicaid doesn't currently cover doula care. But don't let that stop you. Many doulas offer sliding scale fees and payment plans, and some private insurance plans now include doula benefits. It's always worth asking."` (MUST include both doula AND midwife coverage info) |
| **CTA** | Start with WHY: `"Your birth plan is one of the most important tools you'll have. It tells your care team exactly what matters to you — who you want in the room, how you want to manage pain, what happens after delivery. You can build yours with the free PDF birth plan, watch our walkthrough series, or use the mobile app. The True Joy Birthing app is free — download it from the App Store or Google Play. And if you're in {City}, visit our {City} page for the full list of providers and resources. Link in the description."` |

### 9d. Scene Arc Structure

| # | Scene Type | Component | Duration Target |
|---|-----------|-----------|-----------------|
| 1 | `tjb_city_hook` | CityHookSlide | 10-12s |
| 2 | `tjb_city_bridge` | CityBridgeSlide (⚠️ MANDATORY) | 14-18s |
| 3 | `tjb_hospital_card` | HospitalCardSlide | 10-15s each (max 3) |
| 4a | `tjb_provider_grid` | ProviderGridSlide | 5-6s |
| 4b | `tjb_provider_portrait` | ProviderPortraitSlide (named, opt-in only) | 10-15s each (max 2-3) |
| 5 | `tjb_app_feature` | AppFeatureSlide | 18-24s |
| 6 | `tjb_cost_reveal` | CostRevealSlide | 18-22s |
| 7 | `tjb_insurance_branch` | InsuranceBranchSlide (A or B) | 20-28s |
| 8 | `tjb_city_cta` | CityCTASlide | 18-23s |

**Target total:** 2:30–4:00. Hard cap 5:00.

---

## Step 10 — Copy Image Assets

```bash
cd ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/projects/truejoybirthing-website

# City hero silhouette
cp public/images/{slug}-birth-doula-skyline.webp \
  ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/public/images/

# Hospital photos
for hospital in {list-hospital-slugs}; do
  cp public/images/{slug}-${hospital}.webp \
    ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/public/images/
done

# Provider photos  
if [ -d public/images/doulas/ ]; then
  cp public/images/doulas/*.webp \
    ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/public/images/doulas/
fi

# App screenshots (required for AppFeatureSlide)
cp public/images/tjb-app-dashboard.png \
  ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/public/images/
cp public/images/tjb-app-birth-plan-builder.png \
  ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/public/images/

# CTA assets (PDF mockup, store badges)
cp public/images/birth-plan-mockup-square-pdf-3.webp \
  ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/public/images/
cp public/images/app-store-badge.png \
  ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/public/images/
cp public/images/google-play-badge.png \
  ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/public/images/

# Logos
cp public/images/logo.svg \
  ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/public/images/
cp public/images/logo-white.svg \
  ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/public/images/
```

**Verify every image file exists** at the destination before proceeding. Missing images cause Remotion render cancellations.

---

## Step 11 — Generate TTS (Voxtral)

### 11a. Generate Per-Scene WAVs

```bash
cd ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion
mkdir -p public/audio/{slug}/
```

For each scene, call the Voxtral API:

```python
import requests
voice_id = "331c27cd-1809-43c2-853d-4c167f184670"

resp = requests.post(
    "https://api.mistral.ai/v1/audio/speech",
    headers={
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "voxtral-mini-tts-latest",
        "input": scene["narration"],
        "voice_id": voice_id,
        "response_format": "wav"
    },
    timeout=60
)

with open(f"public/audio/{slug}/scene-{idx:02d}.wav", "wb") as f:
    f.write(resp.content)
```

### 11b. Convert to 48kHz Stereo + Normalize

```bash
for wav in public/audio/{slug}/scene-*.wav; do
  base=$(basename "$wav" .wav)
  ffmpeg -y -i "$wav" \
    -af "loudnorm=I=-16:LRA=11:TP=-1.5" \
    -ac 2 -ar 48000 \
    "public/audio/{slug}/${base}-norm.wav"
  mv "public/audio/{slug}/${base}-norm.wav" "$wav"
done
```

### 11c. Measure Actual Duration

```bash
for wav in public/audio/{slug}/scene-*.wav; do
  ffprobe -v error -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 "$wav"
done
```

---

## Step 12 — Set Frame-Precise Durations

**CRITICAL — The #1 failure point.** After TTS generation, the actual audio duration almost never matches the estimated `duration_seconds`. Update the data file.

For each scene, compute:

```python
import math
fps = 30
duration_seconds = math.ceil(audio_duration * fps) / fps
```

Update `{slug}-data.ts` with the exact durations. Every scene must use `Math.ceil()`:

```typescript
duration_seconds: 9.20,  // math.ceil(audio_dur * 30) / 30
```

**Duration verification table** (record after update):

| Scene | Audio | Data | Drift |
|-------|-------|------|-------|
| 01_hook | X.XXs | X.XXs | <0.04s ✓ |
| ... | | | |

Drift must be < 0.04s per scene (≤1 frame at 30fps).

---

## Step 13 — Rebuild Master WAV

### 13a. Pad Each Scene Individually

```bash
cd public/audio/{slug}/

for scene in 01 02 03 04 05 06 07 08; do
  audio_dur=$(ffprobe -v error -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 scene-${scene}.wav)
  data_dur=$(python3 -c "
import re
data=open('../../src/data/{slug}-data.ts').read()
# Find the duration for scene-${scene}
import json
print('TODO: parse from JS object')
")
  # Pad to match data_dur exactly
  ffmpeg -y -i scene-${scene}.wav \
    -af "apad=pad_dur=$(python3 -c "print(${data_dur} - ${audio_dur})")" \
    -t ${data_dur} -ac 2 -ar 48000 \
    scene-${scene}-padded.wav
done
```

### 13b. Concatenate All Padded WAVs

```bash
rm -f concat_list.txt
for f in scene-01-padded.wav scene-02-padded.wav scene-03-padded.wav \
         scene-04-padded.wav scene-05-padded.wav scene-06-padded.wav \
         scene-07-padded.wav scene-08-padded.wav; do
  echo "file '$PWD/$f'" >> concat_list.txt
done

ffmpeg -y -f concat -safe 0 -i concat_list.txt -c copy master.wav
```

### 13c. Verify Total Duration

```bash
master_dur=$(ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 master.wav)
echo "Master WAV: ${master_dur}s"

# Sum all data durations
python3 -c "
import math
durations = [9.20, 17.43, 14.63, 12.17, 16.00, 24.00, 18.17, 21.77]  # from data file
total = sum(durations)
print(f'Data total: {total}s')
print(f'Diff: {abs(${master_dur} - total):.3f}s')
"
```

**Master WAV must be within 0.5s of total data duration.** If the gap is larger, one or more scene pads are wrong — fix before proceeding.

---

## Step 14 — Run Sync Validation

**🚫 DO NOT SKIP. 🚫 DO NOT RENDER WITHOUT THIS PASSING.**

```bash
cd ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion

# Move binary aside for CLI to work
mv src/index.ts src/index.ts.bak

python3 validate_sync.py --slug {slug}

# Restore binary
mv src/index.ts.bak src/index.ts
```

Where `validate_sync.py` checks every scene's audio duration against its `duration_seconds` in the data file.

**Expected output:**
```
  01_hook              audio= 9.20s  data= 9.20  ✓
  02_overview          audio=17.42s  data=17.43  ✓
  ...
  TOTAL: audio=198.06s  video=198.27s  0.22s drift
  ✅ ALL SCENES LINE UP
```

**If any scene says ❌ or WORDS CUT OFF:**
1. Update `duration_seconds` in the data file to `math.ceil(audio_dur * 30) / 30`
2. Rebuild master WAV (Step 13)
3. Re-run validation

---

## Step 15 — Capture Stills for Jeff Approval

**🚫 NEVER RENDER the full video before Jeff approves the slides.** Iteration on stills costs 3 seconds. Full render costs 5-10 minutes.

### 15a. Capture Key Slides

```bash
cd ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion

mv src/index.ts src/index.ts.bak

# AppFeatureSlide at frame 90 (all text animated)
npx remotion still {slug}-City-Guide \
  out/stills/app-slide-{slug}.png --frame=90 --log=error

# CostRevealSlide at midpoint
npx remotion still {slug}-City-Guide \
  out/stills/cost-slide-{slug}.png --frame=420 --log=error

# CTASlide at midpoint
npx remotion still {slug}-City-Guide \
  out/stills/cta-slide-{slug}.png --frame=600 --log=error

mv src/index.ts.bak src/index.ts
```

### 15b. Pre-Ship QA Checklist (Before Sending to Jeff)

Run through EVERY item:

1. [ ] Audio stream exists in master WAV (`ffprobe` shows AAC, stereo, 48kHz)
2. [ ] Provider `isVerified` values match actual `cities.ts` data — NOT hardcoded `true`
3. [ ] App screenshot is a REAL app screenshot, not placeholder/AI-generated phone frame
4. [ ] CTA slide has real mockups (PDF booklet, iPhone app, video thumb) — NOT emoji icons
5. [ ] Audio sync verified: master WAV duration ≈ total scene durations (within 0.5s)
6. [ ] Colors match website palette: LAVENDER=#6E6C99, CHARCOAL=#2A2A2A, font=Cormorant Garamond/Source Sans 3
7. [ ] App feature slide matches website layout: two staggered phone mockups left, eyebrow+headline+bullets+badges right
8. [ ] CTA slide has LIGHT BG (cream #FAF8F5), no "coming soon" text on Google Play, App Store + Google Play badges present
9. [ ] No TrustOffice chrome: no top accent bar, no corner brackets, no T-icon logo, no footer divider, no footer text block
10. [ ] Bridge/Overview scene present (⚠️ mandatory, not optional)
11. [ ] Both doula AND midwife mentioned in app scene narration
12. [ ] Both doula AND midwife cost ranges in Cost Reveal scene
13. [ ] Provider grid slide shows all providers as photo grid with sweep animation (no named portraits unless opted in)
14. [ ] Hook includes "doulas, midwives, insurance" (all three)
15. [ ] All image files exist in `public/images/` — verify with `ls -la`
16. [ ] Phone frame dimensions: 300×650px, second phone offset top:63 left:188
17. [ ] Audio narration mentions midwives alongside doulas in insurance scene

### 15c. Send Stills + QA Results to Jeff

Send the PNG stills and the QA checklist results. Ask for approval before proceeding.

**Do NOT proceed to Step 16 until Jeff explicitly approves the visuals.**

---

## Step 16 — Render Full Video

After Jeff approves the stills:

```bash
cd ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion

mv src/index.ts src/index.ts.bak

npx remotion render {slug}-City-Guide \
  out/{slug}-city-guide.mp4

mv src/index.ts.bak src/index.ts
```

Render time: ~5-10 minutes for a 3:30 video. Output at out/{slug}-city-guide.mp4.

**If sending to Jeff before YouTube upload** (e.g., for final approval):
```bash
# H.264 compression for Discord (under 8MB)
ffmpeg -y -i out/{slug}-city-guide.mp4 \
  -c:v libx264 -preset medium -crf 28 \
  -c:a aac -b:a 96k \
  out/{slug}-city-guide-compressed.mp4

ls -la out/{slug}-city-guide-compressed.mp4  # Target < 8MB
```

---

## Step 17 — Generate YouTube Thumbnail

Use the city hero silhouette image — the SAME image used on the city page and as the OG image right panel. Zero drift between these three uses is a hard rule.

```bash
cd ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/projects/truejoybirthing-website

node scripts/render-yt-thumbnail.cjs {slug} "{City}" "{ST}"
# Output: public/images/yt-thumb-{slug}.png + .webp (1280×720)
```

**Thumbnail design (locked):**
- City hero silhouette full-bleed background
- Left-side lavender gradient overlay (70% → transparent) for legibility
- 5px rose accent bar across top
- City badge pill (small translucent) in top-left
- Headline in dark blur box (60% black, backdrop blur) — guarantees readability at mobile thumbnail size
- Subtitle in Source Sans 3 inside same box
- Play indicator circle bottom-right
- True Joy Birthing heart icon + text bottom-left

**Verify thumbnail:**
```bash
ls -la public/images/yt-thumb-{slug}.png  # Should be 1280×720
identify public/images/yt-thumb-{slug}.png
```

**Copy to Remotion out/ for upload:**
```bash
cp public/images/yt-thumb-{slug}.png \
  ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion/out/
```

---

## Step 18 — Upload to YouTube

**One command:**
```bash
cd ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/video/remotion

mv src/index.ts src/index.ts.bak

python3 scripts/upload-youtube.py {slug}

mv src/index.ts.bak src/index.ts
```

### Screenshot-reality hardening (2026-09-04, after HB + Rancho incidents)

Two videos shipped with provider scenes showing the wrong part of the page / initials
placeholders because the scroll screenshot was stale. Root cause: nothing verified the
screenshot against the live page. Hardened pipeline:

1. **capture-provider-scroll.py** now (a) fails hard if ANY provider photo has
   naturalWidth=0 at capture time (initials-placeholder risk), (b) writes
   `public/images/{slug}-capture-manifest.json` — capture timestamp, live URL, crop
   bounds, section label, per-photo load status + src.
2. **validate-screenshot-reality.py** (G7b in pre-render-gate.sh, per-city, hard gate)
   checks: manifest exists; capture is NEWER than the last cities.ts/public/images
   commit; crop didn't start at page top; all provider photos loaded + files aren't
   initials placeholders (<3KB); manifest photo files == cities.ts localDoulas photo
   paths; data-file providerCount == cities.ts count.
3. **upload-youtube.py** now records the previous live videoId (video-embeds.ts + id
   file) pre-upload, then post-upload: (a) auto-swaps videoId in the website's
   video-embeds.ts, (b) auto-unlists every old public video for that city.

Rule: any content change on a city page (providers, photos, layout) requires
re-capture + re-render of that city's video. The gate now enforces it.

### What upload-youtube.py does:
1. Uploads `out/{slug}-city-guide.mp4` with optimized metadata
2. Sets custom thumbnail from `out/yt-thumb-{slug}.png`
3. Creates or finds `{State} Birth Guides` playlist → adds video
4. Creates or finds `All City Birth Guides` master playlist → adds video
5. Saves YouTube video ID to `out/{slug}-youtube-id.txt`

### Upload Metadata Template

```
Title:       {City} Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)
              (keyword-first, under 70 characters)

Description:
You just found out you're pregnant in {City} — now what? This guide walks you
through everything: doulas and midwives serving {City}, hospital policies,
real costs, and whether {State} Medicaid covers a doula.

📱 Download the free app → https://truejoybirthing.com/birth-support/{slug}/

▸ Find {City} doulas & midwives
▸ Compare hospital options
▸ Know what doula care actually costs
▸ Understand {State} Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to {City}
0:10 — What this guide covers
0:28 — {Hospital 1}
0:42 — {Hospital 2}
0:56 — {Hospital 3}
1:10 — Doulas & Midwives in {City}
1:25 — The Joyful Birth Plan App
1:45 — What {City} Birth Costs
2:05 — {State} Medicaid & Insurance
2:30 — Your Free Resources

📲 Free app: https://truejoybirthing.com/app
📝 Free birth plan: https://truejoybirthing.com/birth-plan-template/
📍 {City} page: https://truejoybirthing.com/birth-support/{slug}/

#doulas #birthplan #pregnancy #firsttimemom #expecting #newmom

Tags:
{City} doula, {City} birth doula, {State} Medicaid doula, {City} pregnancy guide,
birth plan template, first time mom {City}, {City} hospital maternity,
{City} doula cost, {State} birth support, doula near me, {City} midwife,
pregnancy {State}, free birth plan, birth preparation, {City} childbirth education

Category: Education
```

### First 48 Hours Protocol

| Time | Action |
|------|--------|
| Hour 0 | Post as Public. Share on city page + Reddit + social |
| Hour 0-6 | Reply to ALL comments (massive ranking signal) |
| Hour 24 | Check CTR (<5% = tweak thumbnail), retention (<50% = adjust chapters) |
| Hour 48 | Verify in-state playlist + master playlist |

### Post-Upload Verification

```bash
# Read back the YouTube ID
YT_ID=$(cat out/{slug}-youtube-id.txt)
echo "Uploaded: https://youtu.be/${YT_ID}"

# Confirm the page renders (may take ~5 min for YouTube processing)
curl -s -o /dev/null -w "%{http_code}" "https://youtu.be/${YT_ID}"
```

---

## Step 19 — Embed YouTube Video on City Page

### 19a. Add Embed Code to [city].astro

Find the Free App section in `src/pages/birth-support/[city].astro`. Insert the YouTube embed BELOW the Free App section and ABOVE the Doulas & Midwives section:

```astro
<!-- YouTube City Guide Video -->
{
  const citySlug = Astro.params.city;
  const youtubeIds: Record<string, string> = {
    'denver-co': 'qmpu7-f_Aio',
    // Add new city here:
    '{slug}': '{YT_ID}',
  };
  const ytId = youtubeIds[citySlug];
}

{
  ytId && (
    <section class="max-w-5xl mx-auto px-4 py-8 md:py-12">
      <div class="aspect-video rounded-xl overflow-hidden shadow-lg">
        <iframe
          width="100%"
          height="100%"
          src={`https://www.youtube-nocookie.com/embed/${ytId}`}
          title="{City} Birth Guide"
          frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
        ></iframe>
      </div>
    </section>
  )
}
```

### 19b. Add VideoObject Schema

In the JSON-LD `@graph` block in `[city].astro`, add a VideoObject entry:

```astro
{
  ytId && {
    "@type": "VideoObject",
    "name": "{City} Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
    "description": "Guide for expectant parents in {City} covering doulas, midwives, hospitals, costs, and Medicaid.",
    "thumbnailUrl": "https://truejoybirthing.com/images/yt-thumb-{slug}.png",
    "uploadDate": "{today's ISO date}",
    "contentUrl": `https://www.youtube-nocookie.com/embed/${ytId}`,
    "embedUrl": `https://www.youtube-nocookie.com/embed/${ytId}`
  }
}
```

### 19c. Thumbnail Verification

The video thumbnail at `public/images/yt-thumb-{slug}.png` must exist (generated in Step 17).

---

## Step 20 — Deploy Page Update

```bash
cd ~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/projects/truejoybirthing-website

# Run standard deploy (includes git sync + build + push)
bash scripts/deploy.sh {slug}

# Verify the YouTube embed is live
curl -s "https://truejoybirthing.com/birth-support/{slug}/" | \
  grep -o "youtube-nocookie.com/embed/[A-Za-z0-9_-]*" | head -1

# Verify the thumbnail returns 200
curl -s -o /dev/null -w "%{http_code}" \
  "https://truejoybirthing.com/images/yt-thumb-{slug}.png"
```

---

## Step 21 — Provider Opt-In Re-Render

When a provider responds positively to outreach and agrees to be featured in the video (typically Email 3, Day 35+):

### 21a. Confirm Opt-In

Ask: *"Would you be open to being featured by name and photo in our YouTube guide for {City} families? No obligation — I will send you the clip to review first."*

Only proceed if they say yes. Do not feature providers without explicit consent.

### 21b. Re-Render with Named Portraits

1. **Update scene data:** In `remotion/src/data/{slug}-data.ts`, add `tjb_provider_portrait` scenes after the `tjb_provider_grid` scene — one per opted-in provider
2. **Update narration:** Use the `Provider Named` narration template from 9c, including their name, credential, practice, and a personal detail
3. **Regenerate TTS** for the affected scenes (delete old WAVs first: `rm -f public/audio/{slug}/scene-0[34]*.wav`)
4. **Rebuild durations → master WAV → sync validate** (Steps 12-14)
5. **Capture stills → send to Jeff for approval** (Step 15)

### 21c. Upload as NEW Video

**YouTube does not support in-place video replacement.** The updated video gets a new YouTube ID:

1. Rename the rendered file: `cp out/{slug}-city-guide.mp4 out/{slug}-city-guide-v2.mp4`
2. Upload: `python3 scripts/upload-youtube.py {slug}` — use `--suffix "v2"` or manually specify a different title (e.g., append "Updated July 2026")
3. Save the new YouTube ID

### 21d. Update Embed + Re-Deploy

1. Replace the old YouTube ID in `[city].astro` with the new one
2. Update the VideoObject schema `uploadDate` to the new date
3. Re-deploy via `bash scripts/deploy.sh {slug}`

The old video stays on YouTube (it still drives search traffic). The refreshed video becomes the embedded one on the city page.

### 21e. Update Trackers

- Set `video_status` in `city-priority-list.csv` to `live`
- Note the provider opt-in in the Google Sheet outreach tracker

---

## Pipeline Model Routing (Video Phase)

| Subtask | Model | Why |
|---------|-------|-----|
| Scene data creation | GPT-5.5 (flat-rate) | Structure + narration quality matters |
| TTS generation | API call (Mistral Voxtral) | Direct API, no LLM needed |
| Duration calculations | Python script | Mechanical |
| Master WAV rebuild | Shell commands | Mechanical |
| Sync validation | Python script | Mechanical |
| Still capture | Shell/Remotion | Mechanical |
| QA checklist | GPT-5.5 | Judgment needed |
| Thumbnail generation | Shell/Playwright | Mechanical |
| YouTube upload | Python script | Mechanical |
| Embed code | Manual edit + deploy | Human judgment for placement |

---

## Pipeline Diagram (Decision Tree)

```
Phase 1 complete?
  YES → Prerequisites check (Step 8)
           PASS → Create scene data (Step 9)
                  → Copy assets (Step 10)
                  → Generate TTS (Step 11)
                  → Set durations (Step 12)
                  → Rebuild master WAV (Step 13)
                  → Sync validation (Step 14)
                         PASS → Capture stills (Step 15)
                                → Send to Jeff for approval
                                       APPROVED → Render full video (Step 16)
                                                  → Generate thumbnail (Step 17)
                                                  → Upload to YouTube (Step 18)
                                                  → Embed + redeploy (Steps 19-20)
                                                  → Update video_status=live in CSV
                                                  → ✅ G8 PASSES
                                       REJECTED → Fix slides → Go to Step 11
                         FAIL → Fix durations → Go to Step 12
           FAIL → Set video_status=deferred in CSV with reason. Done.

Provider opts in later (Email 3, Day 35+)?
  YES → Update scene data (named portraits)
       → Regenerate TTS → rebuild durations → master WAV → sync validate
       → Capture stills → Jeff approval
       → Re-render → upload as NEW YouTube video
       → Update embed ID → re-deploy
       → ✅ DONE
  NO  → Keep generic grid. Video is fine as-is.
```

---

## Anti-Patterns — What NOT to Do

### Phase 1 (City Page)

| Anti-Pattern | Why |
|-------------|------|
| Skip `validate-city-data.ts` | Catches every regression. Run before every commit. |
| Deploy without outreach | Page is NOT done until outreach sent. |
| Use standalone "Free Birth Plan" | Branded term is "Joyful Birth Plan." |
| Fabricate birth centers or NICU levels | Verify via NPI + Google Maps. |
| Let subagents write directly to cities.ts | Schema drift, partial edits. |
| Patch whole sections of cities.ts | Omitted fields silently dropped. Always incremental. |
| Use `write_file` to round-trip `.ts` files | Line-number injection. Use `patch` or `python3 heredocs`. |

### Phase 2 (Video)

| Anti-Pattern | Why |
|-------------|------|
| **Render without sync validation** | #1 failure mode. Sync drift of 6+ seconds by end of video. NEVER skip. |
| **Use Math.round() for frame computation** | Silently drops frames. Always use `Math.ceil()`. |
| **Render full video before Jeff approval** | 5-10 min wasted if changes needed. Use stills. |
| **TrustOffice chrome carry-over** | Most common visual mistake. Check: top accent bar, corner brackets, T-icon logo, footer divider, footer text block. Remove ALL. |
| **Whole-second durations** | 0.8s per scene drift compounds. Use decimal, frame-precise. |
| **youtube.upload scope** | Silently uploads to personal channel. Must use `youtube` scope. |
| **Upload before channel phone-verified** | Thumbnails.set returns 403. Verify at youtube.com/verify first. |
| **Post >1 video per day** | Algorithm spam flag. Max 1 per day on new channel. |
| **Named provider portraits without opt-in** | Presumptive. Use `tjb_provider_grid` (photo grid with sweep) as default. Only use `tjb_provider_portrait` (named) after opt-in at Email 3 (Day 35+). |
| **Skip bridge/overview scene** | NYC → hospitals jumps without context. Bridge is mandatory. |
| **Omit midwife from cost/insurance/app narration** | Jeff corrected this. Doulas AND midwives always. |
| **Use OG image as thumbnail** | OG = blog banners (1200×630). Thumbnail = YouTube-specific (1280×720) with play indicator and dark blur box. Different format, different job. |
| **"Android coming soon" text on CTA** | Prohibited. Just show Google Play badge. |
| **Dark bg on CTA slide** | CTA slide must be light cream (#FAF8F5). |
| **Assume CF auto-deploy is instant** | Check deployment list for your commit SHA. Don't report "deployed" without verifying. |
| **Hardcode provider isVerified=true** | Pull from cities.ts. Only true if provider confirmed via outreach. |
| **Skipping still-approval workflow** | Jeff will ask for screenshots of changed slides. Save the iteration — send before rendering. |
| **Forget to handle the 20MB src/index.ts binary** | Rename before render/still commands, restore after. It's a video file in the .ts extension. |
| **Don't regenerate audio after script changes** | Old WAV files survive silently. `rm -f public/audio/{slug}/scene-*.wav` then regenerate all. |
| **Use AI-generated screenshots instead of real app screenshots** | Jeff corrects this immediately. Use real 390×844 app screenshots. |

---

## Locked Values Reference

| Item | Value |
|------|-------|
| Voice ID | `331c27cd-1809-43c2-853d-4c167f184670` |
| TTS model | `voxtral-mini-tts-latest` |
| Frame rate | 30 fps |
| Frame computation | `Math.ceil()` |
| Resolution | 1920×1080 |
| Phone frame dimensions | 300×650px, second phone top:63 left:188 |
| Phone frame container height | 720px |
| Thumbnail size | 1280×720 |
| Thumbnail design | Hero silhouette + lavender gradient + dark blur box + play indicator |
| YouTube scope | `youtube` (NOT `youtube.upload`) |
| Max uploads per day | 1 |
| Target video duration | 2:30–4:00 (hard cap 5:00) |
| Max hospitals featured | 3 |
| Provider default mode | `tjb_provider_grid` (photo grid sweep) — switch to `tjb_provider_portrait` (named) only after opt-in |
| Og image + page hero + thumbnail | Same hero image file — zero drift |
| Remotion entry point | `src/index.tsx` (not `src/index.ts` — that's a binary video) |

---

## File Reference

| File | Path |
|------|------|
| Integrated pipeline doc | `web-strategy/integrated-city-video-pipeline.md` |
| Full city pipeline | `tjb-city-pipeline` skill |
| Video production | `tjb-video-production` skill |
| Sync validator | `tjb-video-sync-validator` skill |
| Page preflight | `tjb-page-preflight` skill |
| YouTube strategy | `content/youtube-posting-strategy.md` |
| TJB design system | `content/tjb-video-design-system.md` |
| Remotion project | `video/remotion/` |
| YouTube upload script | `video/remotion/scripts/upload-youtube.py` |
| Thumbnail renderer | `~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/projects/truejoybirthing-website/scripts/render-yt-thumbnail.cjs` |
| Per-city video quickstart | `references/per-city-video-quickstart.md` (in tjb-city-pipeline skill) |
| Video pipeline skill | `tjb-city-video-pipeline` skill — Phase 2 entry point |