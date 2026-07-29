# FILE-SYSTEM.md — Kit Workspace Architecture
<!-- ROUTING: Load when organizing files or checking where something belongs -->
_Last updated: July 29, 2026_

This file owns the workspace file structure, brand folder architecture, file hierarchy rules, and system paths. AGENTS.md points here.

**Authority:** This file is a sub-document of AGENTS.md. It carries the same authority as AGENTS.md on all file-organization decisions.

---

## Organization Principles

These are the rules that govern where every file lives. When in doubt, apply these in order:

1. **Root is Kit's operating system only.** Only files that define *how Kit works* belong at `workspace/`. Brand content, project code, research, and reports never go here.

2. **Brand content lives in its brand folder.** Every document, research file, report, or piece of content that relates to a specific brand belongs under `Kit/life/brands/{BrandName}/`. No exceptions.

3. **Code projects follow their brand.** If a project serves a specific brand, it goes under that brand's `projects/` subfolder. If it's independent, it goes under `Kit/life/projects/`.

4. **Shared resources stay shared.** Cross-brand reference materials (templates, education briefs, operating principles) stay in `Kit/life/resources/` or `Kit/life/templates/`.

5. **One credential store.** All API keys, tokens, and secrets live in `workspace/secrets/`. No separate `api-keys/` or scattered `.env` files outside secrets/.

6. **Never delete — archive.** When a file no longer belongs, move it to `workspace/archive/` with a dated folder. Never delete anything.

7. **Kit/ vs kit/ — both exist, both are valid.** macOS is case-insensitive, so `Kit/` and `kit/` point to the same directory. Use `Kit/` in documentation for readability.

8. **Brand folder names are case-sensitive.** `TrustOffice`, `Wingpoint`, `TrueJoyBirthing`, `AeriusView` — not lowercase, not hyphenated.

---

## Workspace Root

Only Kit's operating system files and system infrastructure directories live at the root. Brand-specific content, project code, and research belong in their respective homes under `Kit/life/`.

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
├── TOOLS.md                   # Tool index (→ TOOLS/*.md for details)
│
├── SYSTEM/                    # System docs, rules, operational state
│   ├── ACTIVE-TASK.md         # Current top-level mission
│   ├── ARCHIVE.md             # Archive policy and locations
│   ├── CROSS-AGENT-WATCHDOG.md # Subagent audit protocol
│   ├── DEAD-LETTER-QUEUE.md   # (in logs/) Failed jobs awaiting retry
│   ├── DELIBERATION-GATE.md   # Protocol for significant decisions
│   ├── DEVELOPMENT-STANDARDS.md # Coding standards, review process
│   ├── JOB-LEDGER.md          # Execution record for spawned jobs
│   ├── JOB-PROTOCOLS.md       # Job lifecycle, checkpoints, watchdog
│   ├── OPERATING-MANUAL.md    # Detailed operating rules (on-demand)
│   ├── PRIORITIZATION.md      # Priority tiers, brand rotation
│   ├── RELIABILITY-STANDARDS.md # Monitoring, incident response
│   ├── ROUTER-RULES.md        # Model config, costs, caps
│   ├── TASKS/                 # Task files for tracked jobs
│   ├── audits/                # Brand audit reports
│   ├── data/                  # JSON state files (campaign, outreach)
│   ├── logs/                  # Active logs (executor, watchdog, dead-letter)
│   └── scripts/               # System-level scripts
│
├── Kit/                      # Capital K — NOT lowercase 'kit'
│   ├── briefs/                # Daily morning briefs
│   └── life/                  # Knowledge graph (PARA structure)
│       ├── brands/           # Brand-specific content (see below)
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
| Brand-specific files (research, reports, content) | `Kit/life/brands/{Brand}/` | Brand isolation |
| Project code | `Kit/life/projects/{project}/` or `Kit/life/brands/{parent}/` | Projects aren't system infrastructure |
| Loose `.py` scripts | `scripts/` | Single utility location |
| System docs | `SYSTEM/` | System docs belong together |

---

## Brand Folders

All brand content lives under `Kit/life/brands/`. Case-sensitive paths:

```
~/.openclaw/workspace/Kit/life/brands/
├── AeriusView/                # NOT aeriusview
├── AnchorPointTrusts/         # AnchorPoint
├── TrueJoyBirthing/           # NOT truejoybirthing
├── TrustMinutes/              # TrustMinutes
├── TrustOffice/               # NOT trustoffice or trust-office
├── Wingpoint/                 # NOT wingpoint or wing-point
├── products/                  # Shared product assets
└── ~OLD/                      # Archived brand content
```

**⚠️ COMMON MISTAKE:** Use `Kit` (capital K), not `kit` (lowercase). Do NOT write to `~/.openclaw/workspace/brands/` — that path is wrong. Always use `Kit/life/brands/{BrandName}/`.

---

## Project Folders

Non-brand projects (utilities, research, experiments) live under `Kit/life/projects/`.

If a project becomes a brand or sub-brand, it moves to `Kit/life/brands/`. The distinction: brands have audiences and revenue targets; projects are tools or experiments.

---

## Single Brand Root Architecture

