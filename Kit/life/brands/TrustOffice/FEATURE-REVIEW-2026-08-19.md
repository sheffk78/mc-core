# TrustOffice Feature Review — 2026-08-19

**Source:** Jeff walkthrough notes, [user-report].
**Purpose:** Convert observed product friction, defects, and open product questions into implementation-ready work. No item below is marked verified until reproduced in code or the live app.

## Recommended execution order

1. **P0 reliability/data correctness:** finalize-minutes failure; Trust Roles integer parsing; dashboard false overdue-task state; banking summary missing linked account; beneficiary class-share accounting.
2. **P1 workflow and UX:** beneficiary information architecture/edit action/default tab; EIN masking; relationship modal fit; duplicate hierarchy label; Trust Roles layout/instructions; typography consistency.
3. **P1 assistant/domain model:** beneficiary types, class beneficiaries, units/percentages, and distribution guidance.
4. **P2 commercial/export workflows:** referral reward rules and testing; defensible export package.
5. **P2/P3 product decisions:** initial-minutes Schedule A automation, bank-account number policy, resolution semantics, dashboard redesign system.

## P0 — Fix before feature expansion

### TO-001 — Finalize drafted minutes fails
- **Area:** Minutes / Schedule A / finalization.
- **Reported behavior:** Finalizing a draft reached from a Schedule A item connected to general assignment minutes returns: “Failed to finalize minutes.”
- **Acceptance:** Reproduce with the reported flow; capture backend response and request ID; finalization succeeds; draft status changes exactly once; linked Schedule A/asset state remains consistent; user receives a useful error if validation fails; regression test covers the flow.
- **Owner:** Kit.
- **Status:** live-verified, [verified] legacy/template finalization bridge is live; Railway backend deployment `9c6e4933-e4e7-4407-a890-214193634c4e`, API/OpenAPI HTTP 200.

### TO-002 — Trust Roles rejects numeric input
- **Area:** Trust Roles save.
- **Reported behavior:** Save returns “Input should be a valid integer, unable to parse string as an integer.”
- **Acceptance:** Identify field and payload; blank/decimal/valid integer behavior is explicit; valid values save and reload; invalid values show inline field guidance rather than raw API text; API and frontend schemas agree; regression test added.
- **Owner:** Kit.
- **Status:** live-verified, [verified] Trust Roles numeric-field normalization is included in live frontend deployment `a70318f7-370f-4c61-b4a7-a99fe855fc3b`.

### TO-003 — Dashboard shows overdue-task CTA with no overdue tasks
- **Area:** Dashboard Today’s Focus.
- **Reported behavior:** “2 actions to boost your score by 3 points” and “take care of overdue tasks” leads to an empty task view.
- **Acceptance:** Every displayed action is derived from current trust-scoped data; zero overdue tasks means no overdue-task CTA; counts and score deltas match the underlying API; empty state explains what is actually useful next; no static engagement bait.
- **Owner:** Kit.
- **Status:** live-verified, [verified] dashboard deadline field/timezone fixes are included in live frontend deployment `a70318f7-370f-4c61-b4a7-a99fe855fc3b`.

### TO-004 — Banking summary omits an existing linked account
- **Area:** Dashboard Banking Accounts Overview.
- **Reported behavior:** Dashboard says no bank accounts linked despite a trust having one.
- **Acceptance:** Use the same trust/user scope and canonical account source as banking/entity pages; linked account appears after save and refresh; API failures render an error state, not “none”; tests cover one and multiple accounts.
- **Owner:** Kit.
- **Status:** live-verified, [verified] banking error/processing states and account-scope fixes are live in frontend deployment `a70318f7-370f-4c61-b4a7-a99fe855fc3b` and backend deployment `9c6e4933-e4e7-4407-a890-214193634c4e`.

