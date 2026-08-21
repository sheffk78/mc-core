---
file: CHANGELOG.md
brand: TrustOffice
type: changelog
description: Running log of all TrustOffice changes — features, fixes, decisions, and market-intel-driven updates.
last_updated: 2026-07-30
updated_by: Kit
---

# TrustOffice — Changelog

**Every change to TrustOffice gets logged here.** Features, bug fixes, strategic decisions, and market-intel-driven updates. This is the single source of truth for "what changed and when."

---

## 2026-08-21: TO-014 Referral Program — deployed + live-verified

**What:** Refer a Friend fully implemented, deployed, and verified live. Closes the last outstanding TO walkthrough item.

**Implementation (commits `f1f10d9` backend, `1194972` frontend):**
- Backend `referrals.py`: `my-code`, `stats`, `validate/{code}`, `track`, and `credits` endpoints; `process_referral_conversion()` issues $50 flat credit; `apply_pending_credits_to_invoice()` applies credits on `invoice.created` (monthly 1/cycle, annual compound); `clawback_credit()` on `charge.refunded`; $500 lifetime cap + 12-month expiry + idempotency guard.
- Frontend: Settings → Refer a Friend section updated (credit balance, lifetime credits, expiring credits), dedicated `/referral` page.
- Rules per Jeff decision 2026-08-20: $50 flat credit, $500 lifetime cap, 12-month expiration, monthly 1/cycle, annual unlimited, refund clawback, referee 50% off first payment.

**Verification (2026-08-21):** Backend endpoints live in OpenAPI spec; frontend bundle `main.f7d824b9.js` serves the referral UI; live smoke tests passed (my-code, stats, validate public exact/lowercase/invalid, auth 401 enforced); credit conversion → invoice → clawback wiring confirmed in the live bundle. Test user created for verification and deleted via admin API afterward.

**Status:** ✅ Live-verified

## 2026-08-21: Verify-first sweep catches discrepancies; Advisor parity + TO-013 + Trust Roles completed

**What:** Post-feature-review verification (5 parallel agents) caught two records-vs-reality divergences, plus a third parity gap. Fixed all three; logged the verification method as the catch mechanism.

**Changes (TrustOfficeApp commit `bd48111`, marketing commit `8fae8e3`):**
- **Advisor pricing over-promise (in-app):** `PricingPage.js`, `UpgradeModal.js`, `SubscriptionGate.js` still claimed "client view, white-label" as live. Corrected to match marketing: client-view + multi-signature → "coming Q3 2026"; white-label binder export stays live (genuinely implemented).
- **TO-013 beneficiary AI knowledge base (rebuild):** Logged "live-verified" but the file didn't exist. Created `backend/knowledge/23-beneficiary-types-and-allocations.md` (8.5K), wired 43 keywords into `_format_knowledge_context()`, added "Beneficiary and Allocation Guidance" to `chat_system_core.md`. Verified routing via venv.
- **Template count reconciled:** Marketing said "31 legal templates" in 5 places; real user-facing count is **36** (backend enum 37 incl. non-user-facing `blank`). Updated index/features/trust-governance-offer.
- **TO-011 Trust Roles tab:** Jeff decided 2026-08-21 — drop the redundant single-item "Trust Roles" tab bar; keep inline role sections. Removed from `SettingsPage.js`.
- **Vault-gate tier-3 documented** (not claimed done): on-demand full-text injection is a future enhancement; Tier 1 + Tier 2 verified.

**Verification note:** The "all done" trigger wasn't met — files logged complete were missing. Lesson: verify claims against code before marking done; several subagents hit iteration caps and truncated, so re-verify truncated items independently.

**Status:** ✅ Code committed + frontend builds clean; backend deploy + health verify in progress.

---

## 2026-07-30: Market Intelligence Loop Buildout

**What:** Fully configured the weekly market intelligence loop — added pricing intelligence track, updated cron with skills + model pin, refined research prompt.

**Changes:**
- `MARKET-INTEL-REFERENCE.md` — added Pricing & Packaging section to feature-to-signal map (4 signal patterns: competitor price drops, tiered pricing, enterprise plans, per-trust vs flat pricing)
- Cron `trustoffice-market-intel` (a4b36e2e3e90) — added skills (`daily-research`, `firecrawl-competitive-intel`), pinned model to `glm-5.2`, refined prompt with named competitors (EstateOS, Vanilla, FreeWill, Trust & Will), explicit Reddit subs (r/trusts, r/estateplanning), web_search/web_extract only (no SearXNG/Camoufox)
- First run scheduled Monday Aug 3 at 7:00 AM MT

**Why:** The cron was a bare shell — no skills, no model pin, generic research queries. Product reviewers flagged pricing intelligence as a missing track. This closes both gaps.

