---
file: GLOBAL-SKILLS-INDEX.md
purpose: Cross-brand skill registry. Kit reads this at every morning boot.
last_updated: 2026-04-21
updated_by: Kit
---

# Global Skills Index

## How This File Works

This is the registry of skills that work across brands. Brand-specific skills
live in `brands/{brand}/skills/` and are listed in each brand's SKILLS-INDEX.md.

When Kit needs a skill for a task, the resolution order is:
1. Brand-specific SKILLS-INDEX first
2. Global SKILLS-INDEX (this file) second
3. If neither has it, create a `pending_review` task proposing a new skill

Brand-specific skills override global skills for the same category, because
they carry voice rules and brand-specific guardrails.

## Active Skills

| Skill File | Purpose | Trigger | Reads | Writes | Approval Gate |
|---|---|---|---|---|---|
| stop-slop-REFERENCE | Remove AI writing patterns from prose (global reference for all email/content) | email refinement, content editing, quality check, stop slop | BRAND-VOICE files, offers | Refined prose (input/output tool) | None (refinement pass) | **Moved to `archive/2026-07-29-cleanup/`** |
| research | Real-time web search and intelligence gathering via Grok/X API | research, web search, intel | Grok API, search terms | intel notes, research summaries | None (read-only) |
| qmd | Local markdown search and document retrieval | search notes, find docs, knowledge graph query | Workspace markdown files | Search results, document excerpts | None |
| agentmail-email-drafting | Read incoming emails, classify, draft replies, submit for approval, send via AgentMail | Email inbox processing, draft review, send approval | AgentMail inbox, BRAND files | Mission Control tasks, email drafts | Jeff approves draft before send |
| code-simplifier | Refactor code for clarity, reduce complexity, remove AI code slop | code review, simplify, refactor, clean up | Source code files | Simplified code files | None (preserves behavior) |
| elevenlabs-calls | AI phone call generation and management via ElevenLabs + Twilio | phone call, voice call, AI call | Call scripts, voice settings | Call logs, recordings | None (script author approves) |
| blog-image-generator | Generate blog post hero images using Google Gemini | blog image, hero image, generate image | Blog post title/topic | Blog images (JPEG/PNG) | None (AI-generated) |
| x-posting | Post, reply, search, engage on X/Twitter via official v2 API | tweet, post, reply, search X, mention | X API v2, post content | Posts, replies, engagement logs | Jeff approves before public post |
| daily-review | Nightly revenue review and next-day planning | end of day, nightly review, plan tomorrow | Revenue metrics, task completion logs | Daily review summary, next-day plan | None (summary only) |
| qwen3-coder | Prompting strategies and task patterns for Qwen3-coder local model family | coding task with Qwen, local inference, prompt design | Qwen3-coder models, code context | Code generation, analysis | None (reference guide) |
| coding-agent-loops | Long-lived AI coding agents (Codex, Claude Code) in persistent tmux sessions with retry loops | coding project, multi-step code task, PRD-based workflow | Code files, PRD documents, agent context | Modified code, completed features, PR links | Jeff reviews code before merge |
| cron-guide | Schedule recurring tasks and automated workflows using OpenClaw cron | schedule task, cron job, recurring automation | Cron job specs, task definitions | Cron entries, execution logs | Jeff approves new cron jobs |
| agentmail-cli | Command-line interface for AgentMail operations (fetch, classify, draft, send) | agentmail operation, email CLI, inbox automation | AgentMail API, email messages | Email operations, logs | Depends on operation |
| mission-control-ops | Read, create, update, triage tasks and approvals in Mission Control | task management, approval triage, MC operation | Mission Control API | Tasks, approvals, status updates | None (CRUD operations) |
| genviral | Complete GenViral Partner API automation (create/schedule posts across TikTok, Instagram, etc.) | genViral, video post, schedule content, slideshow | GenViral API, content files, video assets | Scheduled posts, asset uploads, analytics | Jeff approves scheduling/spend |
| daily-research | Autonomous daily intelligence loop (news, competitors, demand signals) | daily research, morning scout, intelligence briefing | Firecrawl, competitor sites, news sources | Briefing, social drafts, competitor log, demand signals | None (read-only research) |
| site-health | Check production site availability and status | site health, uptime check, heartbeat | HTTP requests to prod URLs | Health status, alerting | None (monitoring only) |
| revenue-metrics | Pull revenue and business metrics across Stripe accounts | revenue, metrics, financial review, business KPIs | Stripe API, account data | Revenue summaries, charts, comparisons | None (read-only) |
| google-gemini-media | Gemini API for Nano Banana images, Veo video, Gemini TTS/audio understanding | gemini image, video generation, text-to-speech, audio analysis | Gemini API, media prompts, audio files | Generated media (images, video, audio) | None (AI-generated) |
| talking-head | Generate talking-head avatar videos from scripts | talking head video, avatar video, AI presenters | Script text, voice settings, Fal API | Avatar videos (MP4/WebM) | None (AI-generated) |
| instagram-slides | Turn blog posts into Instagram carousel slideshows with brand styling | instagram carousel, blog-to-slides, social carousel | Blog posts, brand assets, Gemini API | Carousel images, upload specs | Jeff reviews before posting |
| skill-creator | Create, improve, audit, and maintain AgentSkills | create skill, improve skill, audit skill | Skill templates, AgentSkills spec | SKILL.md files, skill documentation | None (creation/audit) |
| firecrawl | Official Firecrawl CLI for web scraping, search, crawling, browser automation | web scrape, crawl site, search web, browser automation | URLs, search queries, page specs | Clean markdown, scraped content | None (read-only scraping) |
| slack | Control Slack from OpenClaw (react to messages, pin/unpin items) | slack message, slack reaction, slack pin | Slack API, message targets | Reactions, pins, updates | None (message operations) |
| healthcheck | Host security hardening, risk tolerance configuration, OpenClaw deployment audits | security audit, hardening, version check, firewall | Host system, config files | Audit reports, hardening recommendations | Jeff reviews recommendations |
| node-connect | Diagnose OpenClaw node connection and pairing failures for mobile/Mac apps | node pairing, connection error, device pair | Device logs, config files, network status | Diagnostic reports, connection fixes | None (diagnostic) |
| openai-whisper | Local speech-to-text with Whisper CLI (no API key required) | transcribe, speech-to-text, audio-to-text | Audio files (MP3, WAV, M4A) | Text transcripts | None (local only) |
| clawhub | ClawHub CLI for searching, installing, updating, publishing agent skills | install skill, update skill, publish skill, find skill | Clawhub.com registry, skill packages | Installed skills, version updates | Jeff approves new skill installs |
| weather | Get current weather and forecasts via wttr.in or Open-Meteo | weather, forecast, temperature, climate | Location names, weather API | Weather summaries, forecasts | None (public data) |
| xurl | CLI tool for authenticated X/Twitter API requests (post, reply, search, DMs, media) | tweet, reply, quote, DM, search X, upload media | X API v2, content | Posts, replies, DMs, media uploads | Jeff approves public posts |
| xpost | Deprecated (replaced by x-api) | N/A | N/A | N/A | N/A |
| github | GitHub operations via `gh` CLI (issues, PRs, CI runs, code review, API queries) | github issue, PR, CI check, code review | GitHub API, repos, workflows | Issues, PRs, comments, run logs | Jeff reviews code changes |
| 1password | Set up and use 1Password CLI (op) for secret management | 1password, op CLI, secret, credential | 1Password vault, environment | Environment variables, secrets | None (credential retrieval) |
| gemini | Gemini CLI for one-shot Q&A, summaries, and generation | gemini ask, summarize, generate, gemini Q&A | Gemini API, input text | Answers, summaries, generated content | None (AI assistance) |
| discord | Discord ops via message tool | discord message, discord post, channel update | Discord API, channel targets | Messages, posts, updates | Jeff approves external posts |
| things-mac | Manage Things 3 via `things` CLI (add/update projects/todos, read/search/list) | add task, things todo, project, search tasks | Things 3 database, task specs | Tasks, projects, inbox updates | None (local app) |
| caveman | Ultra-compressed communication mode — cuts token usage ~75% by dropping articles/filler/hedging | caveman mode, talk like caveman, less tokens, be brief | SOUL.md, context | Compressed reply | None (style pass) |
| caveman-commit | Generate ultra-compressed git commit messages | commit message, summarize changes | diff output | Commit message | None |
| caveman-compress | Compress existing text into caveman style | compress text, make it terse, shorter | Any text | Compressed text | None |
| caveman-help | Guide to caveman communication rules and intensity levels | help with caveman, how does it work | — | Rules explanation | None |
| caveman-review | Review text for AI slop patterns and suggest caveman rewrites | review for slop, clean up writing | Draft prose | Revised prose | None |
| opencli-oneshot | Generate a single OpenCLI command from a URL + goal description (4-step process) | opencli command, one-shot CLI, generate command | URL + goal | CLI command file | None |
| opencli-explorer | Full site exploration and OpenCLI adapter development | opencli explore, full site, multi-command | URL + goal | CLI adapter files | None |
| opencli-browser | OpenCLI browser automation commands and network capture | opencli browser, capture API, network | — | Browser commands | None |
| opencli-autofix | Auto-fix broken OpenCLI adapter commands | opencli fix, autofix | Broken CLI file | Fixed CLI file | None |
| opencli-usage | Reference guide for OpenCLI commands and patterns | opencli help, usage reference | — | Reference info | None |
| opensrc | Fetch and read source code from npm, PyPI, crates.io, or GitHub packages | source code, read package, opensrc path | Package name | Source code paths | None |
| brightbean-studio | Self-hosted social media management platform — post, schedule, approve across Facebook, Instagram, LinkedIn, TikTok, YouTube, Pinterest, Threads, Bluesky, Google Business Profile, Mastodon | brightbean studio, social media dashboard, schedule posts, social approval workflow | BrightBean URL + API token + workspace ID | Posts, scheduled content, approval status | Jeff reviews before connecting new platforms |
| video-frames | Extract frames or short clips from videos using ffmpeg | extract frames, clip video, ffmpeg operation | Video files, frame specs | Image sequences, video clips | None (utility) |
| crowd-reply | **[DECOMMISSIONED 2026-06-01]** Reddit engagement via CrowdReply API — subscription cancelled, no credits. Preserved for historical reference only. Re-evaluate ROI in ~6 months. | crowd reply, reddit comment, crowdreply task | crowd-reply-training.md, reddit-brand-commenting.md | CrowdReply API, daily notes | Jeff approved autonomous posting for TrustOffice |
| morning-brief | Canonical Morning Brief — daily decision-forcing brief across portfolio (CRON-D-BRIEF, weekdays 7 AM MT) | morning brief, daily brief, CRON-D-BRIEF | Per-brand BRIEF-CONFIG.md, LIVE-STATE.md, BRAND-STATUS.md, DECISIONS.md | Mission Control task, kit/briefs/YYYY-MM-DD-morning-brief.md, brand-specific targets | None (read-only brief generation) |
| analytics | GA4 analytics pull — traffic data for all portfolio properties via Google Analytics Data API | ga4, analytics, traffic, sessions, spike check | GA4 API (service account credentials in 1Password), scripts/ga4-pull.py | Traffic reports, spike alerts, weekly summaries | None (read-only data pull) |
| rumble-ads | Manage advertising campaigns on Rumble via RAC (Rumble Advertising Center) — create campaigns, set targeting, monitor performance, optimize CPM spend | rumble ads, rumble advertising, RAC, rumble campaign | RAC API, ads.rumble.com dashboard | Campaign configs, performance reports | Jeff approves spend before launch |
| lead-enrichment | Enrich lead and prospect information using Autobound API — contact details, company signals, behavioral profiles (DISC), intent data, and personalized outreach content generation | enrich lead, enrich prospect, find email, find contact info, lookup contact, company signals, intent data, prospect research, lead intelligence, autobound, signal search, behavioral profile, DISC profile | Autobound API, brand sender emails | Enriched prospect records, generated outreach drafts | No approval for enrichment; Jeff approves content sends |
| railway-deploy | Deploy web apps (frontend + backend monorepos) to Railway with Dockerfile fallbacks, MongoDB setup, healthchecks, and custom domains | deploy to railway, railway build failure, railway monorepo, railway healthcheck, railway dockerfile | Railway CLI, Dockerfile, nginx config | Deployments, DNS configs, healthcheck endpoints | None (infrastructure ops) |
|| hn-karma-scan | Scan Hacker News for high-signal threads and draft humanized comment suggestions for Jeff to rewrite before posting — builds authentic karma for future Show HN | hn scan, hacker news scan, hn replies, hn karma, hn karma building scan, find hn opportunities, draft hn comment | news.ycombinator.com, prior scan state | HN findings JSON, chat summary | None (drafts for Jeff review only) |
|| tjb-provider-enrichment | Enrich TJB city page provider data (photos, emails, cost ranges, descriptions, hospital info, NICU levels, Medicaid) using cheapest models first with cost-optimized tier escalation | enrich city, enrich providers, enrich city page, tjb-provider-enrichment, provider enrichment | cities.ts, provider websites, Bornbir.com, Perplexity, Firecrawl (fallback) | Enriched provider data patched into cities.ts | None (data enrichment only) |
| maestro-mobile-testing | Test mobile apps on iOS simulators and Android emulators via Maestro MCP — write YAML flows, inspect UI, take screenshots, run E2E tests | mobile test, app test, simulator, emulator, maestro, maesto flow | Maestro MCP server, device simulators/emulators | Test results, screenshots, view hierarchies | None (testing only) |
| feynman-research | Research-first methodology adapted from Feynman (GetCompanion, MIT): evidence-over-fluency, source provenance, no fabrication, durable on-disk artifacts. Covers deep research, literature review, paper critique, paper-code audit, replication plan, experiment loop, research watch, ML recipe, source comparison, large-document (RLM) summarization. | deep research, literature review, paper critique, audit paper vs code, replication plan, run an experiment, experiment loop, optimize [metric] iteratively, research watch, ML training recipe, compare sources, summarize this paper/doc, "research [substantive topic]" | web_search, web_extract, firecrawl-research-papers (paper sources), delegate_task (researcher/writer/verifier/reviewer roles), execute_code (RLM chunking, dataset checks), cronjob (watches) | research artifacts in outputs/ (plan, research, draft, cited, review, provenance), CHANGELOG.md lab notebook | None (read-only research; autoresearch/replication need explicit env confirmation before running code) |