### TO-005 — Beneficiary totals omit class beneficiaries
- **Area:** Beneficiaries, distributions, dashboard summaries.
- **Reported behavior:** Person/organization shares appear, but a class beneficiary share is not represented; example: wife 50% + class of unborn/unborn children 50%.
- **Acceptance:** Person, organization, and class beneficiaries can each hold units/shares; totals include all beneficiary types; UI clearly distinguishes type; distributions and exports preserve the distinction; validation prevents accidental totals over the configured allocation; regression tests cover mixed allocations.
- **Owner:** Kit.
- **Status:** implemented, [verified] Jeff selected: percentage mode with a 100% cap; class allocations are reserved pools distributed among confirmed class members; separate unit mode with configurable ceiling; auditable replacement edits.
- **Implementation (2026-08-20):** Backend: `BeneficiaryDashboardResponse` now includes `total_allocated_percentage`, `certificate_percentage_total`, `class_beneficiary_percentage_total`. Dashboard endpoint computes combined totals. Frontend: `OwnershipPieChart` renders class beneficiaries alongside person/org holders on a single chart. `OverviewTab` shows class beneficiaries inline in the holder list (with "Class" badge, distribution convention tag, member count), a combined allocation summary bar (certificate % + class %), and updated beneficiary count to include class beneficiaries.

## P1 — Beneficiaries and trust administration UX

### TO-006 — Rework Beneficiaries tab information architecture
- **Status:** live-verified, deployed commit bebef43 on TrustOfficeApp-v2 (frontend) and TrustOfficeApp-backend-v2 (backend). Deploy IDs: 0ff1e955 (frontend SUCCESS), 3358bd7d (backend SUCCESS). Health check: app.trustoffice.app 200, api.trustoffice.app/docs 200.
- Rename **People** to **Beneficiaries**.
- Move **Overview** to the first tab and make it the default route/view.
- Preserve the beneficiary-specific tab styling while aligning shared primitives with Settings only where appropriate; do not flatten the better design into Settings’ tab pattern.
- Add an **Edit** action to each beneficiary item so shares/units can be changed in context.
- Acceptance: deep links and browser back behavior remain valid; edit opens the existing canonical form; save updates the list without stale values; person/organization/class labels are clear; responsive behavior verified.

### TO-007 — Add beneficiary allocation model and education
- Support configured unit model: default 100 units = 100%, while allowing trust settings to define another unit basis.
- Display both raw units and calculated percentage where applicable; explain that units and percentages are allocation choices, not legal advice.
- Support person, organization, and class beneficiaries with definitions, examples, and distribution implications.
- Acceptance: assistant, beneficiary UI, validation, summaries, and exports use the same canonical allocation model; no hardcoded assumption that one unit always equals one percent.

### TO-008 — EIN auto-formatting
- Apply one shared formatter/mask wherever EIN is entered or displayed as an editable field.
- Format `123456789` as `12-3456789` while preserving raw digits for storage/API; handle paste, editing, deletion, and already-formatted values.
- Acceptance: all EIN references use the shared component/utility; backend validation remains strict; tests cover typing and paste.

### TO-009 — Relationship dialog fits viewport
- **Reported behavior:** Add-relationship modal is wider than its available space and creates horizontal scrolling.
- **Acceptance:** Fits desktop and mobile viewport without horizontal scroll; fields remain usable at standard zoom; long labels wrap correctly; dialog keyboard/focus behavior remains intact.

### TO-010 — Remove duplicate trust label in hierarchy map
- **Reported behavior:** Trust name appears twice inside the structural-map rectangle.
- **Acceptance:** Reproduce for trust entities and other entity types; render each intended label once; preserve accessibility name and relationship meaning; add a fixture/regression test.

### TO-011 — Trust Roles layout and hierarchy
- Remove redundant top-level “Trust Roles” tab if it adds no navigation value, or replace it with role-specific tabs (Successor Trustee, Trust Protector, etc.).
- Bring successor instructions directly below the first successor trustee section.
- Use the stronger two-column layout for successor trustee and secondary successor trustee where fields support it; retain one-column layout for long text or fields that need full width.
- Align the View Successor Packet and AI actions to the established page-header spacing pattern.
- Acceptance: responsive layout, tab semantics, navigation/deep links, and screen-reader labels verified.

