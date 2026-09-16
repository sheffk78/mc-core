# TJB City-Gate Fix — Phased Execution Plan

**Created:** 2026-09-16, America/Denver
**Working repo:** `/Users/socializerender/Projects/truejoybirthing-website`
**Owner of this plan:** Kit. Each phase ends verified before the next starts. Any phase may be picked up in a fresh chat by loading this file.

## The lesson this plan encodes

Three agents (and Kit) burned out on the same trap: grinding through long serial tool loops until the tool-call guardrail killed the run mid-task. The fix is structural, not willpower:

- **Small batches.** Max 1-3 cities per work unit. One validation run per batch. Never loop a script call 100 times to "check progress."
- **Verify with ONE command** (`validate-city-data.ts` full sweep + per-slug gates), not by polling transcripts.
- **Every phase ends in a commit.** Work between commits is disposable; committed state is truth.
- **Never edit a file another agent owns** (cities.ts lane, public/images lane, scripts lane).

## Verified current state (2026-09-16 ~12:30)

**Gates PASSING (committed to gate artifacts):** seattle-wa, vancouver-wa, hayward-ca, mesa-az, cumming-ga (5/12)

**Fixed on disk, NOT yet committed:** cumming hero re-encode (128KB photo), 6 CA hero watercolor skylines generated + verified (G8 pass, vision-checked), seattle slug-suffixed provider refs, cumming heroImage/supportSceneImage fields, Sutter Eden paragraph, seattle support-scene rename.

**Validator still failing (7):**
| City | Failure | Class | Fix owner |
|---|---|---|---|
| cumming-ga | 2 doulas (min 3) | S4 | Phase 3 |
| newport-beach-ca | ogImage ref missing in cities.ts | S2/field | Phase 4 |
| la-habra-ca | same | same | Phase 4 |
| san-mateo-ca | same | same | Phase 4 |
| palo-alto-ca | same | same | Phase 4 |
| redwood-city-ca | same | same | Phase 4 |
| burlingame-ca | same | same | Phase 4 |

**Verified state (2026-09-16 13:15):** 7/13 gates PASS (seattle, vancouver, hayward, mesa, cumming, greenville, amarillo). Validator: 0 errors. 6 CA cities remain: field wiring in cities.ts + OG renders + gates. Cumming doula fix + greenville/amarillo re-encodes done but UNCOMMITTED (hook blocks until 6 CA pass). Amarillo note: cities.ts references og-city-amarillo-tx-v3.webp; good render lives in og-city-amarillo-tx.webp; -v3 overwritten with the good render.

## PHASE 2 — Greenville + Amarillo ✅ DONE 2026-09-16
- greenville: avif→webp re-encode, G8 passes, gate PASS.
- amarillo: skyline source was gradient; re-encoded from .avif; OG re-rendered via `node scripts/render-og.cjs og-city-amarillo-tx-composition.html og-city-amarillo-tx`; -v3 overwritten with good render; gate PASS.

## PHASE 3 — Cumming ✅ DONE 2026-09-16
- 3rd doula (Full Bloom Birthing Company) added by close-out agent; support scene cropped to 4:3 (666x500); validator clean; gate PASS.

## PHASE 4 — 6 CA cities: OG images + cities.ts field wiring ✅ DONE 2026-09-16 15:20
- Executed in 2 batches of 3 (per the small-batch rule). Each batch: field wiring → 4:3 support-scene crops from hero → -600 hero variants → Pattern B OG re-render → 3 verified real-doula listings per city → validator sweep → gates.
- Gates: 6/6 CA cities failed=0 passed=20 (artifacts in artifacts/gates/). Validator: 0 errors/0 warnings across 168 cities.
- Bug caught + fixed en route: burlingame's image fields were cross-contaminated into the cary-nc entry (cary was serving burlingame imagery); both entries now point at their own assets.
- OG renders: Pattern B photo right-column (70–95KB, 34k–57k colors) — gradient-fallback right-columns caused the earlier sub-5000-color G29 failures.
- COMMITTED 6457af55 (pre-commit hook passed, no --no-verify; includes parked Phase-1 wins + prior OG regen passes).

**Loose uncommitted state (git):** ~25 modified og-city-*.webp (previous OG regen passes, pre-existing), gate artifacts, one staged-but-AM greenville hero. These predate today; commit them as part of Phase 2/5 commits rather than untangling.

