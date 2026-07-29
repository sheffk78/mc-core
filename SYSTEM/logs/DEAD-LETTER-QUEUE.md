# DEAD LETTER QUEUE — Failed Jobs Needing Review
<!-- ROUTING: Log file — append-only, do not edit existing entries -->

_Last updated: 2026-04-24_

Jobs that have failed after retries and need human intervention or diagnosis.

---

| job_id | original_task | failed_at | error_reason | retry_count | last_action | next_step |
|---|---|---|---|---|---|---|
| (none yet) | | | | | | |

---

## Protocol

1. Jobs enter DLQ when: `failed` status + retries exhausted (≥2 attempts)
2. Kit reviews DLQ at each heartbeat
3. If Kit can diagnose and fix → create a new job, reference the DLQ entry
4. If Kit cannot fix → surface to Jeff via pending_review task
5. DLQ entries are never deleted — they are the audit trail of what went wrong