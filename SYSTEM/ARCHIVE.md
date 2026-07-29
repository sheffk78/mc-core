|# ARCHIVE.md — Kit Workspace Archive Policy
<!-- ROUTING: Load when archiving files or checking archive policy -->
_Last updated: 2026-07-25 by Kit_

**Canonical Archive Location:** `/Volumes/RENDER DISK/archive/` (Render Disk root)

---

## What Gets Archived

**Never delete.** When content is no longer current, create a dated folder in the archive with one of these structures:

### Brand-Specific Archives
```
/Volumes/RENDER DISK/archive/brands/{BrandName}/{YYYY-MM-DD}-{purpose}/
├── README.md          # What this archive contains, why it was archived
├── all-content/       # Entire folder content (folders, files)
├── infra-files/       # Configuration, build files, scripts
├── assets/            # Images, videos, media
└── artifacts/         # Generated reports, logs, test outputs
```

### Project/Skill Archives
```
/Volumes/RENDER DISK/archive/projects/{ProjectName}/{YYYY-MM-DD}-{purpose}/
└── similar structure
```

### Workspace/System Archives
```
/Volumes/RENDER DISK/archive/workspace/{YYYY-MM-DD}-{purpose}/
├── README.md
└── {specific files or folders}
```

---

## Archive Naming Convention

- **Brand archives:** `{YYYY-MM-DD}-{purpose}`
  - Example: `2026-07-25-full` (full cleanup archive)
  - Example: `2026-05-01-scope-change` (archived when property scope changed)

- **Project archives:** `{YYYY-MM-DD}-{project-name}-{purpose}`
  - Example: `2026-07-25-railway-move` (Railway project moved to TrustOffice)

- **Workspace archives:** `{YYYY-MM-DD}-{purpose}`
  - Example: `2026-04-23-folder-reorg` (major folder restructure)

---

## Archive Contents

### BRAND.md Variants
- `BRAND.md.bak` — backed-up before major rewrite
- `BRAND.md.old` — previous version when repositioning entity

### Historical Brand Operations
- Complete content folders for abandoned features
- Historical SKILLS-INDEX for product suites that never shipped
- Historical social media pipelines, blog pipelines
- Old outreach and engagement logs

### Infrastructure Artifacts
- Build configuration for tools that were never deployed
- Railway projects moved to new ownership
- Database schemas, API designs for stopped projects
- Cron job definitions for closed pipelines

### Campaign Archives
- Old Reddit engagement logs
- Social posting logs
- Email campaign archives
- Video production drafts no longer in use

---

## Archive Structure Policies

1. **Mirrored structure** — Archive preserves folder structure from source
2. **One README per archive** — Explain what was archived, why, and when
3. **No automatic linking** — Archive contents are references only. Do not create redirects.
4. **Cross-reference in BRAND.md** — When brand docs change, reference old versions in BRAND.md

---

## Archive Folder Location

**Main Archive Root:** `/Volumes/RENDER DISK/archive/`

**Subfolders:**
- `brands/` — Brand-specific archives
- `projects/` — Project-specific archives
- `workspace/` — Workspace/system archives

**Local Backup (for instant access):** `~/.openclaw/workspace/Kit/life/archive/`

**Sync:** Archive is NOT synced to Dropbox. It lives natively on the Render Disk for permanence and speed.

---

## Archive Policy

**Rule 1 — Permanent Path:** Archive contents live in `/Volumes/RENDER DISK/archive/` for permanence and backup protection. Local backup available via `Kit/life/archive/` for workflow use.

**Rule 2 — Dated Folders:** Every archive gets a YYYY-MM-DD prefix to preserve history.

**Rule 3 — README Documentation:** Every archive gets a README explaining what was moved, why, and reference links to current docs.

**Rule 4 — Never Delete:** Archive is additive only. If you need to surface something again, restore from archive. If nothing uses it for 2+ years, archive again with a note.

**Rule 5 — Brand Documents Backup:** Before rewriting BRAND.md, BRAND-STATUS.md, SKILLS-INDEX.md, always backup to archive with `.bak` extension.

---

## Cross-References

- **FILE-SYSTEM.md** — updated with canonical archive path
- **AGENTS.md** — updated with archive policy
- **MEMORY.md** — updated with permanent archive location

---

## Next Archive Steps

AgenticTrust full cleanup:
- ✅ BRAND.md rewritten and backed up
- ✅ BRAND-STATUS.md rewritten and backed up
- ✅ SKILLS-INDEX.md rewritten and backed up
- ⏳ Archive folders to be moved to `/Volumes/RENDER DISK/archive/brands/AgenticTrust/2026-07-25-full/` after final approval