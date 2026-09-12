# FILE-SYSTEM.md — Kit Workspace Architecture
<!-- ROUTING: Load when organizing files or checking where something belongs -->

_Brand folder details, hosting, and full brand architecture: `FILE-SYSTEM-BRANDS.md`._

## Organization Principles

1. **Root is Kit's operating system only.** Only files that define *how Kit works* belong at `workspace/`. Brand content, project code, research, and reports never go here.
2. **Brand content lives in its brand folder.** Every document that relates to a specific brand belongs under `Kit/life/brands/{BrandName}/`. No exceptions.
3. **Code projects follow their brand.** Brand projects → `Kit/life/brands/{brand}/projects/`. Independent → `Kit/life/projects/`.
4. **Shared resources stay shared.** Cross-brand references stay in `Kit/life/resources/` or `Kit/life/templates/`.
5. **One credential store.** All secrets live in `workspace/secrets/`. No scattered `.env` files outside secrets/.
6. **Never delete — archive.** Move to `/Volumes/RENDER DISK/archive/` (canonical) with a dated folder, then run `archive-hook.sh` to index it. Workspace `archive/` is a symlink to it.
7. **Kit/ vs kit/** — macOS is case-insensitive, both are valid. Use `Kit/` in docs.
8. **Brand folder names are case-sensitive.** `TrustOffice`, `Wingpoint`, `TrueJoyBirthing`, `AeriusView` — not lowercase.

9. **Let Hermes own its runtime state.** `.hermes/` is an auto-managed runtime directory (cron execution DB, skill registry index, working memory, operational scripts, auth tokens). Do not create files there expecting durable persistence. If data matters, it lives in workspace first.

## Workspace Root

```
~/.openclaw/workspace/           # Human-curated durable authority; `.hermes/` is the runtime scratch that reads from here
├── AGENTS.md                  # Protocols, rules, routing table (auto-loaded)
├── SOUL.md                    # Kit's voice and identity
├── MEMORY.md                  # Patterns about how Jeff thinks
├── USER.md                    # About Jeff
├── HEARTBEAT.md               # 55-minute work cycle
├── CRONS.md                   # Cron job documentation
├── CODING-PROTOCOLS.md        # Coding workflow paths
├── WORK-PROTOCOL.md           # Task execution protocol
├── FILE-SYSTEM.md             # This file — workspace architecture
├── FILE-SYSTEM-BRANDS.md      # Brand folder details + hosting
├── TOOLS.md                   # Tool index (→ TOOLS/*.md for details)
│
├── SYSTEM/                    # System docs, rules, operational state
│   ├── ACTIVE-TASK.md         # Current top-level mission
│   ├── ARCHIVE.md             # Archive policy and locations
│   ├── CROSS-AGENT-WATCHDOG.md
│   ├── DELIBERATION-GATE.md   # Protocol for significant decisions
│   ├── DEVELOPMENT-STANDARDS.md
│   ├── JOB-LEDGER.md          # Execution record for spawned jobs
│   ├── JOB-PROTOCOLS.md       # Job lifecycle, checkpoints, watchdog
│   ├── OPERATING-MANUAL.md    # Detailed operating rules (on-demand)
│   ├── PRIORITIZATION.md      # Priority tiers, brand rotation
│   ├── RELIABILITY-STANDARDS.md
│   ├── ROUTER-RULES.md        # Model config, costs, caps
│   ├── TASKS/                 # Task files for tracked jobs
│   ├── audits/                # Brand audit reports
│   ├── data/                  # JSON state files (campaign, outreach)
│   ├── logs/                  # Active logs (executor, watchdog, dead-letter)
│   └── scripts/               # System-level scripts
│
├── Kit/                      # Capital K — brand content lives here
│   ├── briefs/                # Daily morning briefs
│   └── life/                  # Knowledge graph (PARA structure)
│       ├── brands/           # Brand-specific content (see FILE-SYSTEM-BRANDS.md)
│       ├── projects/         # Non-brand projects
│       └── resources/        # Cross-brand shared reference materials
│
├── TOOLS/                     # Detailed tool documentation
├── TOOLS/stealth-helpers.md   # Shared browser-automation utility (human-mimicry for Playwright/CDP)
├── archive/                   # Retired files (never deleted)
├── config/                    # System configuration
├── cron_tracking/             # Cron job tracking data
├── mc-core/                   # LEGACY — Mission Control core (decommissioned 2026-08-14, archive candidate)
├── memory/                    # Daily notes (YYYY-MM-DD.md)
├── pending_review/            # Triage inbox for items awaiting Jeff's review (see lifecycle note)
├── scripts/                   # System scripts, tool wrappers, utilities
├── secrets/                   # All credentials and API keys (+ INVENTORY.md)
└── skills/                    # Global cross-brand skills
```

### What does NOT belong at root

| Item | Where it belongs | Why |
|---|---|---|
| Brand-specific files | `Kit/life/brands/{Brand}/` | Brand isolation |
| Project code | `Kit/life/brands/{Brand}/projects/` (brand) or `Kit/life/projects/` (non-brand) | Not system infrastructure |
| Loose `.py` scripts | `scripts/` | Single utility location |
| System docs | `SYSTEM/` | System docs belong together |

### `pending_review/` lifecycle (Jeff directive 2026-08-21)

`pending_review/` is a **triage inbox — a queue, not a pile.** Items are moved here awaiting Jeff's review; they must not linger.

- **It is NOT a storage area.** Any brand-specific material parked here belongs inside its brand folder (`Kit/life/brands/{Brand}/`), not this inbox.
- **Resolved items get DELETED, not archived.** Once an item is handled — or its useful info has been moved to its real home (e.g. credentials confirmed in `~/.config/x-api/keys.env`) — delete the file. Archive is for genuinely historical/retired records, not for cleared inbox items.
- **Superseded proposals get deleted too.** If the work a recommendation describes has already shipped (e.g. a dashboard restructure the code now reflects), the doc is a stale plan with no surviving value — remove it.
- **Surfacing real finds is the goal.** If triage uncovers a genuinely live issue Jeff has forgotten (e.g. a monitor running blind on a drained quota), bring it up — but once Jeff confirms it's already known or not needed, delete the note and move on.

## System Paths

| Item | Path |
|---|---|
| Workspace root | `~/.openclaw/workspace/` |
| Gateway log | `~/.openclaw/logs/gateway.log` |
| Config | `~/.openclaw/openclaw.json` |
| Sessions | `~/.openclaw/agents/main/sessions/` |
| Daily notes | `~/.openclaw/workspace/memory/` |
| Morning briefs | `~/.openclaw/workspace/Kit/briefs/` |
| Brand folders | `~/.openclaw/workspace/Kit/life/brands/{brand}/` |
| Brand folder pattern | `~/.openclaw/workspace/Kit/life/brands/FOLDER-STRUCTURE.md` |
| Global skills | `~/.openclaw/workspace/skills/` |
| Global skills index | `~/.openclaw/workspace/skills/GLOBAL-SKILLS-INDEX.md` |
| All credentials | `~/.openclaw/workspace/secrets/` |
| Secrets inventory | `~/.openclaw/workspace/secrets/INVENTORY.md` |
| Local Archive (symlink) | `~/.openclaw/workspace/archive/` → `/Volumes/RENDER DISK/archive/workspace-archive/` |
| Permanent Archive | `/Volumes/RENDER DISK/archive/` (canonical — official place to archive) |

## Anti-Patterns (DO NOT DO)

| Wrong | Correct | Why |
|---|---|---|
| `workspace/brands/TrustOffice/` | `Kit/life/brands/TrustOffice/` | Brand isolation |
| Brand code at workspace root | `Kit/life/brands/{brand}/projects/` | Not system infrastructure |
| Loose `.py` scripts at root | `scripts/` | Single utility location |
| System docs at workspace root | `SYSTEM/` | System docs belong together |
| `kit/` (lowercase k) | `Kit/` (capital K) | Documentation readability |
|| Credentials in scattered `.env` | `secrets/` only | Single credential store |
|| Data managed by Hermes at runtime hand-edited in `.hermes/` | Let `.hermes/` own it; client files go in workspace | Hermes auto-manages; hand-edits get overwritten |
|| Human-curated knowledge stored only in `.hermes/` | Workspace `Kit/life/`, `SYSTEM/`, `memory/` | Not persistent; lost on reset |