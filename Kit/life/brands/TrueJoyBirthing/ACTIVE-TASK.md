# ACTIVE-TASK — True Joy Birthing (Authoritative Live State)

## Current: Phase 0 done — growth machines verified/fixed; app ship held for Jeff's testing (2026-09-23)
**Status:** Phase 0 of path-to-500 COMPLETE (report: `reports/2026-09-23-phase-zero-completion.md`).
- City expansion: root-caused (no new-city seeding + bloated dispatcher context) → fixed; seeder committed (`9f5aca65`), 5 new cities seeded, worker fires 13:25. Verify 13:25 run advances a seeded city.
- Outreach sweep: running, catch-up budget 15→25/day; relay verified. ~70 live cities still without first-touch.
- Lead capture: LIVE end-to-end (probe 200). Stale "Brevo blocked" note removed from BRAND-STATUS.
- **Jeff gates:** (1) rotate fresh MailerCloud key into 1Password vault (vault key dead 2026-09-23; live key only in Worker secret) — needed only for API monitoring; the Day 0/3/7 nurture automation is ALREADY LIVE (MailerCloud HSZK, Active since 2026-09-04, list wHHZHy); (2) rigorous app testing before any ship (his explicit hold).
**Next:** Phase 1 = (a) confirm 13:25 city-worker run advances a seeded city → (b) analytics digest cron live (script-only, 09:30 daily, job c82b849956ae, verified 2026-09-23) → (c) nurture = live, no build needed; June 6-email HTML set superseded.

