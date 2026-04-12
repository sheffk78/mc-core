# Mission Control API — Kit Integration Guide

Base URL: `https://smartabodetechs.com/api/v1`

---

## Morning Brief

Kit writes a daily brief per brand that displays on the Mission Control Overview page when that brand is selected. Supports full markdown formatting.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/briefs/{brand-slug}` | Read the current brief for a brand |
| `PUT` | `/briefs/{brand-slug}` | Create or update the brief for a brand |

### PUT Body

```json
{
  "content": "## Good Morning, Jeff\n\n**Today's priorities for Agentic Trust:**\n\n- Review 3 pending email drafts\n- Follow up on partnership inquiry\n\n### Inbox Highlights\n\n- 2 new support tickets overnight\n- Investor update got 3 positive replies\n\n> Quote of the day here\n\n---\n\nLet me know if you want me to draft responses.",
  "updated_by": "kit"
}
```

### Fields

- `content` (required) — Full markdown text. Supports headings, bold, italics, bullet/numbered lists, blockquotes, horizontal rules, links, code, and emojis.
- `updated_by` — Who wrote it (default: `"kit"`)

### Brand Slugs

`agentic-trust`, `aav`, `safe-spend`, `arl`, `true-joy-birthing`, `trustoffice`, `wingpoint`, `anchorpoint`

### How It Displays

The brief renders on the Overview page when that brand is selected, with an "Updated today at 8:00 AM" timestamp. It replaces the top-left card on the Overview dashboard. When "All Brands" is selected, Open Tasks are shown instead.

---

## Schedule (Cron Jobs)

The Schedule module manages recurring jobs. Kit can create, list, update, pause/resume, and trigger jobs.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/schedule` | List all scheduled jobs |
| `POST` | `/schedule` | Create a new job |
| `PUT` | `/schedule/{id}` | Update a job |
| `DELETE` | `/schedule/{id}` | Delete a job |
| `PATCH` | `/schedule/{id}/pause` | Pause a job |
| `PATCH` | `/schedule/{id}/resume` | Resume a paused job |
| `POST` | `/schedule/{id}/run` | Trigger a job immediately |

### Create/Update Body

```json
{
  "name": "Daily inbox digest",
  "description": "Compile and send a summary of all unread emails",
  "cron": "0 8 * * *",
  "brand": "agentic-trust",
  "type": "cron",
  "action": "inbox_digest",
  "enabled": true,
  "config": {
    "inbox_id": "support@agentictrust.app",
    "send_to": "jeff@socialize.video"
  }
}
```

### Fields

- `name` (required) — Display name for the job
- `description` — What the job does
- `cron` (required) — Standard cron expression (e.g., `0 8 * * *` = daily at 8am, `*/30 * * * *` = every 30 minutes)
- `brand` — Brand slug this job belongs to
- `type` — Job type (e.g., `cron`, `webhook`, `email`)
- `action` — What to execute (free-form string, Kit defines the behavior)
- `enabled` — `true` or `false`
- `config` — JSON object with any job-specific parameters (flexible schema, Kit decides what goes here)

### Response

All endpoints return the job object with an `id` field that can be used for updates, pause/resume, and run-now operations.

---

## Tasks

Kit can also create and manage tasks that appear on the Kanban board.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tasks` | List all tasks (filter with `?brand=X&status=open`) |
| `POST` | `/tasks` | Create a new task |
| `PATCH` | `/tasks/{id}` | Update a task (status, notes, assignee, etc.) |
| `DELETE` | `/tasks/{id}` | Delete a task |

### Create Body

```json
{
  "title": "Review Q2 partnership proposal",
  "description": "The draft proposal from AcmeCorp is ready for review. Key points to check: pricing tier, SLA terms, and exclusivity clause.",
  "status": "open",
  "brand": "agentic-trust",
  "priority": "high",
  "assignee": "jeff",
  "due_date": "2026-04-10",
  "agent_note": "I've reviewed the initial terms and flagged 3 concerns in the description. Recommend requesting revised SLA before signing.",
  "metadata": {
    "agentmail_inbox_id": "support@agentictrust.app",
    "agentmail_thread_id": "thread_abc123",
    "reply_to_address": "partner@acmecorp.com",
    "send_method": "agentmail"
  }
}
```

### Task Statuses

`open` → `in_progress` → `approval` → `completed`

### Update Body (PATCH)

```json
{
  "status": "completed",
  "append_agent_note": "Email sent to partner@acmecorp.com at 2:30 PM MDT. Confirmation received."
}
```

- `append_agent_note` — Appends text to the existing agent note (does not replace it). Use this for logging actions taken.
- `user_note` — Jeff's notes (set by the UI, Kit can read but should not overwrite).
