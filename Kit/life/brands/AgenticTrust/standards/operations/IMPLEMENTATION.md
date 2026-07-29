# AgenticTrust Implementation Standards

Brand-specific overlays to the core `kit-*` operating standards. This is where AgenticTrust-specific configuration, adaptations, and operational conventions live.

---

## Tech Stack & Tool Selection

| Category | Core Kit Default | AgenticTrust Selection | Override Reason |
|----------|---------------|----------------------|-----------------|
| **Frontend** | — | React (Vite) + Tailwind | Already in production |
| **Backend** | — | FastAPI (Python) + Multi-service architecture | Multiple sub-brands (AAV, ARL, Safe-Spend) |
| **Database** | — | PostgreSQL on Railway | Shared service |
| **Auth** | — | Supabase Auth | User auth + sessions |
| **AI/LLM** | — | Direct model APIs + internal agents | Agent infrastructure |
| **Email** | Sentry | SendGrid | SendGrid is active; no change needed |
| **Hosting** | — | Railway (all sub-brand sites) | Railway Docker multi-stage |
| **CDN** | — | Hover DNS + Railway | Landing pages served via Railway |

### Sub-brand Sites
All deployed to Railway under shared account:

| Sub-brand | Domain | Stack |
|-----------|--------|-------|
| Agent Authority Vault | agentauthority.dev | React static, Railway |
| Agent Reputation Ledger | reputationledger.dev | React static, Railway |
| Safe-Spend | safe-spend.dev | React static, Railway |
| AgenticTrust main | agentictrust.app | (evaluate — currently not deployed separately) |

---

## Deployment Patterns

### Landing Pages (AAV, ARL, Safe-Spend)
- **CD:** Git push → Railway auto-deploy (each sub-brand has separate Railway project)
- **Rollback:** `railway service rollback` or Railway dashboard redeploy
- **Feature flags:** Not currently used for static landing pages

### Blog Pipeline (Safe-Spend only)
- **Content source:** Markdown → GitHub → Railway deploy
- **Automation:** Cron job for generating + publishing blog posts
- **Override:** Safe-Spend blog automation is Kit's most mature content pipeline — prioritize here over manual creation

### Critical Notes
- **Railway token:** Read from `~/.hermes/secrets/railway-token.txt` — canonical single source of truth, works across all projects. The `RAILWAY_API_TOKEN` env var may drift/stale; do not trust it without verification.
- **DNS:** Hover DNS requires Jeff escalation — Kit cannot manage Hover directly
- **LibreOffice:** WingPoint image includes LibreOffice (~700MB); separate from AgenticTrust sub-brands
- **No Friday afternoon deploys** per `SYSTEM/DEVELOPMENT-STANDARDS.md`

---

## Monitoring & Alerting

| Property | Uptime Probe | Error Tracking | Performance | Status |
|----------|-------------|---------------|-------------|--------|
| agentauthority.dev | Railway built-in health | To be added | To be added | Partial |
| reputationledger.dev | Railway built-in health | To be added | To be added | Partial |
| safe-spend.dev | Railway built-in health | To be added | To be added | Partial |

### Alerting Channels
- **Primary:** Discord + Kit autonomous monitoring
- **P1 (site down):** Investigate within 5 minutes, notify Jeff if persistent >30 minutes
- **P2 (degraded):** Investigate within 30 minutes, update LIVE-STATE.md
- **P3 (informational):** Log in daily notes

**TODO:** Add Sentry to all three sub-brand services. Add synthetic check for homepage + CTA forms.

---

## Customer Feedback Loop

### Channels
- **Social mentions:** Kit monitors AgenticTrustKit X account directly (autonomous posting)
- **Blog comments / email:** Minimal — traffic is discovery-oriented, not support-oriented
- **Partnership requests:** Refer to Outreach research skill

### Bug Report Handling
- AgenticTrust sub-brands are lower-traffic than TrustOffice. Bug reports are minimal.
- When found: Kit reproduces → fixes directly (clear root cause) → deploys → updates post-log.md

---

## Quality Gate — AgenticTrust "Done" Overrides

The core `SYSTEM/DEVELOPMENT-STANDARDS.md` Quality Gate applies. AgenticTrust adds these brand-specific checks:

- [ ] **Sub-brand visual consistency** — Safe-Spend, AAV, ARL share design system (see `design-system.md`)
- [ ] **Blog pipeline smoke test** — Post generates → builds → deploys → renders correctly
- [ ] **No AI slop in landing page copy** — Reviewed with `humanizer` skill; brand voice per sub-brand
- [ ] **CTA forms functional** — Currently minimal; any added forms must integrate with backend
- [ ] **AgenticTrustKit X post links verified** — Any URL in scheduled posts must 200 before posting

---

## Escalation Overrides (from `AGENTS.md (charter folded in)`)

The Charter's escalation list applies. AgenticTrust-specific additions:

- **Hover DNS changes:** Escalate to Jeff — Kit cannot manage Hover
- **New sub-brand or naming changes:** Escalate to Jeff (public brand identity)
- **X account strategy changes:** Kit owns day-to-day (1 original + 5-10 engagements/day, Mon-Fri)
- **Blog content cadence:** Kit owns (2x weekly Tue/Fri for Safe-Spend; evaluate for AAV/ARL)
- **Spending >$50/month on new tools:** Escalate — currently within OpenRouter/Google API budgets

---

## Known Issues & Runbook Snippets

| Issue | Symptom | Resolution | Last Verified |
|-------|---------|-----------|-------------|
| AAV/ARL design refresh | Old design still visible | AAV-REDESIGN-SPEC.md and ARL-REDESIGN-SPEC.md drafted; waiting on Jeff's review | 2026-04-29 |
| Safe-Spend blog automation | Scheduled posts may fail silently | Check cron logs in Railway dashboard; verify `posts.json` format | 2026-04-14 |
| OpenRouter metered spend | Unpredictable costs | Default to flat-rate models (Kimi via Ollama); OpenRouter = dormant override only | 2026-04-30 |
| Hover DNS lag | Domain changes take time to propagate | Notify Jeff when requesting DNS changes; allow 24-48h for propagation | Ongoing |

---

## Changelog

| Date | Change | Trigger |
|------|--------|---------|
| 2026-04-30 | Standards file created | Kit Charter + development/reliability standards installed |