## Current: TJB mobile mom-section design — APPROVED, implementation next (2026-09-17)
**Status:** Mockups S10/S11/S12 rev 3 APPROVED by Jeff (Discord #truejoybirthing-web, msg 1550329273821429811 + scope note msg 1550334582501679155). **Implement the approved design; NO new app generated yet.**
**Approved:** S10 Home + S12 Tips keep hband photo bands; S11 Timer is photo-free (graphical gradient + ripple rings behind circle timer) with body mirroring live `contraction-timer.tsx` structure.
**Next:** implement into `frontend/app/(mom)/home.tsx`, `contraction-timer.tsx`, `weekly-tips.tsx` per the handoff doc. Visuals at every step; no deploy (deploy gate separate); no new app scaffolding.
**Canonical files:** `projects/TrueJoyBirthing-Mobile/docs/design-refresh/surfaces-2026-09-14/` → `IMPLEMENTATION-HANDOFF.md` (execution brief), `VERIFY-s10s11s12.md` (design + verification record), `s10s11s12-mom-home-timer-tips.html` (approved mockup), `renders-s10s11s12/` (approved renders).

---

**objective:** Release v1.5.0 (pre-acceptance messaging) — committed, backend deployed, iOS build 152 submitted to ASC. **Google Play: v1.5.0 (versionCode 152) SUBMITTED FOR REVIEW 2026-09-04 — 9 changes batch, console confirms "Your changes are now in review." Expect ~3–7 business days.**

**next todo:** Confirm iOS build 152 in App Store Connect TestFlight + submit iOS for review. Monitor Google Play review outcome (~Sep 9–11); if approved, production goes live at 100% rollout.

**human gate (if any):**
```
GATE: Security audit — PASSED (2026-08-11). Reviewed new messaging auth, 26/26 tests pass.
GATE: ASC upload/submit — BUILD 152 scheduled for submission via EAS (submission ID 4f221fd4). CLI times out while Apple processes (~5-30min). MUST verify in ASC: My Apps → TestFlight → build 152 appears. Jeff logs in for browser confirmation + review submission.
waits: Jeff to confirm build 152 in TestFlight, then fill What-to-Test + Submit for Review
```

**evidence:** `[verified]` 26/26 pre-acceptance messaging tests pass (:8002). `[verified]` code committed 19131a9d + pushed; backend deploy SUCCESS on Railway (f779b048/9b7e78a5), health `/api/health` = healthy, new accept endpoint returns 401 (not 404) confirming live. `[verified]` version bumped to 1.5.0/build 152, iOS EAS build in progress.

---

## What Changed (this release — v1.5.0 pre-acceptance messaging)
- **Backend:** `routes/messages.py` rewritten — mom can message any provider (auto-creates `conversation_thread` status=pre_acceptance); provider can reply + Accept as Client / Decline from chat; provider cannot cold-message a mom; declined threads block further messaging. New endpoints: `POST /messages/threads/{id}/accept`, `POST /messages/threads/{id}/decline`. `routes/relationship_utils.py` gained `get_thread_between` / `get_active_thread_between`. New `conversation_threads` collection (unique index on mom_user_id+provider_id).
- **Frontend:** mom `messages.tsx` (thread badges, pre-acceptance banner, declined-input, search box in New Message modal), provider `ProviderMessages.tsx` (two-section inbox New Inquiries/My Clients, Accept/Decline CTAs + confirmation modal, search box), `marketplace.tsx` + `provider-detail.tsx` (team-gate removed).
- **Design docs:** `docs/design-pre-acceptance-messaging.md` + `docs/PRE_ACCEPTANCE_MESSAGING_FLOW_v1.1.md`.
- **Test:** `backend/tests/test_pre_acceptance_messaging.py` (26 assertions, all pass).
- **Note:** unrelated +2-line change in `frontend/app/(auth)/login.tsx` (textContentType="username") — accessibility improvement, included.

## Security Audit (release gate — 2026-08-11, PASSED)
- `send_message`: verifies receiver exists, blocks self-send/empty content, `_can_send_message` enforces role rules (provider cannot cold-message a mom without a thread/relationship; declined/terminated threads blocked with 403; mom↔provider pre-acceptance flow).
- `accept`/`decline` endpoints: provider-role-gated (`check_role(PROVIDER_ROLES)`) + ownership check (`thread.provider_id == user.user_id`) + status check (must be pre_acceptance).
- `get_messages`: strictly scoped to authenticated user's conversation (sender/receiver match).
- 26/26 integration tests pass. No new injection/authorization gaps found.

## Completed Work → Archive Pointer
- **archived to:** `SYSTEM/archive/ACTIVE-TASK-TJB-2026-08-10.md` (Pittsburgh + Dallas provider fixes)

# ACTIVE 2026-09-23: SEO Recovery Phases 1-2 (Jeff-approved)
Executing per reports/SEO-DECLINE-ANALYSIS-2026-09-23.md. Template rebuild + CTR sprint + deploy. Then Phase 3 city differentiation next.

## JOB-20260923-P3-BATCH2 — Phase 3 city differentiation, batch 2 (15:42 MDT)
- status: running
- context: Pilot (MD/CT twins) shipped live 15:29 (056c9156/4c1ef927). Jeff resumed the SEO thread at 15:39.
- CAUGHT + REVERTED: uncommitted cities.ts edits found in tree at session resume (stale tail of prior session, static 75s+). All 8 hunks degraded or misfactual: 3x "the named Cohen NICU" at Norwalk (Norwalk's NICU is the Jeffrey Peter Bauer NICU per Nuvance/Northwell; Cohen there is only the Pediatric Emergency Center), 2x vague "verified Level III NICU" prose insertions, 2x parenthetical "(Adventist-verified)" duplicates, 1x awkward FAQ rephrase. Web-fact-checked BEFORE apply; reverted via git checkout; committed live version is correct. Lesson: fact-check named-institution claims against primary sources, never trust inherited uncommitted edits.
- batch 2 targets (phase3-similarity.py, worst pairs >0.50): redwood-city-ca<->palo-alto-ca 0.614, new-braunfels-tx<->temple-tx 0.591, chesapeake-va<->norfolk-va 0.538, melissa-tx<->mckinney-tx 0.534, san-mateo-ca<->redwood-city-ca 0.517.
- method: same as pilot — 1 research subagent per city on the strongest side of each pair (redwood-city-ca, temple-tx, chesapeake-va, melissa-tx, san-mateo-ca), payload via scripts/apply-differentiation-payload.py, gates (city-pages.test.ts 169/169, validate, similarity, humanize scanner), deploy off worker windows, live probes + IndexNow.
- note: redwood-city-ca is in 2 of the 5 worst pairs (0.614 + 0.517) — differentiating it once attacks both.
