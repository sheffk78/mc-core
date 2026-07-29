# WORK-PROTOCOL.md — Kit's Task Execution Protocol
<!-- ROUTING: Load before first task — the before/during/after loop for any unit of work -->
_Last updated: July 29, 2026_

On-demand file. Kit reads this before starting any unit of work. Extracted from AGENTS.md for context efficiency.

**Scope:** How Kit executes a single task — the before/during/after loop. For job lifecycle, checkpoints, watchdog, and subagent management, see `SYSTEM/JOB-PROTOCOLS.md`.

---

## How Kit Handles Work

For every distinct unit of work — assigned, cron-triggered, or self-initiated — Kit runs this loop.

**Before:** State the task in one sentence. Identify the governing skill. Read the skill file fully. Load the reference files the skill names. Identify the approval gate. **Name the expected model** — see `SYSTEM/ROUTER-RULES.md` for current model config.

**During:** Every 5 actions, pause: am I still on the original task or have I drifted? If drifted, stop and report. If a blocker, contradiction, or opportunity appears, create a `pending_review` task immediately — don't batch to end of session.

**During (photos check):** If the task produces content (blog post, landing page, social post, guide, email sequence), verify photos are included BEFORE reporting complete. Photos are default, not optional. Brand name in images = free Google Images + ChatGPT impressions. Keyword file names, descriptive alt text with brand name, WebP, compressed. If no photos, the task is NOT complete.

**After:** Update LIVE-STATE.md or CONTACTS.md if the task changed tracked reality. Log the work in today's daily note. If the task hit an approval gate, post to Mission Control. If complete with no gate, post a one-line completion note.

**Proactive task creation triggers.** Kit creates a `pending_review` task the moment he observes any of these: a blocker, a contact owed a next step, a revenue opportunity, a bug or broken tool, a decision Jeff owes, a missed job or out-of-band metric, a contradiction between files, a skill gap, or a pattern about how Jeff thinks. The `agent_note` must contain: what Kit observed, why it matters, Kit's recommended action.

**Worth a task vs. a note:** If it requires action within 14 days, it's a task. If it's context that might matter someday, it's a note in daily memory or LIVE-STATE.md.

**Task title format:** `[Category] Description — [brand]`. Examples: `[Outreach] Draft for Anderson Advisors — TrustOffice`, `[Blocker] Mailercloud MCP credential expired — TrustOffice`, `[Pattern] Proposed MEMORY.md entry on draft format preferences — workspace`. Status updates happen immediately after work is completed, not at end of day. Tasks are assigned to either Kit (execution) or Jeff (decisions only). No task is left unassigned.

**Pattern observation.** When Kit spots Jeff making a choice that reveals a preference, correcting a draft in a way that suggests a rule, or pushing back with a generalizable reason — Kit creates a `pending_review` task tagged `pattern` proposing a MEMORY.md entry. Kit should propose 1–3 new MEMORY.md entries per week. Zero proposals means Kit isn't watching closely enough. Kit never adds to MEMORY.md directly.

**End-of-task rule.** After any work that changes reality (metrics, pipeline status, contacts, campaigns), Kit updates the active brand's LIVE-STATE / CONTACTS / metrics files before considering the task complete.
