# OPENCLAW Routing and Task System

This document defines the operating system Kit should implement for OpenClaw so work does not disappear, routing is intelligent, and Mission Control can accurately reflect what the system is doing.

This plan is designed around the current OpenClaw setup: GLM as the primary interactive model, local Ollama workers, Moonshot Kimi, OpenRouter models including MiniMax and MiMo, Discord as the primary communication channel, existing brand state `.md` files, and a custom Mission Control interface.[cite:23][cite:24][cite:25][cite:47]

## Goals

The system must achieve five things:

- Keep Kit responsive in direct conversation while still delegating real work.
- Prevent work from silently disappearing or stalling.
- Route tasks to the right model lane based on task type, cost, urgency, and system health.
- Consolidate scattered model rules and operating instructions into one coherent execution system.
- Provide a clean source of truth that Mission Control can visualize consistently.[cite:47][cite:25][web:123]

## Non-goals

This implementation should **not** attempt to solve every security problem right now. Security should stay sensible and lightweight, but must not become so restrictive that it blocks execution. Over-hardening has already created friction and should be deferred until the workflow is reliable.[cite:47]

This implementation should also **not** try to use every available provider on day one. The first version should prioritize stability, task continuity, and observability over maximizing provider count.[web:124][web:125]

## Core Concepts

There are three core concepts in the new system:

1. **ACTIVE-TASK** — the one main thing Kit is currently advancing for a given conversation or workstream.
2. **JOB LEDGER** — the durable record of all spawned jobs, statuses, checkpoints, failures, and outputs.
3. **ROUTER** — the decision layer that chooses which model lane and concrete model should do a job.[web:124][web:125][web:123]

Everything else is built on top of these three concepts. Heartbeat, cron, Discord updates, Mission Control, and brand-state files should all plug into them rather than invent parallel systems.

## Existing Documents to Consolidate

OpenClaw already has multiple markdown sources of truth, including:

- Brand-specific state files.
- Model rules.
- Other operating instructions and process notes.
- Workspace memory files and notes.[cite:24]

These should not be deleted blindly. Instead, they should be restructured into a clearer hierarchy.

## File Structure

Kit should implement the following file structure inside the OpenClaw workspace:

```text
workspace/
  SYSTEM/
    OPENCLAW-ROUTING-AND-TASK-SYSTEM.md
    ACTIVE-TASK.md
    JOB-LEDGER.md
    ROUTER-RULES.md
    MODEL-RULES-CONSOLIDATED.md  # [Consolidated into ROUTER-RULES.md] — legacy
    OPERATING-RULES.md  # [Merged into AGENTS.md § Operating Rules, detail now in SYSTEM/OPERATING-MANUAL.md] — legacy
    DEAD-LETTER-QUEUE.md
    WATCHDOG-LOG.md
  TASKS/
    task-<job_id>.md
  BRANDS/
    <brand-name>.md
```

### Notes on file roles

- `ACTIVE-TASK.md` = current top-level work focus for Kit.
- `JOB-LEDGER.md` = lightweight ledger of all jobs and statuses.
- `ROUTER-RULES.md` = lane definitions, assignment rules, escalation logic.
- `MODEL-RULES-CONSOLIDATED.md` = one merged source replacing fragmented model docs. [Now consolidated into ROUTER-RULES.md]
- `OPERATING-RULES.md` = behavioral rules for Kit, subagents, and background jobs. [Now merged into AGENTS.md § Operating Rules, detail in SYSTEM/OPERATING-MANUAL.md § Operating Rules]
- `DEAD-LETTER-QUEUE.md` = failed jobs that need review or repair.
- `WATCHDOG-LOG.md` = simple append-only record of stall scans and interventions.
- `TASKS/task-<job_id>.md` = detailed checkpoint file for each major spawned task.
- `BRANDS/<brand-name>.md` = durable state files for each managed brand.

## Role of Brand State Files

The existing brand `.md` files matter and should remain part of the architecture. They are not replacements for task tracking, but they are durable context stores for each brand.

Use them like this:

- Brand files hold strategic state: current offers, campaigns, blockers, goals, channel notes, assets, recent wins/losses, and standing context.
- `ACTIVE-TASK.md` holds the current operating focus across the conversation or session.
- `JOB-LEDGER.md` holds execution state for spawned jobs.
- Individual task files hold step-by-step progress and outputs.

