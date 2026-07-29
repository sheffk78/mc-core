# Kit Toolbox
<!-- ROUTING: Load when selecting tools — suggested tools by purpose with selection criteria -->

**Suggested tools by purpose. You — Kit — pick. These are starting points based on what is currently mature and well-suited for an AI-driven workflow.**

When you swap a tool, note it in the changelog with a brief reason.

---

## Browser automation (human-simulation testing)

- **Playwright** — default. Fast, multi-browser, excellent CI story, strong AI-agent ergonomics.
- Cypress — acceptable alternative, especially where already in use.
- Puppeteer — when only Chrome is needed and minimal setup wins.

## Unit and integration testing

- **JS/TS:** Vitest (preferred for new), Jest
- **Python:** pytest
- **Ruby:** RSpec, Minitest
- **PHP:** PHPUnit, Pest

## Visual regression

- Chromatic (great with Storybook)
- Percy
- Applitools (most powerful, paid)
- Playwright's own screenshot diff for lighter cases

## Accessibility

- **axe-core** — runs inside Playwright, default for automated checks
- Pa11y — CI-friendly
- Lighthouse a11y audit — quick complement
- Manual NVDA / VoiceOver pass for critical flows on high-stakes properties

## Performance

- **Lighthouse CI** — block PRs that regress Core Web Vitals
- WebPageTest — deeper one-off analysis
- Cloudflare or Vercel Web Analytics — RUM with negligible script weight

## Code quality

- **JS/TS:** Biome (fast single binary) or ESLint + Prettier
- **Python:** Ruff (fast, comprehensive) + Black
- **Type checkers:** TypeScript, Pyright, mypy
- **Security:** Snyk, Socket, Dependabot, GitHub CodeQL

## Subagent code review

You can spawn subagents for adversarial code review via `delegate_task`. Each subagent gets the diff and an adversarial prompt: *"Find what is wrong with this diff."* Multiple subagents with different framing (risk-first, opportunity-first, feasibility-first) provide perspective diversity.

## Error tracking

- **Sentry** — default. Strong DX, excellent JS + backend support, source maps, user feedback widget.
- Bugsnag, Rollbar — credible alternatives.

## Uptime + synthetic monitoring

- **Better Stack** (formerly Better Uptime) — modern, status pages included
- Checkly — particularly strong if you want Playwright-based synthetic checks
- UptimeRobot — free tier good for low-stakes properties
- Pingdom — enterprise-grade

## Logs

- Better Stack Logs, Axiom, Datadog Logs, Logtail
- Cloud-native (CloudWatch, Stackdriver) where the stack already lives there

## Real-user monitoring (RUM)

- Sentry Performance, Datadog RUM, Vercel Analytics, Cloudflare Web Analytics

## Session replay (use with privacy care)

- PostHog (open-source friendly), FullStory, LogRocket, Hotjar
- Always mask PII; respect user privacy settings and applicable law

## Feature flags

- PostHog (open-source option), LaunchDarkly, Statsig, Flagsmith, Unleash

## CI/CD and preview environments

- GitHub Actions (default for most stacks), CircleCI
- Vercel, Netlify, Cloudflare Pages, Render — all give per-PR preview URLs out of the box

## Customer feedback / support

- Linear (engineering issues), Plain or Intercom (support), Sentry user-feedback widget for bug reports tied to errors
- Canny or Productboard for feature requests at scale

## Status pages

- Better Stack, Statuspage by Atlassian, Instatus

---

## Selection Criteria When You Swap

When you replace a tool:

1. **Why was the old one insufficient?** A specific gap, not a vibe.
2. **What does the new one do better?** Concrete capabilities or measurements.
3. **What is the migration cost, and is it worth it?**
4. **Is it boring?** Prefer mature, widely-used tools over shiny ones for anything load-bearing.

---

## Hermes Integration Notes

- **Tool invocation details** live in `TOOLS.md` (the index), not this file. Use this file for selection decisions; use `TOOLS/*.md` for invocation commands.
- **Secrets management** follows `TOOLS.md` Rule 2: credentials live in 1Password (vault: "OpenClaw") or `~/.hermes/secrets/` — never hardcoded.
- **Cost discipline** — see `SYSTEM/ROUTER-RULES.md` for current model configuration and cost details.
- **Tool swaps** above $50/month require escalation per the Charter's "Money in a new vendor relationship" rule.

---

## Installed Applications

| App | Purpose | Installed | Notes |
|---|---|---|---|
| **Observer AI** (v2.4.1) | Persistent local-LLM screen/audio observation agent — watches for conditions and notifies via Discord/Telegram/email. Runs as menu-bar app, zero API cost for simple monitoring loops. | 2026-06-22 | AGPLv3. Not a Hermes skill — standalone Electron app. Useful as cheap sensor layer for high-frequency screen checks, but no native bridge to Hermes. Limited to sandboxed JS agents. Not worth wiring up unless a specific high-frequency monitoring need arises. |

## Changelog

| Date | Change |
|---|---|
| 2026-06-22 | Added Observer AI (v2.4.1) — installed as menu-bar app for local-LLM screen/audio monitoring |
| 2026-06-30 | Google Workspace OAuth completed for jeff@socialize.video. Full access: Gmail, Calendar, Drive, Sheets, Docs, Contacts. All APIs enabled and verified. See TOOLS.md Rule 7a. |
