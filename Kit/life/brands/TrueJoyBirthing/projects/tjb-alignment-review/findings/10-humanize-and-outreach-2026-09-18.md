# Addendum 10 Ã¢ÂÂ Humanize Pass 6 + 5-Touch Outreach Operationalization (2026-09-18)

**Date:** 2026-09-18
**Author:** Content/skill subagent (Jeff-directed)
**Scope:** (1) Strengthen `skills/humanize-content/SKILL.md` Pass 6 per Jeff's 2026-09-18 directive; (2) Operationalize the 5-touch professional-outreach sequence; (3) this addendum. No website code changed, nothing deployed.

---

## Change 1 Ã¢ÂÂ humanize-content SKILL.md Pass 6 (PRIORITY signal reframe)

**What changed:** Pass 6 was rewritten from a cautious, tiered "imperfection injection" pass ("deliberate errors are the *weakest* lever, apply sparingly") into a **PRIORITY signal** Ã¢ÂÂ the primary anti-AI-template defense. Two pillars:

- **Pillar 1 Ã¢ÂÂ Natural human variance (apply by default):** controlled variance is now expected texture, not a risk to avoid Ã¢ÂÂ default-on constructions (sentence-initial "And"/"But", comma splices, fragments, asides, colloquial phrasing) plus *occasional* imperfect grammar/typos (Ã¢ÂÂ¤1 per 500Ã¢ÂÂ1000 words) as normal human texture. Never on data (numbers, names, citations, prices, URLs, schema, CTAs).
- **Pillar 2 Ã¢ÂÂ Deep per-city customization (the PRIMARY defense):** real local providers/hospitals, named specifics (street, county office, NICU level, fees, Medicaid posture, named peers), and local texture per city page. Un-replicable across properties and genuinely useful Ã¢ÂÂ exactly what helpful-content review rewards; also serves E-E-A-T (~3.4ÃÂ post-March-2026).

**Policy-safe:** goal = pass Google helpful-content review; present variance as natural human texture, **never spam-pattern stuffing** (no uniform cadence, no repeated imperfection template across pages). Documented as reflecting Jeff's explicit 2026-09-18 directive.

**Coherence fixes:** the Trigger-map email row ("no typos, no Tier C, ever") and the "What NOT to do" line ("Tier C abuse") referenced the retired tier system Ã¢ÂÂ updated to reference Pass 6 Pillar 1 / email rule so no dangling "Tier C" remains.

**File:** `skills/humanize-content/SKILL.md` (Pass 6, Trigger map row, What-NOT-to-do line).

---

## Change 2 Ã¢ÂÂ 5-Touch Professional Outreach Operationalization

**What was found:** The 5-touch sequence spec lives in `findings/09-outreach-reframe.md` (Email 1Ã¢ÂÂ5, added 2026-09-18). The live cadence lives in `TRUEJOYBIRTHING-CRON-JOBS.md` (**TJB G57** Mon/Wed/Fri 06:30 MT + **Catch-Up Queue Builder/Sweep** daily), driven by `~/.hermes/scripts/tjb-outreach-catchup.py`, `tjb-batch-outreach.py`, `tjb-outreach-send.py`, state in `~/.hermes/state/`, logs in `~/.hermes/logs/` (send-log + opt-out blocklist). Sends go via VPS `mail_client.py` (`shelbi@truejoybirthing.com`) per `OUTREACH-SENDING-POLICY.md`. **Critical gap:** the existing catch-up scripts handle **first-touch only** Ã¢ÂÂ there is no multi-touch follow-up logic, so E2Ã¢ÂÂE5 are not currently planned.

**What was wired:** Created `outreach/5-TOUCH-CADENCE-OPERATIONALIZATION.md` mapping the sequence to MailerCloud:
- **Registry list:** `wHHZHw` Ã¢ÂÂ "TJB Provider Outreach - Engaged" (verified 2026-09-18 via `POST /lists/search`, 22 contacts).
- **Tag schema (9 tags):** `outreach-e1`Ã¢ÂÂ¦`outreach-e5` (touch state) + `outreach-replied`, `outreach-optout`, `outreach-downloaded`, `outreach-ambassador` (status). Pre-create via verified `POST /tags` endpoint (raw `Authorization`, no Bearer, curl).
- **Day-counts:** E1 day 0 Ã¢ÂÂ E2 +5Ã¢ÂÂ7d Ã¢ÂÂ E3 +10Ã¢ÂÂ14d after E2 (no-reply only) Ã¢ÂÂ E4 +4Ã¢ÂÂ6wk after E3 (no-reply + no-download) Ã¢ÂÂ E5 +8Ã¢ÂÂ10wk after E3 (final). Reply/opt-out stop the sequence; download routes to ambassador.
- **Operational home recorded** (every file path above) + a concrete **next-run execution plan** that extends the cadence controller to read the send-log + MailerCloud tags and emit the correct next touch, applying Gate 0c + budget caps and humanize Passes 1/3/4 with real per-city anchors.

**Hard-rule compliance:** no new cron created (cadence rides existing G57 + Catch-Up schedule); no secrets printed; no brand marks; no other brand's skills touched; no MailerCloud state mutated (tags documented as the run's prerequisite, not created live Ã¢ÂÂ per "do not deploy").

**Files:** `outreach/5-TOUCH-CADENCE-OPERATIONALIZATION.md` (new).

---

## Verification

- Pass 6 rewrite applied and diff-confirmed; Tier-C references removed/updated; file remains valid Markdown.
- `wHHZHw` "TJB Provider Outreach - Engaged" confirmed present (22 contacts) via live `POST /lists/search`.
- `POST /tags` endpoint confirmed from `skills/mailercloud-control/SKILL.md`; auth contract confirmed from `mailercloud-integration.md`.
- Both new/modified docs are file-path-complete and map all 5 touches to list `wHHZHw` + tags with day-counts.

## Open items for next run (not executed Ã¢ÂÂ out of deploy scope)

1. Pre-create the 9 MailerCloud tags (call provided in the operationalization doc).
2. Extend `tjb-batch-outreach.py` / add `tjb-outreach-cadence.py` to drive E2Ã¢ÂÂE5 from send-log + tags (build is the next operator's step; this task only wired the plan).
3. Confirm reply-detection feeds `outreach-replied`/`outreach-optout` tags and download signal feeds `outreach-downloaded` Ã¢ÂÂ ambassador route (`wHHZHH`).