Each brand follows a three-layer structure inside its folder. For the full subfolder structure, see `Kit/life/brands/FOLDER-STRUCTURE.md`.

**Layer 1 — Reference Library** (rarely changes, load on demand)

| File | Owns |
|---|---|
| `BIBLE.md` | Pure index — points to all other reference files |
| `BRAND.md` | Identity, positioning, never-do list |
| `BRAND-VOICE.md` | How the brand speaks |
| `AUDIENCE.md` | Personas, pains, verbatim language |
| `FEATURES.md` | What the product does |
| `OFFERS.md` | Pricing, CTAs, what's allowed |
| `PRINCIPLES.md` | Design and ethics guardrails |
| `GLOSSARY.md` | Term definitions |
| `STRATEGY.md` | Current strategic message |

**Layer 2 — Live Operations** (changes weekly or on event)

| File | Owns | Update cadence |
|---|---|---|
| `BRAND-STATUS.md` | Kit's stage, this week's focus, blockers | Weekly + on change |
| `LIVE-STATE.md` | Pure metrics dashboard | Weekly (Friday) |
| `DECISIONS.md` | Dated override log | Jeff appends, Kit reads |
| `CRON-JOBS.md` | What's automated, schedule, expected output | On change |
| `CONTACTS.md` | People, partners, stages | Continuously |
| `SKILLS-INDEX.md` | Map of brand-specific skills | When skills change |

**Layer 3 — Skills** (the "how", invoked by name from SKILLS-INDEX). Brand-specific skills in `brands/{brand}/skills/`. Global skills in `skills/`.

---

## Hierarchy Rules

- BIBLE points; it does not contain.
- LIVE-STATE wins over BIBLE on current status (numbers, pipeline). BIBLE wins on permanent facts (voice, never-do).
- DECISIONS overrides anything else. Decisions log is authoritative.
- If a skill conflicts with BRAND-VOICE or PRINCIPLES, the brand reference wins. Kit flags the skill for update.

---

## System Paths

| Item | Path |
|---|---|
| Workspace root | `~/.openclaw/workspace/` |
| Gateway log | `~/.openclaw/logs/gateway.log` |
| Error log | `~/.openclaw/logs/gateway.err.log` |
| Config | `~/.openclaw/openclaw.json` |
| Sessions | `~/.openclaw/agents/main/sessions/` |
| Daily notes | `~/.openclaw/workspace/memory/` |
| Morning briefs | `~/.openclaw/workspace/Kit/briefs/` |
| Brand folders | `~/.openclaw/workspace/Kit/life/brands/{brand}/` |
| Project folders | `~/.openclaw/workspace/Kit/life/projects/{project}/` |
| Brand folder pattern | `~/.openclaw/workspace/Kit/life/brands/FOLDER-STRUCTURE.md` |
| Global skills | `~/.openclaw/workspace/skills/` |
| Global skills index | `~/.openclaw/workspace/skills/GLOBAL-SKILLS-INDEX.md` |
| System scripts | `~/.openclaw/workspace/scripts/` |
| All credentials | `~/.openclaw/workspace/secrets/` |
| Secrets inventory | `~/.openclaw/workspace/secrets/INVENTORY.md` |
| Local Archive | `~/.openclaw/workspace/archive/` |
| Permanent Archive (Dropbox-synced) | `/Volumes/RENDER DISK/Dropbox/Workspace/Kit/life/archive/` |
| Mission Control | `~/.openclaw/workspace/mc-core/` |

---

## Anti-Patterns (DO NOT DO)

| Wrong | Correct | Why |
|---|---|---|
| `workspace/brands/TrustOffice/` | `Kit/life/brands/TrustOffice/` | Brand isolation |
| Brand code/projects at workspace root | `Kit/life/brands/{brand}/projects/` | Projects aren't system infrastructure |
| Loose `.py` scripts at root | `scripts/` | Single utility location |
| System docs at workspace root | `SYSTEM/` | System docs belong together |
| Cross-brand reference at brand root | `Kit/life/resources/` | Shared resources stay shared |
| `kit/` (lowercase k) | `Kit/` (capital K) | Documentation readability |
| Credentials split across `.env` files | `secrets/` only | Single credential store |
| Duplicate brand info in `BRANDS.md` | `SOUL.md` portfolio table + `BRAND-STATUS.md` | No duplication |

---

## Brand Hosting & Codebase Status

| Brand | Code Repository | Hosting | Database | Kit Access |
|---|---|---|---|---|
| **TrustOffice** | GitHub (synced from Emergent) | Railway (primary) | Railway-managed | Full access via Railway API |
| **WingPoint** | GitHub (synced from Emergent) | Railway (primary) | Railway-managed | Full access via Railway API |
| **True Joy Birthing** | GitHub | Railway.app | MongoDB | Full access via Railway API |
| **AeriusView** | GitHub | Railway | Railway-managed | Full access via Railway API |
| **TrustMinutes** | GitHub | Railway | Railway-managed | Full access via Railway API |

Kit has full Railway access — API token in `secrets/railway-api-token.txt`. Use `skills/railway-deploy/SKILL.md` for deployment instructions.

---

## Change History

Change logs for past reorganizations are archived at `archive/2026-07-29-cleanup/FILE-SYSTEM-CHANGES.md`.