In other words:

- **Brand files = long-lived state by business/domain**
- **ACTIVE-TASK = current mission**
- **JOB LEDGER = operational execution record**
- **Task files = detailed run logs**

Kit must not confuse these layers.

## Communication Channels

Discord should become the primary communication channel. Slack should be removed from active use to reduce system complexity and split attention.

### Discord principles

- Direct interaction with the user should happen in Discord.
- Operational updates should go either to a dedicated Discord ops thread/channel or to Mission Control, not sprayed across multiple channels.
- Routine background noise should be minimized.

### Slack principles

- Slack should be disabled or left dormant until there is a specific reason to restore it.

## Mission Control Relationship

Mission Control should be treated as a separate but connected project. It must not become a second source of truth.

Mission Control should read from the task system and display:

- ACTIVE-TASK status.
- Current job queue.
- Running jobs.
- Stalled jobs.
- Dead-letter jobs.
- Current lane health.
- Current model assignments.
- Checkpoint timeline.

The source of truth should remain the workspace task files and ledger. Mission Control is the visual interface to those records, not an independent planning engine.[web:129][web:131][web:134]

## Operating Principle

Kit is not a single chat bot that keeps everything in short-term memory. Kit is a dispatcher-executor that must write durable records before and during meaningful work.

If work is important enough to take more than about 60 seconds, span multiple tools, or involve spawned subagents, it must become a tracked job.

## ACTIVE-TASK Discipline

`ACTIVE-TASK.md` should always exist and always be current.

It should contain:

- Title of the current mission.
- Why it matters.
- Success definition.
- Relevant brand or project.
- Current phase.
- Next action.
- Related job IDs.
- Risks or blockers.
- Last updated timestamp.

### ACTIVE-TASK rules

- There should be only one primary ACTIVE-TASK per conversation/workstream.
- If the user changes direction significantly, Kit should close or pause the current ACTIVE-TASK and create/update a new one.
- ACTIVE-TASK must be updated whenever a major phase changes.
- ACTIVE-TASK should reference brand state files when relevant.

## Job Ledger

`JOB-LEDGER.md` should be a concise operational ledger. It should be easy for Kit to edit and easy for Mission Control to parse.

### Required fields per job

Each job entry should contain:

- `job_id`
- `parent_active_task`
- `brand_or_project`
- `created_at`
- `updated_at`
- `priority`
- `task_type`
- `lane_requested`
- `lane_assigned`
- `model_assigned`
- `status`
- `retry_count`
- `owner`
- `checkpoint_summary`
- `output_path`
- `error_reason`

### Required statuses

Use only these statuses:

- `queued`
- `assigned`
- `running`
- `checkpointing`
- `waiting`
- `completed`
- `stalled`
- `failed`
- `dead_letter`
- `cancelled`

Do not invent synonyms like “in progress” or “paused maybe.” Use the defined status vocabulary consistently.

## Task Files

Every meaningful job should have its own file in `TASKS/`.

### Task file content

Each task file should include:

- Job metadata.
- Original objective.
- Inputs and links to relevant files.
- Chosen lane and model.
- Checkpoint log.
- Tool actions performed.
- Output summary.
- Handoff notes.
- Failure notes if applicable.

The task file is the durable narrative of the job. The ledger stays short; the task file carries the detail.

## Routing Architecture

Kit should route through **lanes**, not directly through raw providers unless a specific rule requires it.

### Initial lanes

Start with four lanes:

1. `interactive_main`
2. `worker_local`
3. `worker_paid`
4. `fallback_last`

Do **not** make free-provider orchestration the first implementation priority. Free-provider fan-out can be added as a later expansion after the base system is stable.[web:124][web:125]

### Lane definitions

#### `interactive_main`

Purpose:
- User-facing conversation.
- High-level planning.
- Final synthesis and major decisions.

Default model:
- `ollama/glm-5.1:cloud`.[cite:25]

Rules:
- Do not spend this lane on repetitive extraction, tagging, or rote formatting.
- Do not let long autonomous work live inline here if it can be delegated.
- If a task will take time, create a job and delegate.

#### `worker_local`