**Status:** ✅ Live — first run Aug 3

---

## 2026-07-30: Market Intelligence Loop Established

**What:** Created weekly market intelligence loop — automated research → gap analysis → action cycle.

**Files created:**
- `MARKET-INTEL-REFERENCE.md` — feature-to-market-signal mapping with audience filter
- `CHANGELOG.md` — this file
- Weekly cron job `trustoffice-market-intel` (Monday 7:00 AM MT)

**Why:** Continuous awareness of market shifts, competitor moves, and audience demand without manual effort. Every signal is filtered through "is this our audience?" before escalation.

**Status:** ✅ Live

---

## 2026-07-25: Brand Folder Structure Cleanup

**What:** Standardized brand folder structure with three mandatory files.

**Files:**
- `BRAND-STATUS.md` — consolidated from TRUSTOFFICE-LIVE-STATE.md
- `DECISIONS.md` — strategic decision log
- `SKILLS-INDEX.md` — skill inventory

**Why:** Align with AGENTS.md standards, clear ownership mapping, avoid file drift.

**Status:** ✅ Complete

---

## 2026-07-25: Backend + Frontend Architecture Documentation

**What:** Complete architecture documentation for both backend and frontend.

**Files:**
- `TRUSTOFFICE-BACKEND-ARCHITECTURE.md` — 23 MongoDB collections, 68 API routers
- `TRUSTOFFICE-FRONTEND-ARCHITECTURE.md` — 46 pages, 46 components, React Router v7
- `TRUSTOFFICE-FEATURE-IMPLEMENTATION-PLAN.md` — 3-phase roadmap

**Why:** Enable informed feature decisions and reduce onboarding time for new agents.

**Status:** ✅ Complete

---

## 2026-07-24: WingPoint Exclusive Annual Plan

**What:** Created WingPoint-exclusive unlimited trust plan at $99/mo ($1,188/year), annual only.

**Stripe product:** `prod_UwgOxNK1Jw47cy`

**Why:** Reward WingPoint customers who upgrade to TrustOffice. Clear upgrade path from education → tooling.

**Status:** ✅ Deployed

---

## 2026-06-30: Calendar Auto-Population + Recurring Tasks

**What:** Tax deadlines now auto-generate at trust creation. Recurring governance tasks (quarterly, annual, compensation, asset revaluation) auto-create next cycle on completion.

**Why:** Users shouldn't discover features — the system should work by default.

**Status:** ✅ Deployed (commit a7ed729)

---

## 2026-06-30: Vault + AI Chat Integration

**What:** AI assistant now queries vault documents. Document-level citations with article numbers. Intelligent context gate prevents cost bloat on casual questions.

**Why:** Trust documents are the foundation of governance — the AI should know what they say.

**Status:** ✅ Deployed

---

## 2026-06-29: Admin Privacy Lock + Distribution Templates

**What:** Users can block admin/impersonation access. Beneficiary distribution notice template added.

**Why:** Trust data is sensitive. Users should control who can access their account.

**Status:** ✅ Deployed

---

## 2026-06-22: Major Quality Batch

**What:** 34 files updated — brand token violations fixed, rounding standardized, TrustManager component created, E2E flow test completed (12 bugs found, 3 critical fixed).

**Why:** Systematic quality push to meet "premiere tool for trustees" standard.

**Status:** ✅ Deployed

---

## 2026-06-09: Email Template Fix

**What:** Subscription confirmation email changed from "unlimited trusts" to "Up to 10 trusts & entities" to match actual product capability.

**Why:** Honest state of product — PRINCIPLES.md § ethics.

**Status:** ✅ Deployed

---

## 2026-06-04: Pricing Structure Finalized

**What:** Three-tier pricing: Trustee ($79/mo), Estate ($149/mo), Advisor ($399/mo). No free trial confirmed.

**Why:** Simple pricing, clear upgrade path, serious audience.

**Status:** ✅ Permanent

---

## 2026-04-26: No Free Trial Decision

**What:** Removed free trial and freemium model. Direct purchase only.

**Why:** Frequent churn from low-intent users. High support costs. Better alignment with target audience.

**Status:** ✅ Permanent

---

## Changelog Rules

1. **Every change** gets an entry — features, fixes, decisions, market-intel findings that drove action
2. **Market-intel-driven entries** include the signal that triggered them (e.g., "Reddit demand: X → added Y")
3. **Entries are chronological** — newest first
4. **Status labels:** ✅ Live / 🔄 In Progress / 🔲 Planned / ❌ Reverted
5. **Cross-reference** IMPROVEMENT-BACKLOG.md items by number where applicable
