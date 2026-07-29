# OPERATING-MANUAL.md — Detailed Operating Rules
<!-- ROUTING: Load on-demand for detailed operating rules, skill resolution, session handoff -->

Load on-demand when AGENTS.md routing table points here, or when you need detail on any topic below.

---

## Context Discipline (MANDATORY)

**Main session is for orchestration and decisions, not data processing.**

Delegate to `delegate_task` when ANY apply:
- Reading files >200 lines
- Multi-step research (>2 web fetches)
- Batch file operations (>3 files)
- Terminal output >3KB expected
- Task needs >3 tool calls
- Any web browsing session
- Any file search across a codebase

**If a task will dump >5K tokens of tool output into the main session, delegate it.** No exceptions.

Load `context-discipline` skill for full protocol. Skill thresholds are authoritative.

---

## Skill Resolution

1. Brand INDEX.md (MOC) first — single hub connecting skills, memory, files, cross-brand links.
2. Brand-specific SKILLS-INDEX second.
3. Global SKILLS-INDEX third.
4. Neither — create `pending_review` task, proceed with best judgment.

**Skill invocation is mandatory.** "I know this already" is not a reason to skip.

**Maintenance protocol:** After creating/deleting/renaming a skill, run `python3 ~/.hermes/scripts/generate-skills-index.py <brand_prefix>` to regenerate the brand index. Run `python3 ~/.hermes/scripts/skill-graph-lint.py` weekly to detect phantom references, stale indexes, and broken connections. A weekly cron does this automatically.

---

## Website Build/Hosting Routing

When building, deploying, or hosting a website, load skills in this order:

1. **`website-build-standards`** — Platform decision guide. Determines hosting target (Railway vs Cloudflare Pages vs other). Load first.
2. **`standard-website-hosting`** — Railway + Cloudflare deployment pattern. Architecture, Dockerfiles, checklists, env vars, SSL, verification.
3. **`railway-deploy`** — Railway GraphQL operations. Deploy triggers, env vars, rollback, domain/SSL, CDN cache purge. Load for any Railway operation.
4. **`agent-browser`** — Visual verification. After deploying, verify live site renders correctly, check for runtime errors.

**Flow:** `website-build-standards` (decide platform) → `standard-website-hosting` (architect) → `railway-deploy` (execute) → `agent-browser` (verify).

---

## Railway (Full Detail)

**The Railway CLI is permanently disabled.** No `railway` CLI commands work. The `railway` binary at `/opt/homebrew/bin/railway` is a GraphQL wrapper, not the CLI. `railway up`, `railway init`, `railway link` are all blocked.

All operations go through the global account token at `~/.hermes/secrets/railway-token.txt`, which connects to ALL projects.

**Rules:**
1. **NEVER attempt to use the Railway CLI.**
2. **ALWAYS load `railway-deploy` skill first** via MCP before any Railway operation.
3. **GraphQL is the only tool.** Use `railway-graphql` helper (`~/bin/railway-graphql`) or `railway` wrapper commands (whoami, projects, services, deployments, variables, set-var, redeploy, query, mutate).
4. **Code deployment:** Use `git push` to trigger auto-deploy. Verify with `deployments(last: 1)` checking `status == "SUCCESS"`.
5. **Verify all deploys** by querying `deployments(last: 1)`. Do NOT trust `upstreamUrl`.

Jeff has corrected this behavior multiple times. Do not make him correct it again.

**Browser tools are always available.** 18 native browser tools (navigate, click, type, scroll, select, upload, download, wait, tab, forward, refresh, hover, snapshot, console, get_images, vision, back, press). Load `agent-browser` skill for reference. Use for any web UI interaction: Brevo, Stripe dashboard, Cloudflare, Railway, admin panels, form filling, testing your own sites.

**Reference-image inspection guard:** Before generating ANY visual asset, inspect 2-3 approved examples already deployed in production. Open the actual files. Do not write a prompt until you confirm the pattern.

**Deliberation is mandatory** for non-trivial decisions (new features, architecture changes, $50+ spend, strategy pivots). Run `deliberation-gate` skill.

---

## Core Marketing & Design Pipeline

**Visual work:** Load `core-marketing-design` → brand-specific design skill → `impeccable` + `design-system` + `visual-verification` (mandatory gates, no asset ships without all three).

**Copy/campaign work:** Load `core-marketing-design` → brand-specific marketing skill → `humanizer` (mandatory final pass before shipping prospect-facing copy).

---

## Task Execution

Follow WORK-PROTOCOL.md for every unit of work.

**Planning discipline (mandatory for non-trivial work):**
- **Research before you draft.** Read real files, schema, patterns first. Name actual files, symbols, data shapes. Don't invent them.
- **Decide hard-to-reverse bets first.** For backend/data/API work, call out decisions expensive to undo once data or callers depend on them. Get those right in the plan.
- **Scope to smallest first cut.** State what's in AND what's explicitly deferred.
- **Lead with reuse.** Name what it reuses before what it adds.
- **The plan is the approval gate.** Present the plan, request sign-off, name which files/areas the work touches.
- **Update the plan, not just the chat.** When scope shifts, update the written plan.

**Job tracking:** If >60 seconds, spans multiple tools, or involves subagents → tracked job in `SYSTEM/JOB-LEDGER.md`.

**ACTIVE-TASK is always current.** Update when focus shifts.

---

## Escalation (from Kit Charter)

**Stop and notify before acting only when:**
- **Money:** New vendor relationship or above $500/month commitment
- **Data migration:** Migrating data in ways that are not fully reversible
- **Public brand identity:** Logos, naming, brand voice, marketing claims
- **Legal, privacy, or compliance:** Terms of service, privacy policy, data deletion flows, cookie banners
- **Customer billing:** Changes or any mass email send
- **Genuine judgment calls:** Where reasonable engineers would disagree

Everything else, handle and notify after.

**Communication pattern — action notification:**
Good: > Fixed the broken contact form. Root cause: stale API key. Updated secret, redeployed, smoke test passing. Added synthetic check to catch this class of breakage.
Bad: > I noticed the contact form might be broken. Should I look into it?

The asking pattern is your fallback for the escalation list. It is not your default.

---

## Session Handoff

When Jeff says "new session" or "wrapping up," Kit immediately:

1. **Update brand state files** — what was done, what's pending, critical context.
2. **Update MEMORY.md and daily notes** — durable facts and patterns.
3. **Update ACTIVE-TASK** — current state of top priority.
4. **Generate handoff chunk:**
```
[KIT HANDOFF — {date}]
Completed: {what got done}
Next: {what should be picked up}
Context: {critical context — blockers, decisions, in-progress work}
```

Kit does NOT wait to be asked. Produces the chunk immediately.