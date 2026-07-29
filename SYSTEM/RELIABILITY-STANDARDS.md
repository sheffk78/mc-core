# Kit Reliability Standards
<!-- ROUTING: Monitoring and incident response rules -->

**How you keep things running. How you find problems before users do. How you respond when something breaks.**

Read alongside the Charter (`SYSTEM/AGENTS.md (charter folded in)`). Where this and the Charter conflict, the Charter wins.

---

## What "Always Working" Requires

Every public-facing site and tool has, at minimum:

- **Uptime monitoring** — external probe every 1 minute, multi-region
- **Error tracking** — JavaScript errors and server exceptions captured with stack traces and user context
- **Performance monitoring** — real-user metrics (LCP, INP, CLS) and synthetic Lighthouse runs
- **Log aggregation** — application and access logs centralized and queryable for at least 30 days
- **Synthetic checks** for the highest-stakes user flows (login, checkout, contact form, search) running every 5–15 minutes
- **Alerting** — actionable alerts to a channel you check, with severity levels

If any of these is missing for any property, that is a Kit task. Add it.

---

## Alerting Discipline

Alerts must be actionable or they are noise.

- **P1 — site or core flow down.** Immediate. Acknowledge within 5 minutes. Stabilize fast.
- **P2 — degraded but functional.** New error spike, slow page, partial failure. Investigate within 30 minutes.
- **P3 — informational.** Trend worth knowing. Review on the next routine sweep.

Tune aggressively. A noisy alert is worse than no alert because it trains you to ignore it. **If an alert fires three times for the same root cause, fix the root cause or fix the alert.** No exceptions.

---

## Routine Sweeps

### Daily (automated where possible)

- Review error tracking for new error types or spikes
- Confirm uptime is at target across all properties
- Check Core Web Vitals for regressions on each property
- Scan dependency security alerts (Dependabot, Snyk, etc.)

### Weekly

- Review the slowest pages and slowest queries
- Audit feature flag state — close out flags that should be retired
- Review customer feedback channels for patterns
- Confirm backups are running and that recent ones exist

### Monthly

- Restore-test at least one backup to a scratch environment
- Review SSL/TLS expirations, domain renewals, API key ages
- Audit alerting rules — what fired, what did not, what was noise
- Update dependencies (security patches always; major versions on a controlled cadence)
- Review uptime and error trends quarter-over-quarter

---

## Incident Response

When something breaks:

1. **Acknowledge.** Mark the alert and start a working channel or thread. The clock is running.
2. **Stabilize first, diagnose second.** If a rollback restores service, roll back. Diagnosis happens after users are unblocked.
3. **Communicate externally if user-visible.** Post a status update where customers will look (status page, social, email — whatever fits the property). Update at meaningful intervals, not on a clock.
4. **Fix forward only after stabilizing.** Apply the real fix once the bleeding has stopped, with the same testing rigor as any other change.
5. **Postmortem.** Within 48 hours of any P1 or recurring P2:
   - Timeline of what happened
   - Root cause, including process causes — not only code
   - What we did about it
   - What changes prevent recurrence — and the standards-document update those changes imply

Postmortems are blameless and concrete. *"Move faster"* is not an action item. *"Add a synthetic check for the password reset flow that runs every 5 minutes and pages on failure"* is.

---

## Customer Feedback Loop

Every channel where customers report bugs or give feedback (support inbox, in-product feedback widget, social mentions, app store reviews) is monitored.

### For incoming bug reports

- **Acknowledge** within 1 hour during business hours, within 24 hours otherwise
- **Reproduce** or request reproduction details. No fix without reproduction.
- **Triage** by severity — is the customer blocked, frustrated, or sharing?
- **Fix** or write a clear timeline. Customers care most about being heard and having a date.
- **Close the loop.** When the fix ships, tell the customer who reported it.

### For incoming feature requests and feedback

- Capture them in a single place (issue tracker, board, doc — whatever the team already uses)
- Look for patterns. Three customers asking for the same thing is a signal; one is a data point.
- Do not promise. Track and prioritize.

---

## Onboarding a New Property

When a new site, app, or tool comes under our roof, before it is considered production-ready:

- Uptime, error, and performance monitoring are wired up
- Synthetic checks cover the top one or two user flows
- Backups are configured and one restore test has been run
- A page in the issue tracker exists for known issues and roadmap
- A status page or status communication channel is identified
- The Quality Gate from the development standards has been satisfied for the current state

---

## Continuous Improvement

The bar moves up over time. Every quarter:

- Pick the metric that most matters for each property — uptime, p95 latency, conversion rate, error budget — and try to move it
- Retire the slowest, jankiest, lowest-value parts of the codebase you keep tripping over
- Reread these documents. Anything that has not been useful gets cut. Anything missing gets added.

---

## Hermes Integration Notes

- **Job tracking is mandatory.** Per `AGENTS.md`, anything >60s becomes a tracked job in `SYSTEM/JOB-LEDGER.md`.
- **Site health checks** are part of the heartbeat cycle. The `site-health` skill should be loaded for routine sweeps.
- **Customer feedback** from Brand Slack and Discord channels is captured via the respective social skills (`x-posting`, `crowd-reply`, etc.).
- **Postmortem findings** should be added to `SYSTEM/OPERATING-MANUAL.md § Operating Rules` or `SYSTEM/MC-OPERATING-RULES.md` as appropriate, with a dated changelog entry.

---

## Changelog

*(empty — append entries as standards evolve)*
