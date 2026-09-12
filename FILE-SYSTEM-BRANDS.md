# FILE-SYSTEM-BRANDS.md — Brand Folder Details
<!-- ROUTING: Load when you need brand folder structure, hosting, or codebase details -->

Extracted from FILE-SYSTEM.md to keep the main file under 3KB. This file has the detailed brand folder architecture.

## Brand Folders

All brand content lives under `Kit/life/brands/`. Folder names are **case-sensitive** and match the on-disk directories exactly:

```
~/.openclaw/workspace/Kit/life/brands/
├── AeriusView/
├── AgenticTrust/          # SUNSET 2026-07-06 — kept for reference, not active
├── AnchorPointTrusts/     # INACTIVE (dormant) — kept, no on-disk folder yet
├── FreeTrustDocs/
├── MondaySafe/
├── Personal/
├── Slice Photography/     # NOTE: contains a space, quoted in shell
├── SocializeVideo/
├── StenoDesk/
├── TinkleTent/
├── TrueJoyBirthing/       # NOT truejoybirthing
├── TrustMinutes/
├── TrustOffice/           # NOT trustoffice or trust-office
├── TrustParaTodos/
├── Wingpoint/             # On disk exactly: capital W, lowercase p — "Wingpoint"
├── ~OLD/                  # Archived brand content (AgenticTrust etc.)
```

**⚠️ COMMON MISTAKE:** Use `Kit` (capital K), not `kit` (lowercase). Do NOT write to `~/.openclaw/workspace/brands/` — that path is wrong. Always use `Kit/life/brands/{BrandName}/`.

**Inactive/sunset brands are kept, never deleted.** Sunsets (`AgenticTrust`) and dormant brands (`AnchorPointTrusts`) stay in this list and in the folder tree where a folder exists. `AnchorPointTrusts` currently has no on-disk directory — it stays in the doc as INACTIVE and should be scaffolded (via the new-brand setup in `FOLDER-STRUCTURE.md`) before it's reactivated.

**Non-brand shell dirs** (`_TEST-hygiene/`, `_system/`, `bath-remodel-sites/`, `busybusy-research/`, `punchpoint/`) are scratch/experiment, not brands — they belong under `Kit/life/projects/` at most and are flagged by Atlas if they accumulate.

## Project Folders

Non-brand projects (utilities, research, experiments) live under `Kit/life/projects/`.

If a project becomes a brand or sub-brand, it moves to `Kit/life/brands/`. The distinction: brands have audiences and revenue targets; projects are tools or experiments.

## Single Brand Root Architecture

Each brand follows a three-layer structure inside its folder. **`Kit/life/brands/FOLDER-STRUCTURE.md` is the authoritative full skeleton** — including subfolders (`work/`, `outputs/`, `assets/`, `content/`, `intel/`, `skills/`, `projects/`), the file-decision tree, and naming conventions. This table summarizes the root-level reference/live-ops files; see FOLDER-STRUCTURE.md for everything else.

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
| `STATUS-VOCABULARY.md` | Canonical status values |
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

**Layer 3 — Skills** (the "how", invoked by name from SKILLS-INDEX). Brand-specific skills in `brands/{brand}/skills/`. Global skills in `skills/`. Also see `HISTORY.md` (durable completion record) and the subfolder set in `FOLDER-STRUCTURE.md`.

## Hierarchy Rules

- BIBLE points; it does not contain.
- LIVE-STATE wins over BIBLE on current status (numbers, pipeline). BIBLE wins on permanent facts (voice, never-do).
- DECISIONS overrides anything else. Decisions log is authoritative.
- If a skill conflicts with BRAND-VOICE or PRINCIPLES, the brand reference wins. Kit flags the skill for update.

## Brand Hosting & Codebase Status

| Brand | Code Repository | Hosting | Database | Kit Access |
|---|---|---|---|---|
| **TrustOffice** | GitHub (sheffk78) | Railway (primary) | Railway-managed | Full access via Railway API |
| **WingPoint** | GitHub (sheffk78) | Railway (primary) | Railway-managed | Full access via Railway API |
| **True Joy Birthing** | GitHub (sheffk78) | Railway.app | MongoDB | Full access via Railway API |
| **AeriusView** | GitHub (sheffk78) | Railway | Railway-managed | Full access via Railway API |
| **TrustMinutes** | GitHub | Railway | Railway-managed | Full access via Railway API |

Kit has full Railway access — API token in `secrets/railway-api-token.txt`. Use `skills/railway-deploy/SKILL.md` for deployment instructions.