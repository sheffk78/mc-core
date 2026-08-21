# ACTIVE-TASK — TrustOffice (Authoritative Live State)
<!-- State-kernel model: this is the source of truth for what Kit is working on for TrustOffice NOW. Not a completed-work log. -->

**objective:** Close post-review discrepancies found in verify-first sweep and deploy the batch. ✅ DONE — deployed and verified. **TO-014 referral program also live-verified (2026-08-21)** — all requested TrustOffice changes now closed.

**next todo:** (none blocking) — TO-014 shipped + live-verified. Optional follow-up: fix the 2 pre-existing test failures (`test_k1_march_15`, `test_june_30_fy_extension`) on main; they fail identically pre-#43 and are unrelated.

**Done this session (2026-08-21):**
- ✅ **TO-014 Refer a Friend deployed + live-verified** — backend `referrals.py` endpoints live (my-code, stats, validate, track, credits), credit machinery wired end-to-end (conversion on activation subscriptions.py:977, apply on invoice.created, clawback on charge.refunded, $500 cap, idempotency), frontend bundle serves referral UI. Live smoke tests passed; test user deleted via admin API. Docs updated (FEATURE-REVIEW, TO-014 plan checklist complete, CHANGELOG).
- ✅ **Backlog #43 implemented + deployed** — trusts created in Oct+ now seed next-year tax deadlines. Added `_seed_tax_year()` (month>=10 → next year) in `tax_calendar_math.py`; `_generate_tax_calendar` in `trusts.py` keys idempotency + entries on the seed year. Commit `e560f3f`, backend deploy `c88a7273` SUCCESS, `/health` 200. 31 unit tests pass (2 pre-existing failures confirmed on clean main, unrelated).
- ✅ Restored `TestClampDay` (a subagent mangled the test file with literal `\n`; fixed myself).
- ✅ Deploy verified LIVE: backend deploy `41c1f9b0` SUCCESS (/health 200); frontend bundle `main.1e98aae2` contains Q3 2026 + white-label markers; pricing reads `advisor:"Q3 2026"` for client-view/multi-sig.
- n.b. service `deployments(last:)` shows stale FAILED (08-10/11) — known Railway cache artifact; ground truth = `deployment(id:)` query + live health.
- ✅ Decisions recorded: backlog #43 (next-year deadlines for Oct-1+ trusts) + Advisor Q3 carve-out (3-month BIAN to remove "coming"; features NOT marked done) → DECISIONS.md, IMPROVEMENT-BACKLOG.md.
- Advisor in-app price parity fix (3 files) — client-view/multi-sig → "coming Q3 2026"
- TO-013 beneficiary AI knowledge base rebuilt from scratch (file + 43 kw + core guidance)
- Template count reconciled 31→36 (5 marketing spots)
- TO-011 Trust Roles tab dropped (Jeff decision 2026-08-21)
- Vault-gate tier-3 documented as future enhancement
- Status docs corrected (BACKLOG #10, #47, #48; CHANGELOG)

**human gate (if any):**
```
GATE: none — deployed within ownership lane.
```

**evidence:** `[verified]` TO-014 referral endpoints live (my-code/stats return real data, validate exact+lowercase valid + invalid rejected, auth 401 enforced), credit conversion → invoice → clawback wiring confirmed in live bundle; backend `/health` → HTTP 200; frontend bundle serves referral UI.

---

## Should-Run Assessment (heartbeat)
- **verdict:** `idle` — #43 shipped, TO-014 shipped + live-verified, all named decisions closed. Watch the 2 pre-existing test failures as tech debt; optional to fix next session.
- **why:** Deploy confirmed; no open action items in this lane.

---

## Completed Work → Archive Pointer
- **archived to:** (pending post-deploy)