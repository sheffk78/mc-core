# TrustOffice Implementation Standards

Brand-specific overlays to the core `kit-*` operating standards. This is where TrustOffice-specific configuration, adaptations, and operational conventions live.

---

## Tech Stack & Tool Selection

| Category | Core Kit Default | TrustOffice Selection | Override Reason |
|----------|---------------|----------------------|-----------------|
| **Frontend** | — | React + Tailwind | Already in production |
| **Backend** | — | FastAPI (Python) | AI-powered workloads |
| **Database** | — | PostgreSQL on Railway | Production DB |
| **Auth** | — | Supabase Auth | User auth + sessions |
| **AI/LLM** | — | Custom AI backend (OpenRouter for some calls, direct model APIs for others) | AI trust governance features |
| **Email** | Sentry | SendGrid | SendGrid is active; no change needed |
| **Hosting** | — | Railway + Cloudflare Pages | Railway (app), Cloudflare (marketing site) |
| **Payment** | — | Stripe | rk_live_ key; coupon restricted |
| **CDN** | — | Cloudflare | Marketing site only |

---

## Deployment Patterns

### App (app.trustoffice.app)
- **CD:** Git push → Railway auto-deploy (production branch protected; deploy on merge)
- **Preview:** Railway preview deployments for PR review
- **Rollback:** Railway dashboard or `railway service` CLI rollback
- **Feature flags:** Not currently used — evaluate if needed for paid tier rollout

### Marketing Site (trustoffice.app)
- **CD:** Push to main → Cloudflare Pages auto-deploy via Astro
- **Preview:** Cloudflare Pages preview URLs for PRs
- **Rollback:** Re-deploy prior commit via Cloudflare Pages dashboard

### Critical Notes
- **Secret rotation:** Notify Kit immediately when Stripe, SendGrid, or Cloudflare keys rotate — these are env-var dependent on Railway (app) and Cloudflare Pages (marketing)
- **Database migrations:** Run via Railway CLI or Railway dashboard; always take a manual backup first (no automated DB backups from Kit yet — evaluate for Q3)
- **No Friday afternoon deploys** per `SYSTEM/DEVELOPMENT-STANDARDS.md`

---

## Monitoring & Alerting

| Property | Uptime Probe | Error Tracking | Performance | Status |
|----------|-------------|---------------|-------------|--------|
| app.trustoffice.app | Railway built-in health | To be added (Sentry candidate) | To be added | Partial |
| trustoffice.app | Cloudflare Pages | Cloudflare analytics | Lighthouse CI (evaluate) | Partial |

### Alerting Channels
- **Primary:** Discord (Kit's default reachability; Jeff checks there)
- **Secondary:** Email to jeff@socialize.video for P1s
- **P1 (site down):** Investigate within 5 minutes, notify Discord
- **P2 (degraded):** Investigate within 30 minutes, update LIVE-STATE.md
- **P3 (informational):** Log in daily notes, review weekly

**TODO:** Add Sentry to app.trustoffice.app. Add synthetic check for login + trust minutes generation.

---

## Customer Feedback Loop

### Channels
- **Support:** Email (TBD — currently handled by Jeff directly)
- **In-product:** Add a feedback widget (post GA) — evaluate Sentry's widget
- **Social mentions:** Kit monitors via X search; escalate if pattern emerges

### Bug Report Handling
- Acknowledge: Same-day in daily notes
- Reproduce: Kit reproduces or asks Jeff for details
- Fix: Path B (agent-driven) for clear root causes; pending_review for unclear
- Close loop: When fix ships, update post-log.md and notify Jeff

---

## Quality Gate — TrustOffice "Done" Overrides

The core `SYSTEM/DEVELOPMENT-STANDARDS.md` Quality Gate applies. TrustOffice adds these brand-specific checks:

- [ ] **Trust minutes generation tested end-to-end** — seed data → AI generation → PDF output → download works
- [ ] **Stripe checkout flow tested** — free tier, paid tier, coupon code (TRUST49)
- [ ] **Mobile responsiveness verified** — iPhone + Android, portrait + landscape
- [ ] **Accessibility pass** — axe-core on key pages (login, dashboard, trust minutes editor)
- [ ] **No AI slop in customer-facing copy** — reviewed with `humanizer` skill
- [ ] **Brand voice check** — professional, authoritative, warm (see BRAND-VOICE.md)
- [ ] **SEO elements verified** — meta title/description present, structured data if applicable

---

## Escalation Overrides (from `SYSTEM/OPERATING-MANUAL.md § Escalation`, originally `AGENTS.md (charter folded in)`)

The Charter's escalation list applies. TrustOffice-specific additions:

- **Stripe billing changes:** Always escalate to Jeff (money + customer trust)
- **Trust data handling / compliance:** Escalate (legal/regulatory sensitivity)
- **New integrations (calendar, email, etc.):** Jeff approves scope
- **Marketing site content deploys:** Kit deploys directly (within ownership)
- **App feature deploys:** Kit deploys directly for bug fixes; Jeff approves for new features

---

## Known Issues & Runbook Snippets

| Issue | Symptom | Resolution | Last Verified |
|-------|---------|-----------|-------------|
| SendGrid API key rotation | Emails fail silently in production | Update `SENDGRID_API_KEY` in Railway env vars, redeploy | 2026-04-29 |
| Cloudflare Pages build fail | Marketing site 404 or old version | Check build log in Cloudflare dashboard; fix Astro build errors | Ongoing |
| Trial removal (2026-04-29) | New signups → status "expired", plan "none" | By design — legacy users grandfathered, new users pay only | 2026-04-29 |
| OpenRouter metered spend spikes | Unexpected cost | Check ROUTER-RULES.md — default to flat-rate models, use OpenRouter only as override | 2026-04-30 |

---

## Changelog

| Date | Change | Trigger |
|------|--------|---------|
| 2026-04-30 | Standards file created | Kit Charter + development/reliability standards installed |
