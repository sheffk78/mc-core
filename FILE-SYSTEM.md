# FILE-SYSTEM.md — Kit Workspace Architecture
<!-- ROUTING: Load when organizing files or checking where something belongs -->

_Brand folder details, hosting, and full brand architecture: `FILE-SYSTEM-BRANDS.md`._

## Organization Principles

1. **Root is Kit's operating system only.** Only files that define *how Kit works* belong at `workspace/`. Brand content, project code, research, and reports never go here.
2. **Brand content lives in its brand folder.** Every document that relates to a specific brand belongs under `Kit/life/brands/{BrandName}/`. No exceptions.
3. **Code projects follow their brand.** Brand projects → `Kit/life/brands/{brand}/projects/`. Independent → `Kit/life/projects/`.
4. **Shared resources stay shared.** Cross-brand references stay in `Kit/life/resources/` or `Kit/life/templates/`.
5. **One credential store.** All secrets live in `workspace/secrets/`. No scattered `.env` files outside secrets/.
6. **Never delete — archive.** Move to `workspace/archive/` with a dated folder.
7. **Kit/ vs kit/** — macOS is case-insensitive, both are valid. Use `Kit/` in docs.
8. **Brand folder names are case-sensitive.** `TrustOffice`, `Wingpoint`, `TrueJoyBirthing`, `AeriusView` — not lowercase.

## Workspace Root

```
~/.openclaw/workspace/
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
├── archive/                   # Retired files (never deleted)
├── config/                    # System configuration
├── cron_tracking/             # Cron job tracking data
├── mc-core/                   # Mission Control core
├── memory/                    # Daily notes (YYYY-MM-DD.md)
├── pending_review/            # Tasks pending Jeff's review
├── scripts/                   # System scripts, tool wrappers, utilities
├── secrets/                   # All credentials and API keys (+ INVENTORY.md)
└── skills/                    # Global cross-brand skills
```

### What does NOT belong at root

| Item | Where it belongs | Why |
|---|---|---|
| Brand-specific files | `Kit/life/brands/{Brand}/` | Brand isolation |
| Project code | `Kit/life/projects/` or `Kit/life/brands/{parent}/` | Not system infrastructure |
| Loose `.py` scripts | `scripts/` | Single utility location |
| System docs | `SYSTEM/` | System docs belong together |

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
| Local Archive | `~/.openclaw/workspace/archive/` |
| Permanent Archive | `/Volumes/RENDER DISK/Dropbox/Workspace/Kit/life/archive/` |

## Anti-Patterns (DO NOT DO)

| Wrong | Correct | Why |
|---|---|---|
| `workspace/brands/TrustOffice/` | `Kit/life/brands/TrustOffice/` | Brand isolation |
| Brand code at workspace root | `Kit/life/brands/{brand}/projects/` | Not system infrastructure |
| Loose `.py` scripts at root | `scripts/` | Single utility location |
| System docs at workspace root | `SYSTEM/` | System docs belong together |
| `kit/` (lowercase k) | `Kit/` (capital K) | Documentation readability |
| Credentials in scattered `.env` | `secrets/` only | Single credential store |