Purpose:
- Cheap, fast, background work.
- Extraction, chunking, note cleanup, prompt compression, lightweight summaries, routing prep.

Default model:
- `ollama/openclaw-qwen35-quick:latest` (“quick”).[cite:24]

Rules:
- Prefer this lane first for low-risk, repetitive work.
- Keep prompts scoped and compact.
- Use this lane to prepare context for stronger models.

#### `worker_paid`

Purpose:
- Quality-sensitive worker tasks.
- Coding subtasks.
- Important synthesis.
- Reviewer passes.
- Research branches where better quality matters.

Default models:
- `openrouter/minimax/minimax-m2.7`
- `openrouter/xiaomi/mimo-v2-pro`
- `moonshot/kimi-k2.6` after pathing is corrected.[cite:23][cite:31]

Rules:
- Use only when task value justifies paid inference.
- Reserve Anthropic models mostly for review, rescue, or exceptionally important outputs unless specific cost rules say otherwise.[cite:23]

#### `fallback_last`

Purpose:
- Degraded continuity when the preferred lane is unavailable or has failed repeatedly.

Rules:
- Better to produce a clearly marked degraded result than silently disappear.
- This lane should not become the main path.

## Model Mapping and Cleanup

The current config contains one probable inconsistency: Kimi is defined under Moonshot provider, but the alias points to an Ollama path. This should be corrected during implementation so aliases map to the real provider path.[cite:23]

Kit should create one consolidated model rules file that includes:

- Primary role of each model.
- Lane membership.
- Cost sensitivity.
- Quality profile.
- Escalation position.
- Review/rescue usage.

### Suggested model roles

- `glm` = primary interactive orchestrator.[cite:25]
- `quick` = default local worker for cheap utility tasks.[cite:24]
- `minimax` = paid worker for synthesis and execution.[cite:23]
- `mimo` = paid worker for quality-sensitive writing/coding tasks.[cite:23]
- `kimi` = specialist research/coding branch after alias/path correction.[cite:31]
- `haiku` = optional lightweight paid reviewer or overflow worker.[cite:23]
- `sonnet` = reviewer / stronger verifier.[cite:23]
- `opus` = exceptional rescue or highest-stakes review only.[cite:23]

## Task Classification Rules

Kit should classify tasks before routing them.

### Task classes

- `interactive_planning`
- `extraction`
- `summarization`
- `research_branch`
- `coding_subtask`
- `review`
- `brand_update`
- `cron_maintenance`
- `watchdog_intervention`
- `report_delivery`

### Default lane by task class

| Task class | Preferred lane | Notes |
|---|---|---|
| interactive_planning | interactive_main | Use GLM directly. |
| extraction | worker_local | Cheap and fast first pass. |
| summarization | worker_local -> worker_paid | Escalate only if quality matters. |
| research_branch | worker_paid | Can later expand to free lane. |
| coding_subtask | worker_paid | Use stronger worker. |
| review | worker_paid | Haiku/Sonnet style reviewer role. |
| brand_update | worker_local -> interactive_main | Draft locally, finalize at top level. |
| cron_maintenance | worker_local | Keep cheap and bounded. |
| watchdog_intervention | worker_local | Small deterministic ops work. |
| report_delivery | interactive_main | Final response voice and control. |

## Spawn Rules

Subagents are useful but must be governed.

### Spawn policy

- Spawn only when the task benefits from parallel or specialized work.
- Do not spawn simply because a task is hard.
- Every spawned subagent must correspond to a ledger job.
- Parent agent must record why the child exists.
- Parent must define the expected deliverable and stop condition.

### Initial practical limits

Keep current config limits, but add behavioral limits:

- Maximum of 3 meaningful concurrent child jobs for one ACTIVE-TASK unless the task is explicitly marked high-parallel.
- Use the existing configured concurrency, but avoid filling all slots casually.
- If quality coordination becomes harder than the work itself, reduce fan-out.

## Checkpoint Rules

Checkpointing is how Kit stops disappearing.

A checkpoint must be written when:

- A job starts.
- A major tool phase completes.
- A lane/model changes.
- A child job finishes.
- A blocker is discovered.
- The final output is produced.

### Checkpoint format

Each checkpoint should answer:

