# Execution Plan — State-Newborn-Procedures Feature (Phased, Agent-Runnable)

**Plan doc:** `Kit/life/brands/TrueJoyBirthing/plans/2026-09-24-state-newborn-procedures-plan.md` (Chante feedback 2026-09-24 + Jeff decisions §6)
**Project repo:** `Kit/life/brands/TrueJoyBirthing/projects/TrueJoyBirthing-Mobile/`
**Status 2026-09-24:** Phase 1 DONE (3f9f972c). Phase 2 DONE — all 51 jurisdictions verified, mojibake-swept, pushed (9849adf7). Phases 3-7 defined below. This doc is the executable runbook — each phase is a bounded agent task.

**Ground truth already established (do not re-litigate):**
- CA data file: `backend/data/state_resources/ca.json` — 8 procedures, 18 URLs all HTTP-200 verified 2026-09-24.
- API: `backend/routes/state_resources.py` — GET `/api/state-resources` (list), `/{state}`, `/{state}/procedure/{key}`; auth via `check_role` all roles; friendly 404 `not_configured` for missing states. E2E-tested on live server.
- Validator: `scripts/validate_state_resources.py` — schema check always; `--links` verifies every URL HTTP-200; optional state filter.
- CA legal specifics (for agents to mirror in other states): TRF religious refusal signed on the form itself; hearing/CCHD/eye-ointment have NO state declination form → written informed refusal; vitamin K has no state form → 3-way choice oral/shot/none; parents (not midwife) are billed for NBS.
- Language rule: **"informed choice" everywhere; never "against medical advice."**
- Vitamin K: three-way (oral / shot / none). Master form: ONE signature block for all items. No physician signatures; optional referral note field.

**Definition of "researched" per state (the CA standard):**
1. Official newborn metabolic screening program page + parent-education page.
2. Whether a parent declination/opt-out form exists (exact URL + form number) or refusal is documented otherwise (on the collection form / in writing only) — cite the statute or regulation.
3. Homebirth/out-of-hospital midwife instructions (kit ordering, submission deadlines, specimen tracking).
4. Hearing screening: state program page + out-of-hospital path.
5. CCHD pulse-ox: who performs out-of-hospital, any state reporting.
6. Eye ointment: state statute (mandatory vs permissive), any state waiver form.
7. Hep B birth dose: registry/reporting requirements.
8. Program contact (phone/email), billing facts if published.
9. EVERY URL verified HTTP-200 by the validator `--links` mode. No exceptions.

---

## Phase 1 — CA proof (DONE 2026-09-24, commit 3f9f972c)
- [x] `ca.json` researched & built (18 URLs verified live)
- [x] `state_resources.py` router wired into server.py
- [x] E2E verified: register→CA 200, procedure deep-links, unknown state friendly 404, unauth 401
- [x] `validate_state_resources.py` validator

## Phase 2 — Parallel state research: 51 states (COMPLETE 2026-09-24)
**Done.** 5 parallel agents + 1 catch-up agent produced all 50 states + DC. Orchestrator verification: validator `--links` 51/51 exit 0 (247 URLs live-checked), full-batch mojibake sweep clean after double-encoded UTF-8 fixes (71fc4f90, 9849adf7), coverage set() check: no dupes/gaps. Pushed to origin.
**Encoding discipline learned (apply to any future state-data work):** subagent research tends to double-encode UTF-8 — after writing any state JSON, sweep for `Ã`, `Â[^§]`, lone `â`-remnant patterns before commit; layered latin-1→utf-8 decode cycles recover most; a surgical string replace cleans triple-encoded stragglers.

**Agent contract (verbatim in each goal):**
1. For each assigned state, research the official state programs (state .gov sites, state health dept newborn screening pages, state midwifery licensing board guidance). Use web_search + web_extract only; no browser logins.
2. Write `backend/data/state_resources/<lowercase-2letter>.json` matching EXACTLY the schema of `ca.json` (read it first): top keys `state, state_name, last_verified, verified_by, procedures, program_contact`; all 8 procedure keys; `opt_out_form` = exact URL or `null`; where `null`, fill `state_form_note` explaining how refusal is documented + statute cite; fill `midwife_role` for every procedure; `last_verified` = today.
3. Run `python3 scripts/validate_state_resources.py --links <2-letter>`. Fix every failure until exit 0. A link that cannot be verified 200 after 3 tries gets deleted from the file (note in `state_form_note` where it was) — never leave an unverified URL in the file.
4. Commit: `git add backend/data/state_resources && git commit -m "state-resources: <XX> data (N urls verified)"`.
5. Return: state list covered, procedures requiring midwife-only informed choice (no state form), any state with genuinely unusual rules (1 line each). NO URLs in the summary — files are the deliverable.
6. Constraints: no file edits outside `backend/data/state_resources/` and no edits to files already committed by others (read latest main before starting); never fabricate a URL — if a state publishes no homebirth instructions, say so in `state_form_note`; 5-minute tool timeout awareness: batch research state-by-state, write each JSON immediately after its state is done.
**Acceptance:** validator `--links` passes on every batch; orchestrator runs `--links` (all) and diffs the 51-file list against the assigned set; zero dupes/missing.