## What Belongs in Global Skills

A skill belongs in `/workspace/skills/` (and this index) if ALL of the following are true:

- It works the same way across two or more brands without modification
- It does not contain brand-specific voice rules, audience language, or guardrails
- It is reusable infrastructure: a tool wrapper, a research pattern, a file operation,
 a generic workflow, or a research methodology
- It would be wasteful or error-prone to maintain duplicate copies per brand

**Examples of skills that belong here:**
- Generic web research patterns (competitor scans, market sizing)
- File operation utilities (PDF extraction, CSV cleanup, image resizing)
- Tool wrappers (Apify scrapers, 1Password retrieval, Mailercloud generic ops)
- Cross-brand reporting templates (cost reports, model usage summaries)
- Generic outreach research (finding contact info, qualifying business size)
- Calendar and date operations
- Data validation and contradiction-detection patterns

**Examples of skills that do NOT belong here (live in brand folders instead):**
- Anything that writes in a specific brand's voice
- Anything that uses persona-specific verbatim language
- Anything that references a specific brand's offers, CTAs, or pricing
- Anything with brand-specific approval gates or guardrails
- Brand-specific cron jobs and their workflows

**The acid test:** If you copy a skill into a second brand and it produces
usable output without editing the voice, audience, or product references,
it belongs here. If it needs even one find-and-replace per brand, it doesn't.

## Adding a New Skill

When Kit (or Jeff) wants to add a skill to this index:

1. Confirm it passes the acid test above
2. If it's currently a brand-specific skill being promoted to global, check
 that no brand-specific language remains. Strip it if needed.
3. Add a row to the Active Skills table with all six columns filled
4. If the skill is replacing duplicated brand-specific copies, archive the
 duplicates and update each brand's SKILLS-INDEX.md to point here
5. Create a `pending_review` task notifying Jeff of the addition

## Removing or Demoting a Skill

If a global skill turns out to need brand-specific variants:

1. Move it to the brand-specific skills folder for the brand that needs it most
2. Note the demotion in the Decisions log of the affected brand
3. Remove the row from this index
4. Create a `pending_review` task explaining why

Never delete skill files. Archive them to `/workspace/skills/archive/`
with a note explaining the demotion.

## Maintenance

Kit reviews this file:
- Every morning during the boot sequence (read-only check)
- During the monthly should-have-caught review — looking for patterns where
 Kit reinvented work that should have become a global skill
- Whenever Kit notices duplicated logic across two brand-specific skills
 (those are candidates for promotion to global)

When Kit spots a candidate for promotion or demotion, he creates a
`pending_review` task — he never moves skills between layers without
Jeff's approval.
