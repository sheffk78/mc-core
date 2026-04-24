# Mission Control Revamp Prompt for Kit

Kit,

Mission Control now needs to become the primary operating layer between the user and the work system. The old pattern — where the user drops work into Discord chat and expects you to mentally track it while also handling cron jobs, background work, and active requests — is no longer acceptable. It is causing overload, poor visibility, silent stalls, and the feeling that work disappears.

The new goal is this:

**Mission Control must become the main place where the user submits work, sees what is happening, understands what is blocked, and reviews what is complete.**

Discord should remain available for conversation, clarification, approval, feedback, and urgent interruption — but not as the primary intake mechanism for durable work.

You have full authority to redesign, rebuild, or fully replace Mission Control if needed to achieve this objective. Preserve what is useful, but do not preserve old structures just because they exist. The system should be rebuilt around clarity, task durability, and smooth communication with the user.

[cite:23][cite:24][cite:25][cite:47][cite:49][cite:97][cite:98]

## Core Objective

Build or rebuild Mission Control so that it does all of the following:

- Serves as the **primary task intake system** for meaningful user requests.
- Reflects the new task architecture already implemented: ACTIVE-TASK, JOB LEDGER, task files, routing lanes, watchdog, and dead-letter queue.
- Gives the user a real visual answer to: "What is Kit doing?", "What is waiting?", "What is blocked?", and "What finished?"
- Reduces the user’s need to manually manage projects, remember requests, or ask where work went.
- Helps you operate better by making state explicit and visible, rather than hidden in chat context.

Mission Control must behave like a dependable operations cockpit, not a decorative dashboard.

[cite:98][web:202][web:203][web:206][web:208][web:211]

## Product Philosophy

Design Mission Control around these principles:

1. **Tasks must be explicit.** If the work matters, it should exist as an object in the system, not only in chat.[web:202][web:203]
2. **Status must be visible.** The user should not need to ask where work is.[web:206][web:208]
3. **State must be durable.** Mission Control must read from the underlying task system, not guess based on chat history.[cite:24][cite:97]
4. **Communication must be structured.** The user should be able to submit ideas, feedback, direction, and approvals in a clean way.[web:205][web:211]
5. **The UI must match reality.** If a task is stalled, the dashboard must show it clearly. If work is done, it must be marked done. No optimism theater.[web:206][web:208]
6. **The system must help you think.** Mission Control is a tool for your own execution quality, not just a report surface for the user.[web:202][web:205]

## New Role of Mission Control

Mission Control is now responsible for four functions:

### 1. Task Intake

The user should primarily create real work through Mission Control.

Mission Control must support task submission for:
- New ideas
- Strategic direction
- Feedback on existing work
- Change requests
- New objectives
- Brand-specific asks
- Follow-up requests
- Review/revise tasks

Every meaningful input should become a structured task or update to an existing task.

[cite:97][web:182][web:191][web:198]

### 2. System Visibility

Mission Control must show:
- Current ACTIVE-TASK
- Queue of pending jobs
- Running jobs
- Waiting jobs
- Stalled jobs
- Dead-letter jobs
- Recently completed jobs
- Which lane/model is handling important work
- High-level system health

[cite:47][web:205][web:206][web:208][web:211]

### 3. Communication Bridge

Mission Control must become the clean bridge between the user and execution.

That means:
- The user gives objectives in Mission Control.
- You ask for clarification only when needed.
- The user can leave feedback on an active or completed task.
- Feedback should attach to the related task, not vanish into general chat.
- Discord is still available, but Mission Control should be the default durable communication layer for work.

[web:191][web:193][web:199]

### 4. Operational Control

Mission Control should allow the user to:
- Prioritize or deprioritize tasks
- Pause or cancel tasks
- Approve or reject major deliverables
- See blockers requiring human input
- Trigger retries on dead-letter items if appropriate

The user should not need to manage the whole system, but they should be able to steer it clearly.

[web:205][web:211][web:213]

## Source of Truth Rules

Mission Control must not become a second inconsistent memory system.

Use these rules:

- `ACTIVE-TASK.md` remains the source of truth for the current top-level mission.
- `JOB-LEDGER.md` remains the source of truth for task/job states.
- `TASKS/task-<job_id>.md` files remain the detailed checkpoint trail.
- Brand `.md` files remain the durable brand-state layer.
- Mission Control should read from and write to these structures in a clean, predictable way.

If Mission Control needs a more structured backend representation, you may build one, but it must remain tightly synced with these workspace records or explicitly replace them in a disciplined migration path.

[cite:24][cite:97][cite:98]

## UX Outcome Required

The user should be able to do this:

1. Open Mission Control.
2. Submit a new task, idea, correction, or objective.
3. See that work enter the system clearly.
4. Understand what you are doing without asking in Discord.
5. See whether work is queued, active, waiting, blocked, stalled, or done.
6. Review the result in context.
7. Give feedback directly on the task.
8. Trust that the system is moving work forward even when they are not chatting with you.

If the user still feels the need to ask "where are you?" or "are you still working on this?" then Mission Control has failed.

[web:202][web:206][web:208]

## Required Mission Control Features

### Task Inbox / Intake Form

Create a clear intake mechanism.

Each new task should support fields such as:
- Title
- Brand / project
- Type (idea, request, feedback, bug, review, objective, maintenance)
- Priority
- Desired outcome
- Optional deadline or urgency
- Supporting notes/files
- Whether it is a new task or feedback on an existing task

