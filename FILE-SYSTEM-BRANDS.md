# FILE-SYSTEM-BRANDS.md — Brand Folder Details
<!-- ROUTING: Load when you need brand folder structure, hosting, or codebase details -->

Extracted from FILE-SYSTEM.md to keep the main file under 3KB. This file has the detailed brand folder architecture.

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

## Project Folders

Non-brand projects (utilities, research, experiments) live under `Kit/life/projects/`.

If a project becomes a brand or sub-brand, it moves to `Kit/life/brands/`. The distinction: brands have audiences and revenue targets; projects are tools or experiments.

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

## Hierarchy Rules

- BIBLE points; it does not contain.
- LIVE-STATE wins over BIBLE on current status (numbers, pipeline). BIBLE wins on permanent facts (voice, never-do).
- DECISIONS overrides anything else. Decisions log is authoritative.
- If a skill conflicts with BRAND-VOICE or PRINCIPLES, the brand reference wins. Kit flags the skill for update.

## Brand Hosting & Codebase Status

| Brand | Code Repository | Hosting | Database | Kit Access |
|---|---|---|---|---|
| **TrustOffice** | GitHub (synced from Emergent) | Railway (primary) | Railway-managed | Full access via Railway API |
| **WingPoint** | GitHub (synced from Emergent) | Railway (primary) | Railway-managed | Full access via Railway API |
| **True Joy Birthing** | GitHub | Railway.app | MongoDB | Full access via Railway API |
| **AeriusView** | GitHub | Railway | Railway-managed | Full access via Railway API |
| **TrustMinutes** | GitHub | Railway | Railway-managed | Full access via Railway API |

Kit has full Railway access — API token in `secrets/railway-api-token.txt`. Use `skills/railway-deploy/SKILL.md` for deployment instructions.