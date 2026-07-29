# Skills Index Policy
<!-- ROUTING: Load when adding, removing, or demoting a global skill -->

## What Belongs in Global Skills

A skill belongs in `/workspace/skills/` (and this index) if ALL of the following are true:

- It works the same way across two or more brands without modification
- It does not contain brand-specific voice rules, audience language, or guardrails
- It is reusable infrastructure: a tool wrapper, a research pattern, a file operation, a generic workflow, or a research methodology
- It would be wasteful or error-prone to maintain duplicate copies per brand

**Acid test:** If you copy a skill into a second brand and it produces usable output without editing the voice, audience, or product references, it belongs here. If it needs even one find-and-replace per brand, it doesn't.

## Adding a New Skill

1. Confirm it passes the acid test
2. If promoting from brand-specific, strip brand-specific language
3. Add a row to the GLOBAL-SKILLS-INDEX.md table with all six columns filled
4. If replacing duplicated brand-specific copies, archive the duplicates and update each brand's SKILLS-INDEX.md
5. Create a `pending_review` task notifying Jeff

## Removing or Demoting a Skill

1. Move skill files to the brand that needs it most (or archive if fully retired)
2. Note the demotion in the affected brand's Decisions log
3. Remove the row from GLOBAL-SKILLS-INDEX.md
4. Create a `pending_review` task explaining why
5. Never delete skill files — archive to `/workspace/skills/archive/` with a note

## Maintenance

Kit reviews this file:
- Every morning during boot (read-only check)
- During monthly should-have-caught review
- When duplicated logic is spotted across brand-specific skills

When Kit spots a promotion/demotion candidate, create a `pending_review` task — never move skills between layers without Jeff's approval.