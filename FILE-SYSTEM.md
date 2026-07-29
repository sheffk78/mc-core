# FILE-SYSTEM.md — Kit Workspace Architecture
_Last updated: July 27, 2026_

This file owns the workspace file structure, brand folder architecture, file hierarchy rules, and system paths. AGENTS.md points here.

**Authority:** This file is a sub-document of AGENTS.md. It carries the same authority as AGENTS.md on all file-organization decisions.

---

## Organization Principles

These are the rules that govern where every file lives. When in doubt, apply these in order:

1. **Root is Kit's operating system only.** Only files that define *how Kit works* belong at `workspace/`. Brand content, project code, research, and reports never go here.

2. **Brand content lives in its brand folder.** Every document, research file, report, or piece of content that relates to a specific brand belongs under `Kit/life/brands/{BrandName}/`. No exceptions.

3. **Code projects follow their brand.** If a project serves a specific brand, it goes under that brand's `projects/` subfolder. If it's independent, it goes under `Kit/life/projects/`.

4. **Shared resources stay shared.** Cross-brand reference materials (templates, education briefs, operating principles) stay in `Kit/life/resources/` or `Kit/life/templates/`.

5. **One credential store.** All API keys, tokens, and secrets live in `workspace/secrets/`. No separate `api-keys/` or scattered `.env` files outside the root.

6. **Never delete — archive.** When a file no longer belongs, move it to `workspace/archive/` with a dated folder. Never delete anything.

7. **Kit/ vs kit/ — both exist, both are valid.** macOS is case-insensitive, so `Kit/` and `kit/` point to the same directory. Use `Kit/` in documentation for readability.

8. **Brand folder names are case-sensitive.** `TrustOffice`, `Wingpoint`, `TrueJoyBirthing`, `AeriusView` — not lowercase, not hyphenated.

---

## Workspace Root

Only Kit's operating system files and system infrastructure directories live at the root. Brand-specific content, project code, and research belong in their respective homes under `Kit/life/`.

```
~/.openclaw/workspace/
├── AGENTS.md                  # Protocols and rules (router)
├── CODING-PROTOCOLS.md        # Coding workflow paths
├── CRONS.md                   # Cron job documentation
├── FILE-SYSTEM.md             # This file — workspace architecture
├── HEARTBEAT.md               # 55-minute work cycle
├── MEMORY.md                  # Patterns about how Jeff thinks
├── SYSTEM/                    # System docs, rules, operational state
│   ├── ACTIVE-TASK.md         # Current top-level mission
│   ├── ARCHIVE.md             # Archive policy and locations
│   ├── HERMES-ONBOARDING.md   # Hermes agent identity/onboarding
│   ├── JOB-LEDGER.md          # Execution record for spawned jobs
│   ├── ROUTER-RULES.md         # Model config, costs, caps
│   ├── (OPERATING-RULES.md)   # [ARCHIVED 2026-07-28 → archive/2026-07-28-workspace-restructure/] — was merged into AGENTS.md
│   ├── (OWNERSHIP.md)         # [ARCHIVED 2026-07-28 → archive/2026-07-28-workspace-restructure/] — was merged into AGENTS.md
│   ├── PRIORITIZATION.md      # Priority tiers, brand rotation
│   ├── ROUTER-RULES.md        # Lane definitions, task→lane mapping
│   ├── TASKS/                 # OpenClaw task system
│   ├── audits/                # Brand audit reports
│   ├── critical-review-skill-weaving.md  # Skill weaving review
│   ├── memory-architecture-design.md    # Knowledge graph design
│   ├── skill-graph-implementation.md     # Skill graph system spec
│   ├── noota-access-recommendation.md   # Noota access research
│   └── ... (other system docs)
├── SOUL.md                    # Kit's voice
├── TOOLS.md                   # How to invoke local tools
├── USER.md                    # About Jeff
├── WORK-PROTOCOL.md           # Task execution protocol
│
├── Kit/                      # ⚠️ Capital K — NOT lowercase 'kit'
│   ├── briefs/                # Daily morning briefs
│   └── life/                  # Knowledge graph (PARA structure)
│       ├── brands/           # Brand-specific content (see below)
│       ├── projects/         # Non-brand projects (see below)
│       └── resources/        # Cross-brand shared reference materials
│
├── TOOLS/                     # Detailed tool documentation
├── archive/                   # Retired files (never deleted)
├── config/                    # System configuration
├── cron_tracking/             # Cron job tracking data
├── mc-core/                   # Mission Control core
├── memory/                    # Daily notes (YYYY-MM-DD.md)
├── pending_review/            # Tasks pending Jeff's review
├── scripts/                   # System scripts, tool wrappers, and reusable utilities
│   └── x-cli-tools/          # X/Twitter CLI tools
├── secrets/                   # All credentials and API keys
└── skills/                    # Global cross-brand skills
```

