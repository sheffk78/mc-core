# Cron 3x/day rule — full audit (2026-09-11 ~18:35 MDT)

**Kenneth's frustration (msg 1548130473220513835):** "hard rule: no cron job will run more than 3x per day. If this is continuing to happen, I don't understand why."

## Audit result (all 164 enabled jobs)

| Category | Count | Rule status |
|---|---|---|
| Script-only jobs >3x/day | 13 | Only 3 are registered in the approved table; **10 unregistered** |
| LLM jobs >3x/day | **1** | VIOLATION of Hard Rule 2 |
| Total LLM cron fires/day | 87 across 80 jobs | — |

## LLM violations (>3x/day on a model)

1. **TJB Autonomous City Worker — Eligible Queue Items Only** (job 1084dbb6ff47): `25 10-17 * * *` = 8 fires/day, ollama-local, deliver local, last run ok 18:18 today.
   - Pre-dates today; not created in this session. Silent-on-no-change city pipeline worker.
   - Options: (a) reduce to 3x/day, (b) convert to script-only worker (city eligibility check is deterministic DB logic; the LLM only writes the outreach), (c) register in approved table.

## Script-only >3x/day — unregistered (10)

| Job | Fires/day | Note |
|---|---|---|
| cc-note-flush | 96 (every 15m) | CC note funnel, shipped 2026-09-11 with Kenneth's approval in that task's thread |
| Ollama Model Health Check | 96 | infra health |
| cc-cron-ingest | 72 (every 20m) | CC cron feed, shipped 2026-09-11 |
| cross-agent-watchdog-openclaw | 24 | infra watchdog |
| TrustMinutes Site Health (watchdog) | 24 | site monitor |
| Mail Server Health Monitor | 24 | infra |
| AeriusView Postgres Health Monitor | 24 | infra |
| MLL Admin Message Check (Safety Net) | 12 | |
| AeriusView SLA Monitor | 12 | |
| AeriusView Email Inbox Monitor | 12 | |
| AeriusView Reply Handler | 4 | |

Registered in approved table: TJB City Page Completion Monitor (48), Ollama API Health Check (48), session-token-watchdog (48, added 2026-09-11).

## Root cause of "continuing to happen"

The framework's own text carves out script-only monitors ("every 30m minimum, 48/day max") for infra monitors — Kenneth's 3x/day hard rule as stated in Discord doesn't mention that carve-out, but the framework Jeff approved does. The gap is **registration discipline**: monitors were created under the script-only carve-out but never added to the approved table, so the table stopped reflecting reality, and today Kit added a new job (watchdog) under the carve-out without registering it either. Same failure mode repeating.

## Fix proposal (needs Kenneth's decision)

1. **Register all 10 existing script-only monitors** in the approved table with justifications (they're all silent-on-healthy infra checks, zero LLM cost) — OR cull any Kenneth doesn't want.
2. **TJB City Worker:** pick reduce-to-3x / convert-to-script / register.
3. **Registration discipline gate:** cron-preflight.sh gains a check — any new script-only job with cadence >3x/day is BLOCKED unless its name is already in the framework table; adding a row = file edit in the same commit as the cron creation.