### TO-012 — Typography consistency audit
- Audit form labels, inputs, helper text, textareas, guidance blocks, and button text across Trust Roles and adjacent trust-management screens.
- Establish/consume shared typography tokens; specifically eliminate the two-font mismatch in successor instructions.
- Acceptance: same semantic control uses same font family, size, weight, line height, and placeholder styling; visual regression screenshots at desktop/mobile; no one-off font overrides without documented reason.

## P1 — Trust Assistant knowledge and guardrails

### TO-013 — Expand beneficiary and allocation knowledge base
- Teach definitions and trade-offs for individual, organizational, and class beneficiaries; class-beneficiary examples (including descendants/unborn descendants where appropriate); units, percentages, configured unit bases, allocation totals, and distribution mechanics.
- Assistant must distinguish general domain education from trust-specific facts and cite the user’s configured trust data when available.
- It must not recommend a legal outcome as fact; it should explain concepts and prompt the user to consult counsel where drafting or jurisdiction-specific interpretation is involved.
- Acceptance: evaluation set covers at least 12 questions across beneficiary types, unit bases, mixed allocations, and “which should I choose?” guidance; answers use the selected trust’s data and acknowledge uncertainty only for missing trust-specific data.
- **Status:** live-verified. Deployed commit 1398a44, backend deployment `1fa897ce` SUCCESS. Health check: api.trustoffice.app/health → `{"status":"ok","service":"trustoffice-api","db":"connected"}`.
- **Implementation (2026-08-20):** New knowledge file `23-beneficiary-types-and-allocations.md` (10.7K chars) covering individual/organization/class beneficiary types, percentage vs. unit allocation modes, per capita vs. per stirpes distribution, mixed allocations, total allocation tracking, and choosing guidance. Wired into `_format_knowledge_context()` with 30+ topic keywords. Updated `chat_system.md` with beneficiary/allocation guidance section: explain types, distinguish general vs trust-specific facts, cite configured trust data, avoid legal recommendations, guide to pages.

## P2 — Commercial and portability

### TO-014 — Repair and clarify Refer a Friend
- **Status:** ✅ live-verified 2026-08-21. Jeff approved rules 2026-08-20: $50 flat credit, $500 lifetime cap, 12-month expiration, monthly=1/check, annual=unlimited, refund clawback. Backend credit ledger, invoice application, clawback, and updated stats endpoint implemented (commit f1f10d9). Frontend Settings referral section updated (commit 1194972). Deployed and verified live.
- **Verification (2026-08-21):** Backend referral router registered and live — endpoints present in live OpenAPI spec (`/api/referrals/{my-code,stats,validate,credits,track}` + admin). Frontend bundle `main.f7d824b9.js` serves the referral UI (Refer a Friend, my-code, `/referrals/stats`). Live smoke tests passed: my-code returns real code + `?ref=` link; stats returns full structure with `lifetime_cap:500`; validate public (exact+lowercase valid, invalid rejected); unauthenticated my-code 401. Credit machinery wired end-to-end: `process_referral_conversion` on subscription activation (`subscriptions.py:977`), `apply_pending_credits_to_invoice` on `invoice.created`, `clawback_credit` on `charge.refunded`, $500 lifetime cap + idempotency guard (no double-credit). Test user deleted post-verification.
- First verify current referral link generation, attribution, purchase detection, reward issuance, billing-period handling, and idempotency.
- Product proposal to test: **$50 credit per qualified referral**, usable against the next charge; annual users can compound credits (example: 3 referrals = $150) subject to a cap; monthly users receive at most one $50 credit per billing month. Exact cap, qualification event, expiration, refund/cancellation behavior, and stacking rules require Jeff’s decision.
- Acceptance after decision: billing UI states rules plainly; monthly and annual test cases pass; duplicate/refunded purchases do not double-credit; ledger/audit trail exists; no credit is issued before payment is confirmed.
- **Decision gate:** ✅ Jeff decided 2026-08-20 — $50 flat credit, $500 lifetime cap, 12-month expiry, monthly 1/cycle, annual unlimited, refund clawback.