- What just happened?
- What is the current state?
- What is next?
- Is anything blocked?

Keep checkpoints short and concrete.

## Stall Detection and Watchdog

The watchdog should be simple, deterministic, and not depend on deep reasoning. It should read the ledger, apply rules, and write results.[web:126][web:118]

### Stall thresholds

Start with:

- Small utility/local jobs: stalled if no update in 90 seconds.
- Medium jobs: stalled if no update in 4 minutes.
- Long coding/research jobs: stalled if no update in 8 minutes.
- Parent jobs waiting on all children: stalled if all children are done and no parent resume checkpoint appears within 2 minutes.

### Watchdog actions

If a job is stalled:

1. Mark it `stalled` in the ledger.
2. Add an entry to `WATCHDOG-LOG.md`.
3. If retry count is below threshold, requeue it or escalate it.
4. If retry count is exhausted, move it to `dead_letter`.
5. Surface a concise alert to Discord or Mission Control if the job matters.

### Retry policy

- `worker_local`: up to 2 retries.
- `worker_paid`: 1 retry on alternate model, then fail visibly.
- `interactive_main`: do not silently retry complex user-facing work.
- Repeated failures should not loop forever.

## Dead Letter Queue

`DEAD-LETTER-QUEUE.md` should contain:

- Job ID.
- Original task.
- Last checkpoint.
- Failure reason.
- Retry history.
- Suggested next manual action.

Dead-letter jobs are not invisible failures. They are explicit unresolved work.

## Heartbeat Redesign

Heartbeat should no longer be the main mechanism for proving that Kit is alive. It should become a light monitoring/reporting layer only.[web:110][web:116]

### New heartbeat purpose

Heartbeat should report only on:

- Number of running jobs.
- Number of stalled jobs.
- Number of dead-letter jobs.
- Current ACTIVE-TASK.
- Any job exceeding defined SLA.
- Immediate blockers/opportunities.

### Heartbeat rules

- Prefer Discord or Mission Control over Slack.
- Do not repeat long summaries if nothing important changed.
- Heartbeat should summarize the task system, not substitute for it.

## Cron Redesign

Cron should trigger jobs, not perform large autonomous work directly.[web:109][web:112][web:115]

### Cron rules

- Each cron event should create a ledger job.
- The job should then be processed through the standard lane/task system.
- Cron work should be bounded and observable.
- If a cron job fails, it should retry according to policy and then dead-letter if needed.

### Suggested cron usage

Use cron for:

- Nightly memory maintenance.
- Watchdog scans if needed.
- Routine audits.
- Scheduled status refreshes.

Do not use cron for broad open-ended autonomous missions without job tracking.

## Discord Update Rules

Discord is the primary human-facing channel.

### Post to Discord when:

- A major task starts and is expected to take time.
- A major task completes.
- A meaningful blocker appears.
- A stalled job cannot self-recover.
- A dead-letter event needs human visibility.

### Do not post to Discord for:

- Every micro-checkpoint.
- Every tool call.
- Routine internal chatter.

## Consolidating Existing Rules

Kit should perform a consolidation pass over existing operating docs.

### Consolidation tasks

1. Inventory all current model-rule and instruction markdown files.
2. Identify overlaps, contradictions, and stale rules.
3. Merge model-specific guidance into `MODEL-RULES-CONSOLIDATED.md` [now ROUTER-RULES.md].
4. Merge generic behavior guidance into `OPERATING-RULES.md` [now SYSTEM/OPERATING-MANUAL.md § Operating Rules].
5. Keep brand-specific state in brand files.
6. Link all consolidated files from this system document.

### Important consolidation rule

Do not lose useful nuance during consolidation. Preserve important specialist instructions, but relocate them into the correct layer.

## Minimal Security Approach

Security should remain lightweight for now.

### Principles

- Do not add new restrictive guardrails unless there is a concrete pain point.
- Keep existing obvious high-risk command denials if already in place.
- Focus current effort on reliability, continuity, and visibility.
- Revisit stronger governance later after the workflow is stable.

## Implementation Plan for Kit

Kit should implement this in phases.

### Phase 1 — Foundation

