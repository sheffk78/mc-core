# TOOLS.md — Index

*How* to invoke Kit's toolchain. For *whether*/*when* (approval gates, path selection, model choice), see **AGENTS.md**. Voice → SOUL.md. Work cycle → HEARTBEAT.md.

**Read pattern:** On demand. Load only the one file you need from `TOOLS/` — never this index plus a section. If you find a rule here that belongs in AGENTS.md (or vice versa), that's drift — flag via `pending_review` task.

---

## Tool index

| Need to... | Read |
|---|---|
| Assign/execute coding work (Path A/B/C) | `TOOLS/coding-paths.md` |
| Hit the Mission Control API (tasks, approvals, costs, files) | `TOOLS/mission-control-api.md` |
| Post to X / reply / search | `TOOLS/x-api.md` |
| Post social content (TikTok/IG/YT/Pin/LI/FB) | `TOOLS/social-posting-api.md` |
| ~~Post Reddit comments via CrowdReply~~ (ARCHIVED — decommissioned 2026-06-01) | — |
| Send email (any brand) | `TOOLS/mailercloud.md` |
| Scrape social / web / leads | `TOOLS/apify.md` |
| Search markdown across workspace + PARA | `TOOLS/markdown-search.md` |
| Run a >5min background process | `TOOLS/tmux.md` |
| Retrieve a credential | `TOOLS/1password.md` |
| Read repos, commits, code | `TOOLS/github-cli.md` |
| Look up a Discord channel ID | `TOOLS/discord.md` |
| Pick a timeout for a shell or LLM call | `TOOLS/exec-timeouts.md` |
| Pick a tool by purpose (testing, monitoring, CI, etc.) | `TOOLS/SELECTION-GUIDE.md` |
| Deploy to Railway | `TOOLS/railway-deploy.md` (or `skills/railway-deploy/SKILL.md`) |
| Generate content/images/video with Google AI | `TOOLS/google-ai.md` |
| Access YouTube channel data / upload | `TOOLS/youtube.md` |
| Connect apps / automate workflows via Zapier | `TOOLS/zapier.md` |
| Run mobile app tests on iOS/Android | `TOOLS/maestro.md` |
| Access Google Workspace (Gmail, Calendar, Drive, Sheets, Docs) | `TOOLS/google-ai.md` § 7a (or `skills/google-workspace/SKILL.md`) |

---

## Global rules

1. **Approval gates are in AGENTS.md.** TOOLS/ files show commands, not permission to run them. Posting, sending, deploying, and pushing are *always* approval-gated unless AGENTS.md explicitly says otherwise for the current stage.
2. **Never use the 1Password Personal vault.** Credentials live in `--vault "OpenClaw"`.
3. **Never cross-contaminate brand lists, channels, or accounts.** Check the brand's OFFERS.md / BRAND-VOICE.md before any outbound content.
4. **Railway: full access via GraphQL API.** Token at `~/.hermes/secrets/railway-token.txt`. See `TOOLS/railway-deploy.md` for full guide. Never use Railway CLI (broken in headless mode). Never ask Jeff for the token.
5. **Log costs** after LLM work via Mission Control `/api/v1/costs`.
6. **Flag retired tooling.** If you find references to `xpost`, `gemma4-deep`, `gemma4-fast`, `qwen2.5-coder:32b`, `qwen3-coder:480b-cloud`, or `smartabodetechs.com`, open a `pending_review` task.