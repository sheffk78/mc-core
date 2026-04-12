# Mission Control — PRD

## Problem Statement
Build a "Mission Control" dashboard — a human oversight app for managing AI agent tasks across multiple brands. Editorial aesthetic.

## Architecture
- FastAPI + MongoDB + React + WebSocket at `/api/v1/ws`
- All endpoints at `/api/v1/`
- Background: AgentMail auto-sync (120s), Task auto-archive (hourly, 7-day rule)
- **Modular backend** (refactored Apr 1, 2026):
  - `server.py` (281 lines) — orchestrator, lifecycle, WebSocket, background tasks
  - `db.py` — MongoDB client, WebSocket manager, AgentMail config, helpers
  - `models.py` — all Pydantic models
  - `seed.py` — seed data and database seeding
  - `routes/tasks.py` — Tasks + Action-Items CRUD
  - `routes/approvals.py` — Approvals CRUD
  - `routes/schedule.py` — Schedule/Cron CRUD
  - `routes/agentmail.py` — AgentMail inboxes, compose, reply, webhooks, brand-map
  - `routes/users.py` — Users + Agents CRUD
  - `routes/brands.py` — Brands CRUD
  - `routes/calendar.py` — Google Calendar via Service Account (no OAuth redirects)
  - `routes/activity.py` — Activity feed
  - `routes/templates.py` — Email templates
  - `routes/stats.py` — Stats, seed, health, inboxes

## What's Been Implemented

### Core Modules (8 views)
- **Overview**: Stats, summaries of all modules, **Morning Brief** (per-brand, written by Kit via `PUT /api/v1/briefs/{brand}`, read-only markdown display with date stamp — replaces Approvals when brand selected)
- **Approvals**: Email drafts + task approvals, search/filter, approve/reject/discard
- **Tasks (Kanban)**: 4 columns (Open → In Progress → Approval → Completed), drag-and-drop, task detail dialog, assignee filter, due dates, priority
- **Inboxes**: AgentMail (5 inboxes, compose, reply, threads, search)
  - **Thread-based view** (Apr 4, 2026): one line per thread, click to see full email trail
  - Auto-mark-read when clicking into a thread (unread dot removed)
  - Unread dot only reappears when someone replies to the thread
  - **Draft support**: Kit writes drafts via API (labeled "draft"), shown with amber DRAFT header, user can edit + send
  - **Sent badge**: thread shows blue "Sent" badge when latest message was sent
  - **Draft badge**: thread shows amber "Draft" badge when Kit has drafted a reply
  - Collapsible message accordion in thread view (latest auto-expanded)
  - Tabs: All / Received / Sent
  - Search filters threads by subject, sender, or text
- **Schedule**: Cron job management (CRUD, pause/resume/run-now)
- **Calendar**: Google Service Account integration (read + write, weekly grid, event creation) — no OAuth redirect needed
- **Activity Feed**: Real-time event log
- **Settings**: Users & Agents CRUD, Brands CRUD, General info

### Task System
- 4-column Kanban: Open → In Progress → Approval → Completed
- Task Detail Dialog: click card → view/edit all fields (title, description, due date, priority, assignee, notes)
- **Trash**: Delete tasks permanently from the detail dialog (with confirmation step)
- Description area doubled in height (120px read, 140px edit)
- Assignee: Tasks assigned to Jeff (human) or Kit (agent) with filter dropdown
- Approval integration: Tasks in "Approval" column appear in Approvals view
- Auto-archive: Completed tasks → archived after 7 days

### Settings
- **Users & Agents**: CRUD, avatar colors, human/agent roles
- **Brands**: CRUD with color picker, slug management
- **General**: Info about auto-archive, AgentMail sync, real-time updates, API version

