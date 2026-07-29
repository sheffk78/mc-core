# Product Quality Cluster — Consolidation Audit

_Produced: 2026-05-02 by Kit_
_Requested by: Jeff Kohler_
_Mandate: Read all reference files, cite findings, flag contradictions and gaps, propose cluster shape, then stop for review. No drafting until Jeff reviews this audit._

---

## 1. Existing Product-Quality Content Found

### 1.1 Product expectations, design principles, and definitions of done

| Passage | File | Lines | What it states |
|---|---|---|---|
| Four checks for every product/workflow | `BRAND.md` | 28–35 | 1. Can an agent do this? 2. Can a human approve in <1 min? 3. Is the audit trail complete? 4. Does it scale to 1,000 agents? |
| Agent-first design principle | `BRAND.md` | 24 | "All tools follow one rule: **agent-first, human-approved**." |
| Design Principles (visual/aesthetic) | `BRAND.md` | 88–92 | Dark, infrastructure-grade; no rounded corners; no animations beyond subtle feedback; reads as trustworthy, technical, long-term. |
| Agent-first implementation checklist | `OFFERS.md` | 230–237 | Four bullets: APIs agents can call for setup; machine-readable responses including reasons; "request human approval" path with rich context; log every action with who/what/why. |
| Design Principles for Agent-First Tools | `Agent_First_Design_Principles.md` | 45–311 | Six principles: Assume Agent Setup-Human Approval; Design APIs for Agents; Minimize Human Input Surface Area; Build Progressive Trust Systems; Make Human Approval Lightweight; Design for Agent-to-Agent Interactions. Plus 10-item implementation checklist. |
| Implementation Checklist (10 items) | `Agent_First_Design_Principles.md` | 222–233 | Includes: agent-initiated via API, structured responses, actionable errors, approval pathway, full context in approval, agent tracking, complete audit trail, programmatic rules, agent-to-agent delegation, lightweight approval UI. |
| Content Quality Gate (scoring) | `agentictrust-01-system-overview.md` | 336–361 | Five dimensions scored 1–5: Authenticity, Specificity, Value, Platform fit, CTA fit. Tier 1 writes → Tier 2 reviews → Tier 3 formats. Fails twice → escalate to Mission Control. |
| Model Tiering specification | `agentictrust-01-system-overview.md` | 30–56 | Tier 1 (Sonnet/Opus) = research & writing. Tier 2 (Sonnet) = review & quality gate. Tier 3 (Haiku) = execution & formatting. Never use Haiku to review Sonnet output. |
| Failure handling rules | `agentictrust-01-system-overview.md` | 297–332 | API timeout → retry once; 401/403 → log and Mission Control immediately; content fails twice → Mission Control; partial success → log separately, surface failures only. |
| Safe-Spend differentiation must-haves | `AgenticTrust_Tool_Stack___Revised_Plan.md` | 86–93 | Escrow accounts, multi-policy per account, time-windowed authority, vendor/category controls, AAV credential link, decision trail (not just transaction log). |
| Safe-Spend MVP checklist | `AgenticTrust_Tool_Stack___Revised_Plan.md` | 120–130 | 7 items: escrow primitives, ≥2 layered policies, basic time-window, vendor controls, optional AAV check, decision trail logging, client hardening. |
| Product availability table | `LIVE-STATE.md` | 20–30 | AAV = Beta/early access; Safe-Spend = Beta waitlist; ARL = Beta; Agreement/Compliance/Service Menu = Phase 2 (not live). |
| Infrastructure gaps | `LIVE-STATE.md` | 138–143 | AgentMail not in TOOLS.md; GenViral not in TOOLS.md; 1Password/Apify orphaned cross-refs; `product/` folder absent. |

### 1.2 Product expectations from sub-brand statuses

From `BRAND-STATUS.md`:
- **AAV**: Core tool verified (registration, grants, certificates, V1 API with constraint enforcement), frontend/backend path mismatches patched, design shipped.
- **Safe-Spend**: Landing renders; `/api/` returns 504; design at v11+ still not approved; redesign needs prototype-first approach.
- **ARL**: Blank screen (new finding today, 2026-05-02 — separate diagnosis doc created). All Railway deployments FAILED since April 23.

### 1.3 Contradictions and inconsistencies

