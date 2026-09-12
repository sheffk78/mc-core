# Cron Alternative Decision Framework

> **MANDATORY:** Load this skill before creating ANY new cron job. No exceptions.
> If you're about to run `hermes cron create`, you must have already read this file
> and documented your alternative analysis in the cron prompt or a pending_review task.

## The Rule

**No cron job may run more than 3x/day unless it is a script-only (`no_agent=True`) infra monitor** (health checks, watchdogs, DB sentinels). This is a hard Jeff directive, not a guideline.

**No cron job may use `ollama-cloud` or any metered provider.** All crons must use `cron-orchestrator-v2:latest` on `ollama-local`. The sentinel flags provider drift.

## Decision Tree — Run Before Creating ANY Cron

```
Need: something happens periodically or on an event
│
├─ Is it triggered by an external event (new row, status change, message, error)?
│   ├─ YES → Use a WEBHOOK or EVENT LISTENER, not a cron
│   │         • Discord webhook (mention @Kit to trigger Hermes)
│   │         • TidyCal webhooks → eliminates polling
│   │         • GitHub webhooks → eliminates repo polling
│   │         • Railway deploy webhooks → eliminates deploy status polling
│   │         • API-internal event (post-save hook, DB trigger, FastAPI background task)
│   │
│   ├─ Is it business logic that runs on a schedule (process queue, check timeouts, send reminders)?
│   │   ├─ YES → Move to API-INTERNAL SCHEDULER (asyncio lifespan, APScheduler, Celery beat)
│   │   │         • The AeriusView API already does this — see app/scheduler.py
│   │   │         • TrustOffice/StenoDesk APIs can adopt the same pattern
│   │   │         • Benefits: zero token burn, zero external polling, instant startup, no cron tax
│   │   │
│   ├─ Is it a file/state change that needs announcing (city completed, deploy finished, training done)?
│   │   ├─ YES → PUSH NOTIFICATION from the process that completes the work
│   │   │         • Pipeline writes completion → fires Discord message directly
│   │   │         • Training script exits → posts to Discord (distillation-monitor.sh pattern)
│   │   │         • If push isn't possible → script-only cron (`no_agent=True`), max 3x/day
│   │   │
│   ├─ Is it genuine infrastructure monitoring (API health, DB connectivity, mail server)?
│   │   ├─ YES → Script-only cron (`no_agent=True`), every 30m minimum
│   │   │         • Must be silent on success (empty stdout = no delivery)
│   │   │         • Must post to ops channel only, never #general
│   │   │         • 48/day max (every 30m)
│   │   │
│   ├─ Is it content/research/SEO/outreach work that needs an LLM?
│   │   ├─ YES → Cron on `ollama-local` / `cron-orchestrator-v2:latest`, max 3x/day
│   │   │         • Must be pinned to ollama-local (NEVER ollama-cloud)
│   │   │         • Must deliver to brand channel or local, never #general for routine output
│   │   │         • Must have EMPTY-STOP rule: if 0 items, report "0 items" and stop
│   │   │
│   └─ None of the above? → Document in pending_review and ask Jeff
```

## Alternatives Quick Reference

| Need | Don't use cron. Use this instead. |
|---|---|
| React to new email/message/reply | Webhook or IMAP IDLE |
| React to new lead/route/status change | API-internal scheduler or DB trigger |
| React to contractor joining a metro | Event-driven ad trigger inside API |
| React to TidyCal booking | TidyCal webhook (not polling) |
| React to GitHub push/PR | GitHub webhook → Discord |
| React to Railway deploy status | Railway webhook or check on next API request |
| Process queued items on schedule | API-internal asyncio scheduler (see app/scheduler.py) |
| Announce task completion | Push from the completing process (Discord webhook) |
| Monitor API/DB/mail health | Script-only cron, every 30m, silent on success |
| Daily/weekly content drafts | Cron on ollama-local, 1-3x/day max |

## Pre-Flight Checklist (run mentally before every cron creation)

