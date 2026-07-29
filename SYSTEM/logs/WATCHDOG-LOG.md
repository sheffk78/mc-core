# WATCHDOG LOG — Stall Scans and Interventions
<!-- ROUTING: Log file — append-only, do not edit existing entries -->

_Last updated: 2026-04-24_

Append-only log of watchdog scans and any interventions Kit performs on stalled/failed jobs.

---

| timestamp | scan_type | jobs_checked | issues_found | action_taken | note |
|---|---|---|---|---|---|
| (no entries yet) | | | | | |
| 2026-04-27 17:13 | heartbeat_scan | 43 crons checked | 8 issues | tjb-crowdreply disabled (4 consec errors), others monitored | TJB CrowdReply 4x timeout (disabled per 3-error rule). WingPoint Monday 2x timeout, 6 others 1x each — monitoring. |
| 2026-07-16T12:12Z | cron_scan | 0 (API down) | 0 | none | MC Daily Cleanup: API DOWN (Railway 404). Local cleanup only. 74 briefs archived, 3 tasks archived, 1 stale checkpoint. |

---

## Scan Types

- **heartbeat_scan** — routine check during 55-min heartbeat
- **manual_scan** — Kit noticed something and checked proactively
- **cron_scan** — automated scan from a cron job

## Intervention Types

- **flag_stalled** — marked a job as stalled
- **escalate** — moved a job to failed/dead_letter
- **restart** — created a new job to replace a failed one
- **surface** — created a pending_review task for Jeff

---

## Cross-Agent Health

Inter-agent health checks (watcher → target → status). Merged from `CROSS-AGENT-WATCHDOG.md` on 2026-07-27.

| Timestamp | Watcher | Target | Status | Action | Notes |
|---|---|---|---|---|---|
| 2026-07-27 22:14:14 | Hermes | OpenClaw | healthy | none | Gateway responding on port 18888 |
| 2026-07-27 22:45:24 | Hermes | OpenClaw | healthy | none | Gateway responding on port 18888 |