1. **ARL product status contradiction** (`AgenticTrust_Tool_Stack___Revised_Plan.md` line 59 vs. `BRAND.md` line 49 and `LIVE-STATE.md` line 26)
   - Tool Stack calls ARL "**Maybe**" — a Phase 3 optional tool, only built if clients ask for reputation.
   - BRAND.md lists ARL as a core product alongside AAV and Safe-Spend.
   - LIVE-STATE marks ARL as "Beta" — actively offered.
   - **Resolution needed**: Is ARL core or optional? Current operational reality treats it as core (has a domain, a Railway service, a live frontend).

2. **Phase 2 products marketed inconsistently**
   - `BRAND.md` lists Agreement Engine, Compliance Passport, and Service Menu with dates (April, May, June 2026).
   - `LIVE-STATE.md` marks all three as "Phase 2 — not live" with strict rule: "Never market Phase 2 products as available."
   - `BRAND.md` doesn't explicitly market them, but dates suggest availability. Minor tension, not a hard contradiction.

3. **Visual design enforcement gap**
   - `BRAND.md` line 90: "No rounded corners" — this is a hard rule.
   - No process exists to verify UI compliance across live sites. If Safe-Spend v11 has rounded corners, no audit would catch it.

4. **Content Quality Gate ≠ Product Quality**
   - `agentictrust-01-system-overview.md` has an elaborate content quality scoring system (Authenticity, Specificity, Value, etc.).
   - Zero equivalent exists for product/build quality. The closest thing is the Agent_First_Design_Principles implementation checklist, which lives in an archived doc.

---

## 2. Standing Expectations (Jeff's Recent Message, Synthesized)

From `prompt1_agentic_trust.md` (the instruction document itself), Jeff has stated:

1. **Cluster structure**: New Product Quality cluster is structurally parallel to Intel, Content, and Outreach — meaning it needs an anchor skill, canonical handoff contracts, and clear upstream/downstream relationships.
2. **Five skills minimum**: product-router, product-health, product-audit, product-dogfood, product-build.
3. **Audit-first discipline**: Consolidation before creation. Don't draft anything until the audit is reviewed.
4. **Overlap detection**: Explicitly flag any overlap with existing `agentictrust-product-insights` skill.
5. **Principles portability**: Question whether `Agent_First_Design_Principles.md` should be folded into `PRODUCT-EXPECTATIONS.md` or stay separate.
6. **Autonomy expectation**: Jeff has granted Kit "Trusted" stage on AgenticTrust websites — Kit has full authority over code, design, uptime, deployments. Only escalates DNS/registrar and strategic direction.

---

## 3. Current Operational Gaps

Every product-quality issue tracked anywhere:

| # | Issue | Source File | Lines | Owner Today | Severity |
|---|---|---|---|---|---|
| 1 | **AAV blog admin key working** | `LIVE-STATE.md` | 210 | Kit (confirmed working) | ✅ Resolved |
| 2 | **Safe-Spend API key failing auth** | `LIVE-STATE.md` | 211 | Kit | 🔴 High |
| 3 | **RepLedger API key missing** | `LIVE-STATE.md` | 212 | Kit | 🔴 High |
| 4 | **Safe-Spend backend 504 errors** | `BRAND-STATUS.md` | 38 | Kit | 🔴 High |
| 5 | **ARL blank screen** | Diagnosis doc (new today) | — | Kit (diagnosed, not fixed) | 🔴 High |
| 6 | **ARL all Railway deployments FAILED since Apr 23** | Diagnosis doc (new today) | — | Kit | 🔴 High |
| 7 | **Emergent → Railway migration pending** | `LIVE-STATE.md` | 214–217 | Jeff (blocked on priority order) | 🟡 Medium |
| 8 | **Safe-Spend redesign not approved** | `BRAND-STATUS.md` | 37 | Jeff (needs visual prototype) | 🟡 Medium |
| 9 | **Blog auto-publishing blocked (needs API keys)** | `LIVE-STATE.md` | 209; `BRAND-STATUS.md` | Kit | 🟡 Medium |
| 10 | **No product-quality standards doc exists** | — | — | No one | 🔴 High |
| 11 | **No health check endpoints for ARL** | Curl test today | — | No one | 🔴 High |
| 12 | `agentictrust-product-insights` pending | `LIVE-STATE.md`; `SKILLS-INDEX.md` | 119 | Kit (not started) | 🟡 Medium |
| 13 | `product/` folder absent | `LIVE-STATE.md` | 143 | Kit (create on first run) | 🟢 Low |
| 14 | **Safe-Spend frontend/backend path mismatches** | `BRAND-STATUS.md` | 35 | Kit (patched for AAV, not Safe-Spend) | 🟡 Medium |
| 15 | **BATCH-001, BATCH-002 video reviews waiting on Jeff** | `LIVE-STATE.md` | 96–102 | Jeff | 🟢 Low (not product) |