### Chat View (MOCKED — awaiting OpenClaw gateway)
- GatewayAdapter pattern: MockGatewayAdapter (swap to RealGatewayAdapter when ready)
- Configurable gateway URL via REACT_APP_GATEWAY_URL (default ws://127.0.0.1:18888)
- Configurable auth via REACT_APP_GATEWAY_TOKEN (Bearer token in .env, not hardcoded)
- **Env var toggle** (Apr 2, 2026): `REACT_APP_USE_MOCK_GATEWAY=true|false`
  - `true`: MockGatewayAdapter (preview builds, no gateway needed)
  - `false`: RealGatewayAdapter (WebSocket, OpenClaw protocol v3)
  - No silent fallback — real mode failures are visible in UI
- **RealGatewayAdapter** (fully implemented, untested against live gateway):
  - WebSocket protocol v3 handshake with auth token
  - `chat.send` → fire-and-forget, streaming response via events
  - `sessions.list`, `chat.history`, `status` → request/response over WS
  - Streaming text rendering (progressive updates as tokens arrive)
  - Connection states: connected / connecting / handshaking / reconnecting / auth_failed / origin_rejected / unreachable
  - Auto-reconnect with exponential backoff (max 10 attempts)
  - Debug logging: `REACT_APP_GATEWAY_DEBUG=true` logs all WS frames to console
  - Colored console groups for send/receive frames
- **Event-based adapter interface** (both adapters):
  - `sendMessage()` is fire-and-forget; response arrives via `onChatEvent` subscription
  - `onChatEvent(callback)` → events: streaming, complete, typing, abort, tool, error
  - `onConnectionStateChange(callback)` → connection state changes
- **Connection state banner** (real mode only): shows connecting/auth_failed/origin_rejected/unreachable with retry button
- **Mode indicator**: sidebar footer shows "Mock" or "Live" with green connected dot
- **Chat History Sidebar** (260px, full implementation — Apr 2, 2026):
  - Session list grouped by date (Today, Yesterday, Last 7 days, Older)
  - Dot indicators: filled accent for current session, outline for past sessions
  - Context menu per session with Rename (inline edit) and Delete
  - Search input at top to filter sessions by title
  - Read-only mode: viewing a past session hides the input box
  - "Back to current" banner with accent button to return to the active session
  - Session titles auto-generated from first user message (~40 char truncation)
  - `+ New` button + `/new` slash command to create sessions
  - Mobile slide-out drawer (260px) with overlay
- Markdown rendering (tables, code blocks with **syntax highlighting + Copy button**, lists, blockquotes, HR)
- **Syntax highlighting**: highlight.js with 10 languages (JS, Python, Bash, JSON, CSS, HTML, TypeScript, SQL, YAML, Markdown)
- **Links open in new tab**: target="_blank" via custom marked renderer + DOMPurify hook
- **System messages**: centered, muted, smaller text for /new confirmations etc.
- **Relative timestamps**: "just now", "2m ago", "1h ago" — full date/time on hover
- **Action buttons**: renders `actions[]` from message payload as styled button row (navigate, open_url, bulk_approve)
- **Embedded entity cards**: renders `embeds[]` as compact inline cards with status badges
- **"Show more" collapse**: for Kit responses over ~500 words, with gradient mask and expand toggle
- Slash commands: /status, /usage, /compact, /context, /new, /clear, /reset
- Typing indicator, optimistic sends, auto-scroll
- **Enhanced Status Bar** (Apr 2, 2026):
  - Model name (provider prefix stripped): `claude-opus-4-6`
  - Context bar with `42% ctx (84.0k/200.0k)` — used/max tokens
  - Token arrows: `↘12.4k ↗2.1k` (down=input, up=output)
  - Session cost: `$0.23 session`
  - Cache/response-time tooltips on hover
  - 95%+ context warning: pulsing bar + red hint "Try /compact"
  - Periodic refresh: re-fetches status every 60s when idle
  - Max height: 32px
- Full-bleed chat layout (escapes .mc-content padding/max-width constraints)

### Other Features
- WebSocket real-time updates, email templates, search/filter, brand filtering
- API v1 with full spec alignment
- Keyboard shortcuts in Approvals: ↑/↓ or J/K to navigate, A to approve, D to discard/send-back, Esc to deselect

## Prioritized Backlog

### P1
- ~~Keyboard shortcuts (a = approve, d = discard)~~ DONE (Apr 1, 2026)
- ~~Chat History Sidebar~~ DONE (Apr 2, 2026)
- ~~RealGatewayAdapter (WebSocket + event-based)~~ DONE (Apr 2, 2026) — code complete, needs live gateway test
- ~~Google Calendar OAuth redirect_uri_mismatch fix~~ RESOLVED — replaced with Service Account (Apr 2, 2026)

### P2
- Multi-user auth with roles
- Notification layer
- Auto-approval threshold rules
- Mobile responsive

## Future / Blocked
## Kit (OpenClaw) Integration — Option 2 Architecture
Kit creates tasks with metadata for human approval. Kit polls for approved tasks, sends emails via AgentMail directly, then marks tasks completed with send logs.

### Supported Flows
- `POST /api/v1/tasks` with `metadata` (JSON dict: agentmail_inbox_id, agentmail_thread_id, reply_to_address, send_method)
- `PATCH /api/v1/tasks/{id}` with `user_note` ("approved" / "approved with edits: ..." / "reject: ...")
- `PATCH /api/v1/tasks/{id}` with `status: "completed"` + `append_agent_note` (appends send log without replacing draft)
- `PATCH /api/v1/approvals/{id}` with `status: "dismissed"` (hides from pending, keeps in DB)
- `GET /api/v1/tasks?brand=X&status=open` for Kit polling (filter by metadata.send_method in client)