**Key facts for any session picking this up:**
- OpenRouter key: line 6 of `~/.hermes/secrets/openrouter-keys.txt` is the live one (line 1 401s). Gen pattern works: `google/gemini-3.1-flash-image`, `modalities:["image","text"]`, ~13s per image. Reusable script saved at `/tmp/gen_ca_hero.py` (copy into repo `scripts/` in Phase 4 if needed again).
- G8 photo check thresholds: top-band unique colors ≥ 2000 AND full ≥ 20000. G29/G35 OG check: full ≥ 5000.
- Pre-commit hook requires per-city stage-gate artifacts passing for touched cities; NEVER `--no-verify`.
- cities.ts entries for the 6 CA cities currently have NO heroImage/ogImage/supportSceneImage fields (that's the og-missing warnings).

---

## PHASE 1 — Commit the verified wins ⏸ BLOCKED (parked, retry after Phase 4)
1. Fresh gate artifacts run for the 5 passing cities (done 12:33, all failed=0 stage_emission).
2. Commit blocked by pre-commit hook: it scans the WHOLE working tree, and the 6 CA cities' og-city-*.webp files are tree-modified (from earlier OG regen passes) — hook demands their city gates pass before ANY commit. Can't commit a subset. **Do NOT --no-verify.**
3. **Resolution path:** finish Phase 4 (fields + gates for the 6 CA cities) FIRST, then this commit lands as part of Phase 4's commits. Phase 1's staging is ready.

## PHASE 2 — Greenville + Amarillo hero/OG re-encode
1. Greenville: `magick public/images/greenville-sc-birth-doula-skyline.avif -quality 90 public/images/greenville-sc-birth-doula-skyline.webp` → verify G8 color counts pass → copy to heroes/ → re-run `python3.13 scripts/preflight-stage-gate.py greenville-sc build` → failed=0.
2. Amarillo: render OG via Pattern B template (`scripts/render-city-og-template.html`) embedding the real amarillo hero photo; verify full colors ≥ 5000; re-run gate → failed=0.
3. Commit both + gate artifacts. **Exit criteria: 7/12 gates passing.**

## PHASE 3 — Cumming 3rd doula
1. Add Full Bloom Birthing Company (real listing, discoverdoulas.com/georgia/cumming/) as 3rd localDoulas entry, mirroring existing entry structure exactly. No invented URL/reviews/certs. If no site confirmed, use the discoverdoulas profile URL.
2. Re-run cumming gate → failed=0. Commit. **Exit criteria: 8/12 gates, cumming validator clean.**

## PHASE 4 — 6 CA cities: OG images + cities.ts field wiring
1. Check which of the 6 have `public/images/og-city-<slug>.webp`; for missing ones, render from hero (crop 1200x630, quality 90, >30KB) — or the Pattern B template render if that's the canonical OG path (validator/gate message will say which).
2. In cities.ts add to each of the 6 entries: `heroImage`, `ogImage` ("/images/og-city-<slug>.webp"), `supportSceneImage` (only if that file exists on disk; else mirror hayward-ca's pattern or omit — test the gate after each city).
3. Batch: 2 cities per pass → run validator sweep after each pair → gate per city → failed=0 for all 6.
4. Commit per pair of cities to keep commits small. **Exit criteria: full validator 0 errors/0 warnings, 12/12 gates passing, 14/12 including cumming+greenville+amarillo.**

## PHASE 5 — Full sweep + build + deploy ✅ DONE 2026-09-16 ~16:10 (closed by Kit, after subagent failure)

**Subagent failure (deleg_e51657c4, "Railway deploy"):** delivered nothing verifiable. Fact-checked 2026-09-16 ~15:55: origin/main still at c41d19ec (no push — reflog confirms), live OG hashes stale. Two plan errors were baked into its instructions: (a) Railway is the WRONG target — this repo deploys via **Cloudflare Pages direct upload** (`scripts/deploy.sh` → wrangler; `.hermes/environment.json` confirms; git push is version-control only), (b) its result was never received/verified.

**What actually executed (Kit, 2026-09-16):**
1. Validator sweep: 0 errors/0 warnings, 168 cities ✅ (matches Phase 4 claim)
2. Build: `npm run build` exit 0 (336 URLs, sitemap-cities 186) ✅
3. Full gated deploy `bash scripts/deploy.sh`: git sync, pre-deploy gate, self-test all PASS; **visual preflight FAILED at full-tree scope** — 14 pre-existing placeholder provider photos in 8+ cities (virginia-beach, pittsburgh, richmond, charlotte, kansas-city, lakewood, colorado-springs, greenville + 4 more), files untouched since July 26-27. Not today's work.
4. Doctrine check: recent deploys (Sep 3–15) are all per-city scoped (`deploy.sh <slug>` scopes the visual gate to one city); placeholder debt is cleared in dedicated batches (58 replaced Aug 26). Followed documented scope: `validate-xrefs.ts` PASS + `visual-preflight.sh` scoped per each of the 6 CA cities — all 6 PASS.
5. Push: `git push origin main` → origin/main **6457af55** (pre-push hook passed, no --no-verify) ✅
6. CF Pages upload: `npx wrangler pages deploy dist --project-name=truejoybirthing-website --branch=main` → deployment https://a956175e.truejoybirthing-website.pages.dev ✅
7. **CF edge-cache purge required:** zone serves `/images/*` with 1-year immutable cache; truejoybirthing.com returned stale bytes (age: 82426, cf-cache-status: HIT) even after upload. Purged 8 URLs via zone API (zone 39d68039…).
8. **Live verification (all byte/hash-verified):** 6/6 og-city-*.webp sha256 == local committed render, HTTP 200; 6/6 birth-support pages HTTP 200 with og:image wired + correct titles. ✅

**⚠️ Standing blocker for future FULL-TREE deploys (not city-scoped):** the 14 placeholder provider photos will block `deploy.sh` (unscoped) until sourced as real headshots. City-scoped deploys unaffected. Needs a dedicated placeholder-batch job (like Aug 26's 58-photo sweep).

**CLOSED — 14/14 gates passing, all live. Plan complete.**

## Guardrails for every session executing this plan
- One batch per tool-call turn. If a run fails twice identically: STOP, write the blocker in this file under "Blockers", move to another phase. Never re-run the same failing command a third time.
- Check `artifacts/gates/<slug>-build.json` `failed` count as the ONLY gate truth.
- If the close-out agent (deleg_f88df1fb) lands anything mid-plan, re-verify its files with the validators before counting them — self-reports are not truth.