1. Create `SYSTEM/`, `TASKS/`, and `BRANDS/` structure if missing.
2. Create or migrate `ACTIVE-TASK.md`.
3. Create `JOB-LEDGER.md` template.
4. Create per-task template in `TASKS/`.
5. Create `MODEL-RULES-CONSOLIDATED.md` [now ROUTER-RULES.md].
6. Create `OPERATING-RULES.md` [now SYSTEM/OPERATING-MANUAL.md § Operating Rules].
7. Correct Kimi pathing/alias inconsistency.

### Phase 2 — Operational behavior

1. Require tracked jobs for non-trivial tasks.
2. Add checkpoint-writing behavior to task execution.
3. Add status vocabulary enforcement.
4. Add simple watchdog script/process or equivalent deterministic routine.
5. Add `DEAD-LETTER-QUEUE.md` and `WATCHDOG-LOG.md`.

### Phase 3 — Routing intelligence

1. Implement lane-based routing rules.
2. Default cheap work to `worker_local`.
3. Escalate quality-sensitive work to `worker_paid`.
4. Keep `interactive_main` reserved for user interaction and synthesis.
5. Add simple retry and fallback behavior.

### Phase 4 — Channel and UI alignment

1. Remove or disable Slack from active workflow.
2. Move operational visibility to Discord + Mission Control.
3. Expose ledger and ACTIVE-TASK status cleanly for Mission Control.
4. Ensure Mission Control uses task records as source of truth.

### Phase 5 — Optional later expansion

1. Add `worker_free` lane for NVIDIA and similar providers.
2. Add lane-health scoring.
3. Add more sophisticated routing based on cost and reliability.
4. Add richer Mission Control analytics and lane health views.

## First Deliverables Kit Should Produce

Kit should produce these first:

- `SYSTEM/ACTIVE-TASK.md`
- `SYSTEM/JOB-LEDGER.md`
- `SYSTEM/MODEL-RULES-CONSOLIDATED.md` [now SYSTEM/ROUTER-RULES.md]
- `SYSTEM/OPERATING-RULES.md` [now SYSTEM/OPERATING-MANUAL.md § Operating Rules]
- `SYSTEM/logs/DEAD-LETTER-QUEUE.md`
- `SYSTEM/logs/WATCHDOG-LOG.md`
- One example file in `TASKS/`
- A short implementation note describing what was migrated and what still needs human input

## What the Human Must Provide

The human should provide only the minimum necessary inputs.

### Required human inputs

- Confirmation of the preferred paid-worker ranking among MiniMax, MiMo, and Kimi.
- Confirmation of which existing markdown files should be treated as authoritative if conflicts appear.
- Confirmation that Slack should be disabled from active workflow.
- Confirmation of which Discord thread/channel should receive operational updates.
- Confirmation of brand file locations if they are not already standardized.

### Optional human inputs

- Budget rules for when paid models may be used.
- Special handling for certain brands or clients.
- Mission Control design preferences for later visualization work.

Everything else should be set up by Kit as much as possible.

## Practical Behavioral Rules for Kit

Kit should follow these rules during implementation and operation:

- Never silently abandon a meaningful task.
- Never keep important task state only in chat context.
- Always create a job record before long or multi-step work.
- Keep ACTIVE-TASK current.
- Use the cheapest viable lane first unless quality or risk requires more.
- Escalate visibly rather than fail invisibly.
- Prefer clarity and durable written state over cleverness.
- Keep the system simple enough that Mission Control can explain it visually.

## Example Workflow

### Example: brand research task

1. User asks for a new strategic review for a brand.
2. Kit updates `ACTIVE-TASK.md`.
3. Kit creates a parent job in `JOB-LEDGER.md`.
4. Kit spawns 1–3 child jobs.
5. Child jobs use `worker_local` for extraction and `worker_paid` for higher-quality synthesis as needed.[cite:24][cite:23]
6. Each child writes checkpoints.
7. Parent job resumes, synthesizes, and delivers result through `interactive_main`.[cite:25]
8. Brand state file is updated if the result changes durable brand context.
9. Mission Control reflects the same state changes from the ledger.

## Final Principle

The system should feel like a visible workshop, not a disappearing magician.

Kit’s job is not merely to answer. Kit’s job is to keep work moving forward in a way that is durable, inspectable, and aligned with the real operating state of OpenClaw.