## Phase 3 — Informed-choice master doc + sign flow (backend)
- [ ] New template type `informed_choice` in the contracts/waiver pipeline (mirror `midwife_contract_template.py` pattern). One master doc, checkbox per procedure, ONE signature block (mom sign+date, midwife sign+date).
- [ ] Language gate: string-scan generated doc text — hard-fail on "against medical advice" (case-insensitive); CI-safe unit test.
- [ ] Vitamin K renders 3-way radio (oral/shot/none) in the doc.
- [ ] Sign flow mirrors `POST /contracts/{id}/sign`; store with `retention_until = signed_at + 10y`; PDF export via existing `/contracts/{id}/pdf`.
- [ ] Unit tests: template render, language-gate, retention math, sign flow.
**Acceptance:** tests green; sample master PDF generates with all 8 items + single signature block.

## Phase 4 — Birth-plan "Newborn Procedures" section + cards (backend + app)
- [x] Backend: add `newborn_procedures` to `BIRTH_PLAN_SECTIONS` (mom.py:20, admin.py:20, server.py:553); decisions shape `{procedure_id: {choice, decided_at, doc_id}}`. — DONE (0d987daa): added to care_plans.py (serving route), mom.py, admin.py, server.py; persistence verified E2E.
- [x] App: `src/components/NewbornProceduresForm.tsx` — per-procedure decision card (opt-in / opt-out / undecided); vitamin K 3-way (oral | shot); state form deep-link when `opt_out_form` non-null, informed-choice doc creation otherwise; state auto-fills from `profile.location_state`, never re-asked. Wired into `app/(mom)/birth-plan.tsx` renderSectionContent. — Kit ✅ 71a351c7
- [x] Title/icon maps updated: mom birth-plan (icon → approved `newborn_care` glyph), provider client-birth-plans, admin content titles. — Kit ✅ 71a351c7
- [x] Unknown state → friendly "generic informed-choice cards" fallback (never a dead end) — implemented (banner + generic cards when profile state missing or state JSON fetch fails).
- [ ] Midwife-visibility gate: section renders only when mom has a midwife relationship (hospital-only moms don't see it). — PENDING (next task)
- [ ] App E2E (EXPO RN) acceptance run — PENDING (part of the testing pass Jeff requested 2026-09-25).
**Acceptance (updated):** app E2E (EXPO RN): mom in CA sees CA links; mom with no state data sees generic cards; hospital-only mom sees no section.
**Design note:** cards follow approved design system (design_guidelines.md); PDF packet for Jeff/Chante visual review before ship, per visual-review preference — packet due with the testing plan.

## Phase 5 — Web documentation hub (truejoybirthing.com)
- [ ] Generator script renders 51 per-state pages from the JSON data (single source of truth — no hand-written state facts) + hub index page: "Newborn procedures by state."
- [ ] Each state page: program links, opt-out form (or "no state form — signed informed choice" explanation), midwife homebirth instructions, billing note, "Verified [last_verified]" stamp. No medical advice, official .gov links only.
- [ ] One explainer post: "Informed choice vs. against medical advice: what you're actually signing" (Chante's framing).
- [ ] Humanize pipeline on every publishable text (scan gate: HIGH RISK = do not ship). CF Workers path for TO site (frontend/deploy.sh).
**Acceptance:** all 51 pages render from data; humanize scan ≤ MEDIUM on all; links from app deep-link to state pages (web + app share one source).

## Phase 6 — Retention flag + midwife doc view/export
- [ ] Midwife client-file view lists all informed-choice docs per client with retention date.
- [ ] Bulk PDF export per client.
**Acceptance:** midwife surface E2E + retention date correct (10y).

## Phase 7 — Biannual link-check cron (create at the END)
- [ ] `state-links-check.py` — script-only, no_agent=True: re-run validator `--links` on all 51 files; diff vs stored link map; report to `reports/state-links/<date>-report.md`; silent on all-green; on breakage → 3-line Discord alert to #truejoybirthing-main + report path (detect-and-defer; no LLM in the cron itself).
- [ ] Cadence 2x/year (Jan 15 / Jul 15). Cron Alternative Gate analysis already documented in plan §4. First run Jan 15, 2027.
**Acceptance:** framework registration + one manual dry-run showing silent-success behavior.

## Phase 8 — Payment plans (independent track, do NOT block on 2-7)
- [ ] `payment_plan` subdoc on invoices: custom schedules — provider sets n installments (amount, due_date, status); mom-side payment view; status roll-up (due/partial/paid).
- [ ] One invoice per mom per provider; trackable midwife→mom and doula→mom.
**Acceptance:** backend tests + E2E on the provider + mom surfaces.

## Deploy & verification discipline (applies to every phase)
- One Railway deploy at the END of Phases 3+4 (backend+frontend batched) and one after Phase 5; both through the mandatory gate: load `railway-deploy` skill, deploy-preflight.sh, `deployments(last:1) status == SUCCESS`, live health probe. Never report deployed without verification.
- Never delete files; archive instead. Job records per phase in JOB-LEDGER. Status vocabulary: queued/assigned/running/checkpointing/waiting/completed/stalled/failed/dead_letter/cancelled.
- Humanize gate for anything publishable. Brand-identity block: no logos/marks.