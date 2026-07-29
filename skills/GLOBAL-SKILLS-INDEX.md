---
file: GLOBAL-SKILLS-INDEX.md
purpose: Cross-brand skill registry. Kit reads this at morning boot.
last_updated: 2026-07-29
---

# Global Skills Index

Resolution order: 1) Brand SKILLS-INDEX → 2) This file → 3) `pending_review` task.
Brand skills override global for same category (they carry voice rules + guardrails).
Skill add/remove/demote policy: `SKILLS-INDEX-POLICY.md`.

## Active Skills

| Skill | Purpose | Trigger | Approval |
|---|---|---|---|
| markdown-search | Local markdown search and document retrieval | search notes, find docs | None |
| research | Real-time web search and intelligence gathering | research, web search, intel | None |
| agentmail-email-drafting | Read emails, classify, draft replies, send via AgentMail | email inbox processing, draft review | Jeff approves before send |
| agentmail-cli | CLI for AgentMail operations (fetch, classify, draft, send) | agentmail operation, email CLI | Depends on operation |
| code-simplifier | Refactor code for clarity, remove AI code slop | code review, simplify, refactor | None |
| coding-agent-loops | Long-lived AI coding agents in persistent tmux sessions | coding project, multi-step code task | Jeff reviews before merge |
| cron-guide | Schedule recurring tasks and automated workflows | schedule task, cron job | Jeff approves new crons |
| mission-control-ops | Read, create, update, triage tasks and approvals | task management, MC operation | None |
| x-posting | Post, reply, search, engage on X/Twitter via v2 API | tweet, post, reply, search X | Jeff approves public posts |
| xurl | Authenticated X/Twitter API requests (post, reply, search, DMs, media) | tweet, reply, quote, DM, search X | Jeff approves public posts |
| social-posting-api | GenViral Partner API — post/schedule across TikTok, Instagram, etc. | genViral, video post, schedule content | Jeff approves scheduling/spend |
| nightly-revenue-review | Nightly revenue review and next-day planning | end of day, nightly review | None (summary only) |
| daily-research | Autonomous daily intelligence loop | daily research, morning scout | None (read-only) |
| site-health | Check production site availability | site health, uptime check | None (monitoring) |
| revenue-metrics | Pull revenue and business metrics across Stripe | revenue, metrics, financial review | None (read-only) |
| blog-image-generator | Generate blog hero images using Google Gemini | blog image, hero image | None |
| google-gemini-media | Gemini API for Nano Banana images, Veo video, TTS/audio | gemini image, video generation | None |
| talking-head | Generate talking-head avatar videos from scripts | talking head video, avatar video | None |
| instagram-slides | Turn blog posts into Instagram carousels with brand styling | instagram carousel, blog-to-slides | Jeff reviews before posting |
| elevenlabs-calls | AI phone call generation via ElevenLabs + Twilio | phone call, AI call | None |
| lead-enrichment | Enrich prospects using Autobound API | enrich lead, find email, prospect research | Jeff approves content sends |
| qwen3-coder | Prompting strategies for Qwen3-coder local model family | coding task with Qwen | None |
| firecrawl | Web scraping, search, crawling, browser automation | web scrape, crawl site, search web | None |
| railway-deploy | Deploy web apps to Railway with Dockerfile fallbacks | deploy to railway, railway build | None (infra ops) |
| github | GitHub operations via `gh` CLI | github issue, PR, CI check | Jeff reviews code |
| 1password | 1Password CLI for secret management | 1password, op CLI, credential | None |
| discord | Discord ops via message tool | discord message, channel update | Jeff approves external posts |
| things-mac | Manage Things 3 via `things` CLI | add task, things todo | None |
| video-frames | Extract frames/clips from videos using ffmpeg | extract frames, clip video | None |
| brightbean-studio | Self-hosted social media management platform | social media dashboard, schedule posts | Jeff reviews new platforms |
| maestro-mobile-testing | Test mobile apps on iOS/Android via Maestro MCP | mobile test, simulator, emulator | None |
| feynman-research | Research-first methodology — evidence over fluency | deep research, literature review | None (read-only) |
| rumble-ads | Manage ad campaigns on Rumble via RAC | rumble ads, rumble advertising | Jeff approves spend |
| analytics | GA4 analytics pull — traffic data for all properties | ga4, analytics, traffic | None (read-only) |
| morning-brief | Daily decision-forcing brief across portfolio (CRON-D-BRIEF) | morning brief, daily brief | None |
| lead-magnet-pipeline | Lead magnet creation pipeline | lead magnet, content pipeline | Jeff approves sends |

## Archived / Decommissioned

| Skill | Status | Date | Archive Location |
|---|---|---|---|
| crowd-reply | Decommissioned | 2026-06-01 | `archive/2026-07-29-cleanup/skills-crowd-reply/` |
| stop-slop-REFERENCE | Archived | 2026-07-29 | `archive/2026-07-29-cleanup/` |
| xpost | Deprecated (replaced by x-api) | — | — |