1. **Have I checked for a webhook alternative?** Document why webhook won't work.
2. **Have I checked if the API can do this internally?** Document why API scheduler won't work.
3. **Is this a script-only job?** If LLM is needed, justify why a script can't detect-and-defer.
4. **Frequency:** Will this exceed 3x/day? If yes, Jeff approval required.
5. **Provider:** Is it pinned to `ollama-local`? If `ollama-cloud`, stop immediately.
6. **Silence:** Will it stay silent when there's nothing to report?
7. **Delivery:** Is it going to the right channel (not #general for routine output)?

## The Sentinel

`~/.openclaw/workspace/SYSTEM/scripts/cron-sentinel.sh` runs 3x/day (8am, 2pm, 8pm) and:
- Flags any enabled job exceeding 3x/day
- Flags any job on `ollama-cloud` or any metered provider
- Flags any LLM job that should be `no_agent=True`
- Posts violations to #kit-ops (not #general)

## Pattern: detect-and-defer

The ideal cron is a cheap script that detects a condition and only triggers LLM work when there's something to act on:

```
Script runs (no_agent=True, every 30m)
  → Checks: are there new items? Is something stuck?
  → If NO: empty stdout → silent → zero cost
  → If YES: stdout → Discord delivery → @Kit mention → Hermes investigates
```

This pattern burns zero tokens on empty runs and only triggers LLM work when there's a real problem.

## File Locations

- Decision framework (this file): `SYSTEM/CRON-ALTERNATIVE-FRAMEWORK.md`
- Sentinel script: `SYSTEM/scripts/cron-sentinel.sh`
- Pre-flight gate: `SYSTEM/scripts/cron-preflight.sh`
- Registry of approved high-frequency jobs: below

## Documented alternative analyses (cron-allowed jobs, ≤3x/day)

| Job | Cadence | Why cron (not webhook/API-scheduler) | Type |
|---|---|---|---|
| TrustOffice Trustpilot Review Monitor | 1st & 15th monthly (09:07) | External site (Trustpilot) with no webhook/API on Kenneth's free plan; Enterprise-only API → CDP scrape via agent Chrome. Script-only, silent on no change. | no_agent=True, 2x/month |

## Approved High-Frequency Jobs (>3x/day)

Only script-only infra monitors may exceed 3x/day. All must be `no_agent=True`.

| Job | Frequency | Justification | Approved |
|---|---|---|---|
| TJB City Page Completion Monitor | every 30m (48/day) | Pipeline state polling, silent on no change | ✓ script-only |
| Ollama API Health Check | every 30m (48/day) | External service health, silent when healthy | ✓ script-only |
| session-token-watchdog | every 30m (48/day) | Independent runaway-LLM-session detector (reads state.db post-hoc; backstop for the 2026-09-11 74-call loop incident that burned 43.3M tokens). Silent on healthy (empty stdout = no Discord); alerts only to #openclaw on a stuck-retry signature. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| cc-note-flush | every 15m (96/day) | CC note funnel: batches queued task notes into ONE Discord message per brand (Jeff directive "work one at a time, I don't manage that"). Script-only httpx poster, zero LLM. Silent when queue empty. Built 2026-09-11. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| cc-cron-ingest | every 20m (72/day) | CC cron feed ingest: parses all enabled jobs' persisted output into feed.json (script-only, silent on no change). Command Center needs fresher-than-30m data for the attention queue. Built 2026-09-11. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| Ollama Model Health Check | every 15m (96/day) | Local model availability probe (script-only, silent when healthy). Faster detection than 30m because stuck-model states block 87 LLM cron fires/day. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| cross-agent-watchdog-openclaw | hourly (24/day) | Cross-agent heartbeat monitor, script-only, silent on healthy. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| TrustMinutes Site Health (watchdog) | hourly (24/day) | Site health monitor, script-only, silent on healthy. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| Mail Server Health Monitor | hourly (24/day) | Dovecot/SMTP health, script-only, silent on healthy. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| AeriusView Postgres Health Monitor | hourly (24/day) | DB health, script-only, silent on healthy. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| MLL Admin Message Check (Safety Net) | every 120m (12/day) | Admin inbox safety net, script-only. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| AeriusView SLA Monitor | every 2h (12/day) | Lead SLA timer checks, script-only. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| AeriusView Email Inbox Monitor | every 120m (12/day) | Inbox poll, script-only. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |
| AeriusView Reply Handler | 4x/day | Reply classification + auto-answer, script-only. | ✓ script-only, registered 2026-09-11 (approved in full-audit batch) |

Any addition to this table requires explicit Jeff approval.
## Approved High-Frequency Jobs

| Job | Frequency | Type | Justification | Added |
|---|---|---|---|---|
| stable-mail-weekly-sweep | 1x/week (Mon 09:00 MDT) | Script-only (no_agent=True) | Backstop for event-driven Stable mail pipeline: reconciles Stable API mail items vs local manifest; downloads any scans missed by webhooks (Svix retries exhausted / tunnel downtime). Silent on success (empty stdout), Discord #general only when discrepancy found. Not replacing the webhook — the webhook is primary. | 2026-09-07 |


### Approved: TrustOffice nightly DB backup (job 12a13dec9afa, 2026-09-11)
- **Type:** script-only (no_agent=True, zero LLM calls) — exempt from LLM cadence rules per Hard Rule 3.
- **Schedule:** 0 9 * * * (daily 09:00 UTC / 03:00 MDT, low-traffic window; spacing rule N/A — no LLM contention).
- **What:** nightly encrypted MongoDB backup -> Cloudflare R2 (30d retention) + Discord success/fail ping to #kit-email webhook (1530357644945129492).
- **Why cron is right:** no event source exists for "day rolled over"; webhook/API-internal scheduling not applicable to a standalone infra monitor. Script-only, silent on nothing-to-report.
- **E2E verified 2026-09-11:** dump 110MB -> age-encrypted 70MB -> R2 upload -> download -> decrypt -> mongorestore 9/9 docs verified.