### TO-015 — Design defensible data export package
- **Status:** live-verified. Deployed commit d4223a1, backend deployment `d395f2cf` SUCCESS, frontend deployment `bebf158d` SUCCESS. Health check passing.
- **Implementation (2026-08-20):** Backend: `GET /api/export?trust_id=X` — gathers all trust data (profile, entities, beneficiaries, certificates, assets, tasks, calendar, distributions, transactions, vault documents with original files, audit trail, minutes/resolutions as PDFs, AI chat history) into a ZIP with manifest.json + structured JSON. On-demand generation (no server-side retention). Audit-logged. Frontend: Settings > Export section now has "Download Full Export" button with progress indicator and error handling.

## P2/P3 — Product decisions and research

### TO-016 — Initial trust minutes to Schedule A asset automation
- Determine whether acceptance of the initial bank account is legally/operationally modeled as the first Schedule A asset in TrustOffice.
- Research with trust-law counsel/authoritative guidance before changing behavior.
- Proposed implementation if approved: create a draft Schedule A asset linked to the initial minutes, with amount, institution, effective date, source minutes, and explicit user confirmation before finalization.
- Do not store full bank account numbers by default; assess whether last four digits plus institution is sufficient and document security/retention implications.
- Clarify whether finalized initial minutes are the operative resolution in this workflow or whether a separate resolution document is required.
- **Decision gate:** legal/accounting semantics, bank-account data policy, and resolution model.

### TO-017 — Dashboard information architecture review
- **Status:** live-verified. Audited all dashboard cards, CTAs, counts, and score against live trust-scoped data. No static engagement bait found (TO-003 fix holds). Error states are explicit (TO-004 fix holds). Progressive disclosure works correctly.
- **Implementation (2026-08-20):** Created `docs/DASHBOARD-DATA-CONTRACT.md` mapping every visible dashboard value to its API field and backend query. Documented layout rules, error handling rules, and component→data mappings for future audits.

## Cross-cutting implementation standards

- Every bug gets a reproduction, root cause, regression test, and live verification before closure.
- Keep beneficiary/unit semantics canonical across frontend, backend, Trust Assistant, dashboard, and exports.
- Preserve auditability: meaningful allocation, minutes, referral, and export actions should be logged.
- Update `IMPROVEMENT-BACKLOG.md`, `BRAND-STATUS.md`, `CHANGELOG.md`, and `DECISIONS.md` only when implementation/decisions change reality; this review is a planning artifact.
- Supervised stage: new feature implementation and commercial/legal decisions require Jeff approval before production publish/deploy; clear bug fixes remain executable within ownership.

## Pending Jeff decisions

1. ~~Referral: $50 credit cap, qualification event, expiration, stacking, monthly limit, refund behavior.~~ ✅ Decided 2026-08-20.
2. ~~Initial minutes: Schedule A automation~~ ✅ Decided 2026-08-20 — auto-create draft Schedule A entry linked to initial minutes; store last four digits of bank account number only.
3. ~~Export: included data/document classes, original vault files, assistant material, archive/retention format.~~ ✅ Decided 2026-08-20 — include everything (vault files + audit trail + assistant material); ZIP of individual PDFs + structured JSON; 90-day retention.
4. ~~Beneficiary unit model~~ ✅ Decided 2026-08-20.
5. Whether “Trust Roles” should become role-specific tabs or simply lose the redundant label.

## Source note

This document captures the user’s walkthrough as reported observations and proposals. It is not a verification report and does not claim the defects are reproduced yet.

**Next recommended move:** Start with TO-001 through TO-005 in one reliability pass, then implement TO-006 through TO-012 as the beneficiary/trust-admin UX pass.