The intake should be fast and not feel bureaucratic. Simplicity matters.

[web:202][web:203][web:211]

### Kanban or Status Board

Mission Control should have a clear visual task board. At minimum, show these columns:
- Inbox
- Queued
- Active
- Waiting
- Review
- Completed
- Stalled
- Dead Letter

If you choose a different visual layout, it must still preserve this clarity.

[web:202][web:203][web:211][web:212]

### Live Activity Feed

Add a real-time or near-real-time feed showing meaningful events, such as:
- Task created
- Task assigned
- Model/lane selected
- Checkpoint written
- Tool run finished
- Task stalled
- Task retried
- Task completed
- Feedback added

Do not flood the feed with useless noise. It should be useful, legible, and confidence-building.

[web:202][web:205][web:206]

### ACTIVE-TASK Panel

Create a prominent panel showing:
- Current top-level mission
- Why it matters
- Current phase
- Next action
- Main blockers
- Related task IDs

This should help the user orient immediately.

[cite:97][cite:98][web:208]

### Blockers and Needs-Input View

Create a dedicated way to show what needs the user’s attention.

Examples:
- Missing clarification
- Approval required
- Credentials/API key needed
- Conflicting instructions
- Failed task needing decision

The system should make human intervention precise, not vague.

[web:205][web:208]

### Review and Feedback Loop

Users must be able to comment on work and have that feedback attach directly to the relevant task or deliverable.

Feedback should be treated as one of three things:
- Minor adjustment to an active task
- Reopen or revise completed task
- New follow-on task

Do not let feedback become a disconnected chat message.

[web:191][web:198][web:210]

### System Health View

Show at least a lightweight version of:
- Active jobs count
- Stalled jobs count
- Dead-letter count
- Queue depth
- Lane usage by type
- Current gateway / worker health if available

This is not for vanity metrics. It is to help both you and the user trust the system.

[web:205][web:206][web:207]

## Routing and Lane Visibility

Mission Control should help make the new routing system understandable.

For important tasks, show:
- Requested lane
- Assigned lane
- Model used
- Why it was chosen, if useful

You do not need to expose every internal implementation detail, but the user should be able to understand the broad logic: local worker, monthly-included worker, paid overflow, fallback, etc.

[cite:23][cite:24][cite:25][web:206][web:207]

## Updated Lane Assumptions

Use the latest model assumptions:

- GLM remains the primary interactive orchestrator.[cite:25]
- Quick remains a cheap utility/background worker.[cite:24]
- Kimi is **not** to be treated as a metered paid luxury worker. Kimi is part of the monthly Ollama plan and should handle a meaningful share of heavy execution work, especially research/coding style worker tasks.[cite:23][cite:31]
- OpenRouter metered models should be used selectively for quality-sensitive overflow, external validation, or reviewer roles.[cite:23]

Mission Control should reflect this updated reality so the system does not misleadingly present Kimi as an expensive edge case when it is actually part of the core worker pool.

## Discord’s New Role

Discord is no longer the main intake system for durable work.

Use Discord for:
- Clarification questions
- Fast strategic discussion
- Human approvals
- Urgent interruptions
- Concise milestone updates

Do not rely on Discord as the place where large tasks begin and remain tracked.

If a meaningful task starts in Discord, convert it into a Mission Control task or ask the user for a quick confirmation to create one.

[web:182][web:191][web:193][web:199]

## Build Freedom

You are authorized to make major changes, including:
- Full UI redesign
- Data model redesign
- New backend structures
- Rewritten task flows
- New views, panels, and controls
- Removal of old Mission Control features that no longer serve the objective

Do not preserve legacy structure at the cost of clarity.

## Delivery Requirements

Please approach this as an implementation project with phases.

### Phase 1 — Diagnose and map

Produce a short assessment of the current Mission Control system:
- What parts are useful
- What parts are misleading or insufficient
- What currently does not map to the new task architecture
- What should be preserved, changed, or removed

### Phase 2 — Design the new operating model

Define:
- Mission Control information architecture
- Primary screens/panels
- Task intake flow
- Task lifecycle visualization
- Feedback loop design
- How Mission Control syncs with the underlying task records

### Phase 3 — Implement the revamp

Build the upgraded Mission Control system.

### Phase 4 — Validate against real use

Test the result against realistic scenarios:
- New task intake
- User feedback on active work
- Task stalls
- Dead-letter events
- Cron-created work
- Research task with multiple worker jobs
- Brand-specific work updates

### Phase 5 — Refine until it actually reduces babysitting

If the system still makes the user ask where work is, keep refining.

## What Success Looks Like

Success is not “a prettier dashboard.”

Success is when:
- The user enters work through Mission Control by default.
- The user can see what is happening without asking.
- You are less overloaded because work is structured instead of scattered.
- Feedback becomes part of the work system instead of getting lost in chat.
- Mission Control and the underlying task system stay in sync.
- The user trusts that work continues even when they are not actively chatting with you.

[web:202][web:205][web:208][web:211]

## Final Instruction

Take ownership of this project. Treat Mission Control as a tool you are building for yourself and for your working relationship with the user.

The objective is not to preserve the old Mission Control.
The objective is to create the Mission Control that should have existed all along.
