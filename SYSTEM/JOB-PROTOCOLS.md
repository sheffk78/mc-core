# JOB PROTOCOLS — Lifecycle, Checkpoint, Watchdog, Subagents
<!-- ROUTING: Load before first task — job lifecycle, checkpoints, watchdog rules -->

_Load on demand: when starting a job, running checkpoints, doing heartbeat watchdog, or spawning subagents._

**Scope:** How Kit manages tracked jobs — lifecycle, checkpoints, watchdog, subagent orchestration. For the task execution loop (before/during/after any unit of work), see `WORK-PROTOCOL.md`.

---

## Job Lifecycle

1. **Classify** the task (see ROUTER-RULES.md)
2. **Route** to the appropriate lane
3. **Create** a job entry in `SYSTEM/JOB-LEDGER.md`
4. **Create** a task file at `SYSTEM/TASKS/task-<job_id>.md` for significant jobs
5. **Execute** on the assigned lane
6. **Checkpoint** — write progress to the task file at meaningful completion points
7. **Update** the ledger status as the job progresses
8. **Complete** — write output summary, update brand files if needed, mark job completed
9. **If stalled/failed** — update ledger, diagnose, retry or escalate to DEAD-LETTER-QUEUE

## Checkpoint Protocol

For any job that runs more than a few minutes:

1. Write a checkpoint to the task file at each meaningful completion point
2. Include: what was done, what's next, any blockers
3. Update the `checkpoint_summary` field in the ledger
4. If a subagent dies mid-task, the checkpoint is the recovery point

## Watchdog Protocol

Every heartbeat, Kit checks for stalled jobs:

1. Scan the ledger for jobs in `running` or `waiting` status
2. Any job with no checkpoint for >15 minutes → flag as `stalled`
3. Any job `stalled` for >30 minutes → move to `failed`, add to DEAD-LETTER-QUEUE
4. Log interventions in `SYSTEM/logs/WATCHDOG-LOG.md`

## Subagent Rules

- Subagents write to their own scratch files, never directly to ledger or brand files
- Kit orchestrates and merges subagent results at heartbeat or completion
- Subagents prepare, never send — all external actions go through Kit's approval gate
- Subagents get clear subtask + output contract + explicit max token budget
- Rate-limit spawns: 10-15s apart, check active count first, never retry timed-out spawns

## Verifying Subagent Output

Subagents can hallucinate or misunderstand. After delegation returns:
1. Read the output file(s) to verify they exist and are well-formed
2. Check for obvious errors (JSON parse failures, broken templates, missing sections)
3. If something looks wrong, re-delegate with more specific instructions or do it inline
4. For quality-sensitive content, run through humanizer before delivery