### Gap analysis

- **No proactive health monitoring exists.** Every issue above was discovered reactively (user reports, manual curl, Jeff asking). There is no cron or heartbeat checking `/api/health` on any product.
- **No owner for end-to-end product quality.** Kit owns the code, but there is no explicit skill or process that checks "does the product actually work for an agent-end-user?"
- **`product-insights` is strategic, not operational.** It synthesizes intel into roadmap recommendations. It does NOT check uptime, fix broken deployments, or verify design compliance.
- **Design principles are archived.** `Agent_First_Design_Principles.md` lives in `~OLD/` — it's not referenced by any active skill. The Agent First checklist lives in `OFFERS.md`, which is semantically wrong (it's not an offer).

---

## 4. Proposed Cluster Shape

Based on Jeff's five requested skills. One paragraph each.

### 4.1 `product-router` (cluster anchor)
**Scope:** The intake and triage skill. When a product issue, bug report, deployment failure, design drift, or quality concern is surfaced, `product-router` classifies it by severity (site-down vs. visual nit), product (AAV vs. Safe-Spend vs. ARL), and subsystem (frontend, backend, API, design, infra). It then routes to exactly one downstream skill, or escalates to Mission Control with a clear recommendation. Owns the canonical `product_ticket` handoff contract.

**What it does NOT do:** Fix anything, write code, or run health checks. Pure routing.

### 4.2 `product-health`
**Scope:** Proactive monitoring of deployed products. Scheduled heartbeat checks against each product's health endpoints (for AAV: `/api/health`; for Safe-Spend: `/api/v1/health`; for ARL — endpoint to be defined). Tracks uptime, response times, deployment status on Railway, latest deploy success/failure. Surfaces anomalies as `product_ticket` → `product-router` → Mission Control if human attention needed.

**What it does NOT do:** Diagnose root causes (that's product-audit), or apply fixes (that's product-build). It only detects and reports.

### 4.3 `product-audit`
**Scope:** Periodic deep inspection of each product against the Agent First design principles, the four BRAND.md checks, and the live differentiation claims (e.g., does Safe-Spend actually have escrow accounts, multi-policy support, decision trails?). Runs after major deployments or on a monthly cadence. Produces an audit report with pass/fail scoring against the implementation checklist from `Agent_First_Design_Principles.md`.