### What does NOT belong at root

| Item | Where it belongs | Why |
|---|---|---|
| Brand-specific files (research, reports, content) | `Kit/life/brands/{Brand}/` | Brand isolation |
| Project code (rental-finder, etc.) | `Kit/life/projects/{project}/` or `Kit/life/brands/{parent}/` | Projects aren't system infrastructure |
|| `BRANDS.md` (removed) | SOUL.md portfolio table + individual BRAND-STATUS.md | Duplicated info |
| entities.json, mempalace.yaml (archived) | `archive/workspace-cleanup-2026-04-23/` | Stale path references, low value |
| api-keys/ (merged) | `secrets/` | Single credential store |

---

## Brand Folders

All brand content lives under `Kit/life/brands/`. Case-sensitive paths:

```
~/.openclaw/workspace/Kit/life/brands/
├── AeriusView/                # NOT aeriusview
├── AnchorPointTrusts/         # AnchorPoint
├── TrueJoyBirthing/           # NOT truejoybirthing
│   └── reddit-drafts/         # Reddit engagement drafts
├── TrustMinutes/              # TrustMinutes
│   └── reports/               # Generated reports
├── TrustOffice/               # NOT trustoffice or trust-office
├── Wingpoint/                 # NOT wingpoint or wing-point
│   └── research/              # LinkedIn and advisor research
├── products/                  # Shared product assets
└── ~OLD/                      # Archived brand content
```

**⚠️ COMMON MISTAKE:** Use `Kit` (capital K), not `kit` (lowercase). Do NOT write to `~/.openclaw/workspace/brands/` — that path is wrong and will create duplicate, out-of-sync files. Always use `Kit/life/brands/{BrandName}/`.

---

## Project Folders

Non-brand projects (utilities, research, experiments) live under `Kit/life/projects/`:

```
~/.openclaw/workspace/Kit/life/projects/
├── brightbean-studio/         # Creative tool project
├── rental-finder/              # Rental search utility
└── reverse-synthid/            # SynthID research project
```

If a project becomes a brand or sub-brand, it moves to `Kit/life/brands/`. The distinction: brands have audiences and revenue targets; projects are tools or experiments.

---

## Single Brand Root Architecture

Each brand follows a three-layer structure inside its folder. For the full subfolder structure, naming conventions, and the decision tree on where individual files go, see `~/.openclaw/workspace/kit/life/brands/FOLDER-STRUCTURE.md`.

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

**Layer 3 — Skills** (the "how", invoked by name from SKILLS-INDEX). Brand-specific skills in `brands/{brand}/skills/`. Global skills in `~/.openclaw/workspace/skills/`.

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
| Railway scripts | `~/.openclaw/workspace/scripts/railway/` |
| X/Twitter CLI tools | `~/.openclaw/workspace/scripts/x-cli-tools/` |
| All credentials | `~/.openclaw/workspace/secrets/` |
| Local Archive | `~/.openclaw/workspace/archive/` |
| Permanent Archive (Dropbox-synced) | `/Volumes/RENDER DISK/Dropbox/Workspace/Kit/life/archive/` |
| Mission Control | `~/.openclaw/workspace/mc-core/` |

---

## Anti-Patterns (DO NOT DO)

| ❌ Wrong | ✅ Correct |
|---|---|
| `workspace/brands/TrustOffice/` | `Kit/life/brands/TrustOffice/` | Brand isolation |
| Brand code/projects at workspace root | `Kit/life/brands/{brand}/projects/` or `Kit/life/projects/` | Projects aren't system infrastructure |
| Brand research at `workspace/research/` | `Kit/life/brands/{brand}/research/` | Brand isolation |
| Utility scripts at workspace root | `scripts/` | Single utility location |
| System docs at workspace root | `SYSTEM/` | System docs belong together |
| Cross-brand reference at brand root | `Kit/life/resources/` | Shared resources stay shared (§4) |
| Archived brand folders (AgenticTrust) | `archive/` or `~OLD/` inside brands/ | Sunset brands get archived |
| `~/.openclaw/workspace/kit/life/brands/` (lowercase k) | `~/.openclaw/workspace/Kit/life/brands/` (capital K) |
| Brand reports at `workspace/reports/` | `Kit/life/brands/{brand}/reports/` |
| Project code at `workspace/{project}/` | `Kit/life/projects/{project}/` or `Kit/life/brands/{parent}/{project}/` |
| Credentials split across `api-keys/` and `secrets/` | `secrets/` only |
|| Duplicate brand info in `BRANDS.md` at root | `SOUL.md` portfolio table + individual `BRAND-STATUS.md` |
| Stale backups (`.bak` files) at root | Delete — keep only the current version |
| Empty directories from accidents (e.g., `~` dir) | Delete immediately |

