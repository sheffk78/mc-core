# Mission Control Revamp — Design Document

_Created: 2026-04-24 | Author: Kit | Status: Phase 1 → 2 (Design locked, implementing)_

## The Problem

1. **Discord is not a task system.** Jeff drops tasks in 3-4 different channels. They scatter. Kit can't track them. Work disappears.
2. **MC is a passive dashboard.** It shows data but doesn't drive execution. Kit doesn't pull work from it. Jeff can't see what Kit is doing.
3. **No intake.** There's no clean way for Jeff to say "do this" and have it show up as actionable work.
4. **No lifecycle.** Tasks get created and sit in "open" forever. No blocked state, no parent/child, no feedback loop.
5. **The "where is Kit?" problem.** Jeff wakes up to failures and has no visibility into what happened, what's queued, or what's stuck.

## The Solution

### Two Core Views

**1. Kit Command Center** (Kit's primary workspace — replaces the old Dashboard Overview)
- What am I working on right now? (ACTIVE-TASK panel)
- What's queued next? (ordered priority queue)
- What's blocked waiting on Jeff? (blocked items, clearly labeled)
- What just completed? (recent completions feed)
- System health: jobs, crons, model costs

**2. Jeff Intake** (Jeff's primary view — replaces Jeff Queue)
- Fast task submission form (title, brand, priority, notes — done in 10 seconds)
- "Needs Jeff" queue: approvals, pending reviews, blocked items
- "Kit is working on" feed: in-progress tasks with last checkpoint
- Feedback thread on any task (not lost in Discord)

### Data Model Changes

Add to the `tasks` table:
- `blocked_on` (text) — what this is waiting for and who needs to act
- `parent_task_id` (text, FK → tasks.id) — for subtasks
- `source` (text) — where did this come from? "discord", "mc_ui", "cron", "kit_proactive"
- `lane` (text) — which routing lane: "interactive_main", "worker_production", "worker_local"
- `checkpoint_summary` (text) — latest progress note
- `checkpoint_at` (text) — when last checkpoint was written

Add a `task_comments` table:
- `id`, `task_id`, `author` (kit/jeff), `content`, `created_at`
- This is the feedback loop. Both Kit and Jeff can comment.

Add a `task_status_history` table:
- `id`, `task_id`, `from_status`, `to_status`, `changed_by`, `changed_at`
- Audit trail of every status change.

### Task Lifecycle

```
new → open → in_progress → pending_review → completed
                ↓                ↓
              blocked          revisions (reopens to in_progress)
                ↓
           completed (after unblock)
```

- `blocked`: Something external is needed. Shown prominently to Jeff.
- `pending_review`: Kit finished. Jeff reviews and approves or sends back.
- `revisions`: Jeff wants changes. Reopens to `in_progress`.

### Discord → MC Bridge

When Jeff sends a message in Discord that looks like a task request:
- Kit creates an MC task with `source: "discord"` and links back to the message
- Kit replies in Discord with "Created MC task [id] — I'll handle this"
- Kit then works from MC, not from Discord memory

This is the key behavioral change. Discord becomes for conversation, MC becomes for work.

### New API Endpoints

- `POST /api/v1/tasks/:id/comments` — Add a comment to a task
- `GET /api/v1/tasks/:id/comments` — Get comments for a task
- `GET /api/v1/tasks/:id/history` — Get status change history
- `PATCH /api/v1/tasks/:id` — Already exists, add support for new fields
- `GET /api/v1/tasks?status=blocked` — Filter by blocked status
- `GET /api/v1/tasks?assignee=kit&status=in_progress` — Kit's active work

### New Frontend Views

1. **KitCommandCenter.tsx** — Kit's workspace
   - Active mission panel (from ACTIVE-TASK)
   - Priority queue (next 5 tasks)
   - Blocked items needing Jeff
   - Recent completions
   - System health bar
   
2. **JeffIntake.tsx** — Jeff's workspace (replaces JeffQueue)
   - Quick add task form (always visible, not buried in a modal)
   - "Needs You" column (approvals + blocked items + pending reviews)
   - "Kit's Working On" column (in_progress tasks with checkpoints)
   - "Done" column (recently completed)

3. **TaskDetailModal.tsx** — Enhanced with comments thread
   - Add comment input at bottom
   - Show comment history
   - Show status change history

### Implementation Order

1. ✅ Schema migration (add new columns + task_comments + task_status_history)
2. ✅ API endpoints for comments and history
3. ✅ Update task routes to handle new fields
4. ✅ JeffIntake view with quick-add form
5. ✅ KitCommandCenter view
6. ✅ Enhanced TaskDetailModal with comments
7. ✅ WebSocket events for real-time comments
8. ✅ Update AGENTS.md with MC-first workflow rules

### What Success Looks Like

- Jeff opens MC, types a task, hits enter. It shows up. Kit starts working.
- Jeff can see exactly what Kit is doing and what's blocked.
- Kit pulls work from MC, not from Discord.
- Feedback stays attached to tasks.
- No more "where is Kit?" questions.