**What it does NOT do:** Run continuously like health checks, or actually use the product as a user (that's product-dogfood). It's the standards-compliance layer.

### 4.4 `product-dogfood`
**Scope:** End-to-end product usage as an agent would — API calls, frontend navigation, complete workflows (AAV grant → verify → revoke; Safe-Spend fund → spend → audit trail). Finds the friction that health checks miss: confusing error messages, broken UI flows, API responses that aren't machine-readable, approval paths that take >1 minute.

**What it does NOT do:** Fix the issues found (routes to product-build via product-router).

**Overlap note:** Hermes already has a global `dogfood` skill. `product-dogfood` should be the AgenticTrust-specific wrapper that loads brand voice, product-specific test accounts, and the `Agent_First_Design_Principles` scoring rubric.

### 4.5 `product-build`
**Scope:** The execution arm. Receives approved `product_ticket` items with clear scope and implements the fix: code changes, config updates, Railway redeploys, environment variable fixes, nginx proxy adjustments. Follows the SYSTEM/DEVELOPMENT-STANDARDS.md quality gate (RED-GREEN for bug fixes, spec-first for features).

**What it does NOT do:** Decide whether to fix something (router does), diagnose (audit does), or monitor (health does). It's the fix-only skill.

### 4.6 Overlap with `agentictrust-product-insights`

| Dimension | `product-insights` | New Product Quality cluster |
|---|---|---|
| **Purpose** | Strategic synthesis — roadmap, feature gaps, competitive positioning | Operational execution — uptime, quality compliance, bug fixes |
| **Cadence** | Monthly (or triggered by weekly-deep-dive) | Continuous (health) + periodic (audit) + on-demand (router/build) |
| **Consumes** | Intel cluster output (weekly-deep-dive nuggets) | Live product state, deployment status, API responses, user friction |
| **Produces** | Roadmap recommendations for Jeff | Fixed products, health dashboards, audit reports |
| **Overlap** | **None.** They are orthogonal. Product-insights answers "what should we build?" Product Quality answers "is what we built working?" |

**Verdict:** No overlap. `product-insights` stays in Cluster 4 (Intel downstream). The new Product Quality cluster is a separate operational lane.

---

## 5. Recommendations

### What to keep where it is

| Item | Location | Rationale |
|---|---|---|
| Agent First design philosophy (the "why") | `~OLD/Agent_First_Design_Principles.md` | Rich, historical, cited. Keep as reference, not primary operational doc. |
| The four BRAND.md checks | `BRAND.md` lines 28–35 | Already the canonical first-stop for brand context. Concise, memorable, loaded at every session start. |
| Design principles (visual) | `BRAND.md` lines 88–92 | Right place — visual identity belongs in brand reference. |
| Content Quality Gate | `agentictrust-01-system-overview.md` | Content-specific, not product-specific. Leave it. |
| Content model tiering | `agentictrust-01-system-overview.md` | Content-specific. Leave it. |
| `product-insights` skill | `SKILLS-INDEX.md` Cluster 4 | Strategic lane. Stays separate. |

### What to move

| Item | Current Location | Proposed New Location | Rationale |
|---|---|---|---|
| Agent-first implementation checklist (4 bullets) | `OFFERS.md` lines 230–237 | New `PRODUCT-EXPECTATIONS.md` (or folded into it) | Not an offer — it's a quality standard for how products must behave. Semantically wrong in OFFERS.md. |
| Safe-Spend differentiation table | `AgenticTrust_Tool_Stack___Revised_Plan.md` | Keep in Tool Stack; also copy to `PRODUCT-EXPECTATIONS.md` as testable criteria | The table defines what "working" means for Safe-Spend. It should be auditable. |
| Safe-Spend MVP checklist (7 items) | `AgenticTrust_Tool_Stack___Revised_Plan.md` lines 120–130 | Keep in Tool Stack; also copy to `PRODUCT-EXPECTATIONS.md` | Same reasoning — these are definition-of-done criteria. |

### What to create

| Item | Purpose | Owner |
|---|---|---|
| `PRODUCT-EXPECTATIONS.md` | Single source of truth for product quality standards — the condensed, checkable, versioned standards doc. | `product-audit` loads this; all product-build tasks verify against it. |
| `product-router.md` skill | Cluster anchor. Defines `product_ticket` payload, routing rules, severity classification. | Core of new cluster. |
| `product-health.md` skill | Heartbeat monitoring, Railway deployment tracking, health endpoint polling. | Runs as cron. |
| `product-audit.md` skill | Monthly standards compliance audit against `PRODUCT-EXPECTATIONS.md`. | Manual trigger or monthly cron. |
| `product-dogfood.md` skill | End-to-end workflow testing per product, using real test accounts. | On-demand or weekly. |
| `product-build.md` skill | Fix execution, deployment, code changes. Only consumes approved tickets. | On-demand from router. |
| `product/` folder | Storage for audit reports, health logs, dogfood test results, build tickets. | `LIVE-STATE.md` infrastructure section. |

### What to delete

Nothing should be deleted. `Agent_First_Design_Principles.md` is archived already (`~OLD/`). The old `agentictrust-content.md` was properly archived per `DECISIONS.md` entry 2026-04-12. The new cluster adds files; it does not remove historical documents.

### Specific question: `Agent_First_Design_Principles.md` — fold or separate?

**Recommendation: Keep it separate as a reference file. Do NOT fold it into `PRODUCT-EXPECTATIONS.md`.**

Rationale:
- `Agent_First_Design_Principles.md` is 375 lines of philosophy + market validation + real-world examples + competitive analysis. It's the "why."
- `PRODUCT-EXPECTATIONS.md` should be a tight, checkable standards document — the "what" and "how to verify." Probably <100 lines.
- The relationship: `PRODUCT-EXPECTATIONS.md` distills the design principles into auditable criteria. `Agent_First_Design_Principles.md` provides the reasoning when someone asks "why does this standard exist?"
- Jeff's workflow preference: he discovered tools independently and asks for verification. A 375-line philosophy doc is not a practical verification checklist. A separate condensed doc is.

**Proposed relationship:**
```
Agent_First_Design_Principles.md (reference, historical, ~OLD/)
    ↓ distilled into
PRODUCT-EXPECTATIONS.md (operational, versioned, AgenticTrust root)
    ↓ loaded by
product-audit.md, product-dogfood.md, product-build.md
```

---

## 6. Open Questions for Jeff

1. **ARL status resolution.** Tool Stack calls ARL "Maybe" (Phase 3 optional). BRAND.md and live infrastructure treat it as core. Is the Tool Stack outdated, or is ARL genuinely on probation?

2. **`product-build` autonomy boundary.** Under current stage (Trusted), Kit has full authority over code/deployments. Does this extend to the Product Quality cluster — meaning `product-build` can fix bugs and redeploy without explicit Jeff approval per fix? Or should there be a spending/severity threshold (e.g., auto-fix under $0, ask for >$0)?

3. **Health endpoint for ARL.** Currently `api.reputationledger.dev` returns 404. AAV and Safe-Spend both expose `/api/health`. Should ARL add one? Or should `product-health` check the Railway deployment status directly?

4. **SLA / detection target.** How quickly should the Product Quality cluster detect a blank screen or 504? Options: 5 minutes (aggressive cron), 1 hour (moderate), 24 hours (daily sweep)? This determines `product-health` cron frequency.

5. **Product-dogfood test accounts.** Does Jeff want Kit to create and maintain dedicated test accounts on each product, or use the existing `Kit testing accounts` mentioned in the Emergent → Railway migration? If the latter, where are the credentials?

6. **`product-insights` activation.** Currently pending. Should it be activated alongside Product Quality, or remain deferred until someone is actually asking for roadmap analysis?

7. **Failure handling integration.** The OpenClaw system overview has detailed failure handling rules (retry once, Mission Control on double fail, etc.). Should Product Quality cluster use the same pattern, or adopt the newer Hermes SYSTEM/RELIABILITY-STANDARDS.md pattern (incident severity, postmortem format)?

8. **ARCHITECTURE QUESTION:** Should the new Product Quality cluster live in `SKILLS-INDEX.md` as "Cluster 5" (shifting Community Engagement to Cluster 6), or does it supersede/rename the existing "Cluster 4 — Product" that only contains `product-insights`?

---

## Appendix: Files Read for This Audit

| File | Path | Status |
|---|---|---|
| BRAND.md | `Kit/life/brands/AgenticTrust/BRAND.md` | ✅ Read in full |
| AUDIENCE.md | `Kit/life/brands/AgenticTrust/AUDIENCE.md` | ✅ Read in full |
| OFFERS.md | `Kit/life/brands/AgenticTrust/OFFERS.md` | ✅ Read in full |
| BRAND-STATUS.md | `Kit/life/brands/AgenticTrust/BRAND-STATUS.md` | ✅ Read in full |
| LIVE-STATE.md | `Kit/life/brands/AgenticTrust/LIVE-STATE.md` | ✅ Read in full |
| DECISIONS.md | `Kit/life/brands/AgenticTrust/DECISIONS.md` | ✅ Read in full |
| SKILLS-INDEX.md | `Kit/life/brands/AgenticTrust/SKILLS-INDEX.md` | ✅ Read in full |
| AGENTS.md | `Kit/life/brands/AgenticTrust/AGENTS.md` | ⚠️ Not found (expected — lives at workspace root `AGENTS.md`) |
| Agent_First_Design_Principles.md | `Kit/life/brands/~OLD/Agent_First_Design_Principles.md` | ✅ Read in full |
| agentictrust-01-system-overview.md | `Kit/life/brands/~OLD/agentictrust-01-system-overview.md` | ✅ Read in full |
| AgenticTrust_Tool_Stack___Revised_Plan.md | `Kit/life/brands/~OLD/AgenticTrust Tool Stack – Revised Plan.md` | ✅ Read in full |
| agentauthority.dev | Live site | ✅ HTTP 200 |
| safe-spend.dev | Live site | ✅ HTTP 200 |
| reputationledger.dev | Live site | ✅ HTTP 200 (blank screen per diagnosis) |
| api.reputationledger.dev | Live API | ⚠️ HTTP 404 (no health endpoint) |