---

## Brand Hosting & Codebase Status

| Brand | Code Repository | Hosting | Database | Kit Access |
|---|---|---|---|---|
| **TrustOffice** | GitHub (synced from Emergent) | Railway (primary), Emergent (legacy) | Railway-managed | Full access via Railway CLI + API |
| **WingPoint** | GitHub (synced from Emergent) | Railway (primary), Emergent (legacy) | Railway-managed | Full access via Railway CLI + API |
| **True Joy Birthing** | GitHub | Railway.app | MongoDB | Full access via Railway CLI + API |
| **AeriusView** | GitHub | Railway | Railway-managed | Full access via Railway CLI + API |
| **TrustMinutes** | GitHub | Railway | Railway-managed | Full access via Railway CLI + API |

Kit has full Railway access — Railway CLI and API token in environment. Use `skills/railway-deploy/SKILL.md` for deployment instructions.

---

## 2026-04-23 Reorganization

The following changes were made on April 23, 2026:

| Moved From | Moved To | Reason |
|---|---|---|
| `workspace/rental-finder/` | `Kit/life/projects/rental-finder/` | Non-brand project |
| `workspace/brightbean-studio/` | `Kit/life/projects/brightbean-studio/` | Non-brand project |
| `workspace/reverse-synthid/` | `Kit/life/projects/reverse-synthid/` | Non-brand project |
| `workspace/x-cli-tools/` | `workspace/scripts/x-cli-tools/` | System tooling |
| `workspace/research/*` | `Kit/life/brands/{brand}/research/` | Brand-specific research |
| `workspace/reports/*` | `Kit/life/brands/TrustMinutes/reports/` | TrustMinutes content |
| `workspace/api-keys/*` | `workspace/secrets/` | Consolidated credential store |
| `workspace/BRANDS.md` | `archive/workspace-cleanup-2026-04-23/` | Duplicated by IDENTITY.md |
| `workspace/DREAMS.md` | `archive/workspace-cleanup-2026-04-23/` | Not operational |
| `workspace/entities.json` | `archive/workspace-cleanup-2026-04-23/` | Stale paths |
| `workspace/mempalace.yaml` | `archive/workspace-cleanup-2026-04-23/` | Stale paths |
| `Kit/reddit-drafts-*.md` | `Kit/life/brands/TrueJoyBirthing/reddit-drafts/` | TJB content |
| `Kit/task{1,2,3}.json` | `archive/workspace-cleanup-2026-04-23/` | Stale artifacts |
| `Kit/SESSION_INIT_RULES.md` | `archive/workspace-cleanup-2026-04-23/` | Superseded by AGENTS.md |

---

## 2026-07-27 Reorganization

Major workspace cleanup performed on July 27, 2026. **110 misplaced items** were triaged and resolved — no data was lost. All actions documented in `archive/2026-07-27-workspace-cleanup/MANIFEST.json`.

| Category | Action | Count | Details |
|---|---|---|---|
| TJB research files | ARCHIVE | 8 | Raw research JSONs already deployed in `cities.ts` → `archive/.../tjb-research/` |
| TJB outreach emails | MOVE | 5 | Scattered email drafts → `TrueJoyBirthing/outreach/<slug>/` (bozeman merged to 1 canonical) |
| TJB images | ARCHIVE | 15 MB | `tjb-images/` — all cities already have optimized images in `public/images/` |
| AeriusView API | MERGE+ARCHIVE | 1 dir | Unique docs merged to canonical repo `~/Projects/aeriusview-api/`, stale copy archived |
| AeriusView research | MOVE | 1.9 MB | `aeriusview-research/` → `AeriusView/research/` |
| AeriusView scripts | MOVE | 4 files | SLC contractor scripts → `~/Projects/aeriusview-scripts/` |
| AeriusView pricing | MOVE | 1 dir | `app/pricing.py` (drone pricing) → `AeriusView/app/` |
| SocializeVideo platform | MOVE | 11 MB | `socialize-platform/` → `SocializeVideo/projects/` |
| SocializeVideo toolkit | MOVE+ARCHIVE | 6 files | v3 → `SocializeVideo/toolkit/`, v1/v2 archived |
| WingPoint research | MOVE | 4 files | Legal brief renders + position paper → `Wingpoint/research/` |
| WingPoint backup | MOVE | 1 dir | MongoDB backup → `Wingpoint/data/mongodb-backup/` |
| StenoDesk deploy | MOVE | 4 items | Deploy scripts → `StenoDesk/scripts/`, frontend config → `StenoDesk/frontend/` |
| Utility scripts | MOVE to `scripts/` | 4 | `classify_and_update.py`, `finalize_summary.py`, `run-ads-automated.sh`, `scan_inboxes.py` |
| One-off scripts | ARCHIVE | 7 | Diagnostics, migration runners → `archive/.../scripts/` |
| Security risk | DELETE | 1 | `db_check.py` (hardcoded DB password) |
| Duplicate files | DELETE | 3 | `check-hero2.js`, `find_natalie_emails.py`, `.bak` files |
| System docs | MOVE to `SYSTEM/` | 5 | `ARCHIVE.md`, `HERMES-ONBOARDING.md`, + 3 design docs |
| System infrastructure | MOVE to `SYSTEM/` | 2 dirs | `TASKS/` and `audits/` → `SYSTEM/TASKS/` and `SYSTEM/audits/` |
| Stray directories | ARCHIVE | 7 | `keyframes/`, `ladder-safety-frames/`, `monitoring/`, `og-check/`, `output/`, `discovery-results/`, `scout/` |
| Accidental items | DELETE | 3 | `~` dir, `strix-scans/` (empty), `IDEA=test` |
| Audit/review data | ARCHIVE | 8 files | Shelbi audit, Fable5 review, competitor ads → `archive/.../audits/` |
| Brand loose files | MOVE | 7 | `.dm` files, LinkDaddy CSV, linkseeker PDFs → respective brand folders |
| Cross-brand reference | MOVE | 1 | `SEO-BACKLINK-PLAN.md` → `Kit/life/resources/` |
| Project loose files | MOVE | 8 | `ai_instructor_*` → new `projects/ai-instructor-outreach/`, fable5 plans → `projects/fable5-review/` |

**`skills-lock.json`** remains at workspace root — it is Hermes skill infrastructure, not a stray file.

**`scout/.env`** was archived with a manifest flag noting secrets need scrubbing before any external access.

**Active brand folders preserved** (Jeff's explicit instruction, July 27): `busybusy-research/`, `punchpoint/`, `Slice Photography/`, `TinkleTent/` — not archived despite appearing inactive.

---

## 2026-07-28 Workspace Restructure

Additional cleanup performed on July 28, 2026:

| Moved From | Moved To | Reason |
|---|---|---|
| `outreach-pipeline-dashboard-spec.md` (root) | `Kit/life/brands/TrustOffice/` | TrustOffice deliverable |
| `ads-channels-dashboard-spec.md` (root) | `Kit/life/brands/TrustOffice/` | TrustOffice deliverable |
| `trust-record-retention-research.md` (root) | `Kit/life/brands/TrustOffice/` | TrustOffice deliverable |
| `aeriusview-admin-dashboard-spec.md` (root) | `Kit/life/brands/aeriusview/` | AeriusView deliverable |
| `aeriusview-dashboard-gap-analysis.md` (root) | `Kit/life/brands/aeriusview/` | AeriusView deliverable |
| `lehi-ut-doulas-research.md` (root) | `Kit/life/brands/TrueJoyBirthing/research/` | TJB research |
| `newark-nj-enrichment.json` (root) | `Kit/life/brands/TrueJoyBirthing/research/` | TJB research data |
| `railway_*.py`, `railway_*.json` (root, 31 files) | `scripts/railway/` | Utility scripts |
| `SYSTEM/OPERATING-RULES.md` | `archive/2026-07-28-workspace-restructure/` | Empty stub (already merged into AGENTS.md) |
| `SYSTEM/OWNERSHIP.md` | `archive/2026-07-28-workspace-restructure/` | Empty stub (already merged into AGENTS.md) |
| `ben_dns_email.txt` (root) | `archive/2026-07-28-workspace-restructure/` | One-off artifact |
| `downloaded_image.png` (root) | `archive/2026-07-28-workspace-restructure/` | Stray image |
| `tidycal_sync_report.md` (root) | `archive/2026-07-28-workspace-restructure/` | One-off report |
| `IDENTITY.md` (root) | `archive/2026-07-29-cleanup/` | Merged into SOUL.md 2026-07-28; stub archived 2026-07-29 |