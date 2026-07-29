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
| Post social content (TikTok/IG/YT/Pin/LI/FB) | `TOOLS/genviral.md` |
| Post Reddit comments via CrowdReply | `TOOLS/crowdreply.md` |
| Send email (any brand) | `TOOLS/mailercloud.md` |
| Scrape social / web / leads | `TOOLS/apify.md` |
| Search markdown across workspace + PARA | `TOOLS/qmd.md` |
| Run a >5min background process | `TOOLS/tmux.md` |
| Retrieve a credential | `TOOLS/1password.md` |
| Read repos, commits, code | `TOOLS/github-cli.md` |
| Look up a Discord channel ID | `TOOLS/discord.md` |
| Pick a timeout for a shell or LLM call | `TOOLS/exec-timeouts.md` |
| Pick a tool by purpose (testing, monitoring, CI, etc.) | `TOOLS/SELECTION-GUIDE.md` |
| Deploy to Railway (full-stack, monorepo, databases, domains) | `TOOLS/railway-deploy.md` (or `skills/railway-deploy/SKILL.md`) |
| Generate content/images/video with Google's AI (Gemini, Imagen, Veo) | `TOOLS/google-ai.md` or Rule 7 below |
| Access YouTube channel data / upload | `TOOLS/youtube.md` or Rule 8 below |
| Connect apps / automate workflows via Zapier | `TOOLS/zapier.md` |
| Run mobile app tests on iOS simulators and Android emulators | `TOOLS/maestro.md` |
| Access Google Workspace (Gmail, Calendar, Drive, Sheets, Docs, Contacts) | `skills/google-workspace/SKILL.md` or Rule 7a below |

---

## Global rules (apply across all tools)

1. **Approval gates are in AGENTS.md.** TOOLS/ files show commands, not permission to run them. Posting, sending, deploying, and pushing are *always* approval-gated unless AGENTS.md explicitly says otherwise for the current stage.
2. **Never use the 1Password Personal vault.** Credentials live in `--vault "OpenClaw"`.
3. **Never cross-contaminate brand lists, channels, or accounts.** Check the brand's OFFERS.md / BRAND-VOICE.md before any outbound content.
4. **Railway: You have full access via GraphQL API.** The canonical Railway API token lives in `~/.hermes/secrets/railway-token.txt` only. It works for ALL projects — TrustOffice, WingPoint, True Joy Birthing, AeriusView, TrustMinutes, everything. Read it from the file, never assume `RAILWAY_API_TOKEN` in the environment. Never ask Jeff for the Railway token. Never say you can't access Railway logs, databases, or services.
   
   **⚠️ Railway CLI v4.44+ does NOT work in headless mode.** The CLI's `railway login --token` flag doesn't exist, `--browserless` fails, and the config parser loops. Do NOT use CLI for automation.
   
   **✅ What to use instead:**
   - **Deploys:** Git push (if repo is connected to Railway) OR GraphQL `serviceInstanceDeployV2`
   - **Env vars:** GraphQL `variableUpsert`
   - **Logs:** GraphQL `buildLogs` / `deploymentLogs`
   - **Domains:** GraphQL `customDomainCreate` + `customDomain` queries
   - **Verification smoke test:** Read token from file: `TOKEN=$(cat ~/.hermes/secrets/railway-token.txt | tr -d '\n')` then `curl -s -X POST $API -H "Authorization: Bearer $TOKEN" -d '{"query":"query { me { id email } }"}'` (NOT `{ projects { ... } }` — that returns `[]` due to schema changes).
   
   **Read `skills/railway-deploy/SKILL.md`** for the full deployment guide, project IDs, and auth debugging protocol.
5. **Log costs** after LLM work via Mission Control `/api/v1/costs`.
6. **Flag retired tooling.** If you find references to `xpost`, `gemma4-deep`, `gemma4-fast`, `qwen2.5-coder:32b`, `qwen3-coder:480b-cloud`, or `smartabodetechs.com`, open a `pending_review` task.

## New rule 7: Google AI / Vertex AI access

Kit has three authenticated Google connections available for content generation and API work:

### 7a — Google Workspace (OAuth) — `~/.hermes/google_token.json`
- **Account:** `jeff@socialize.video`
- **Scopes:** Gmail (read/send/modify), Calendar (read/write), Drive (read/write), Sheets (read/write), Docs (read/write), Contacts (read)
- **All APIs enabled and verified:** Gmail ✅ Calendar ✅ Drive ✅ Sheets ✅ Docs ✅ Contacts ✅ (enabled June 30, 2026)
- **What to use it for:** Reading and sending email, checking/managing calendar, searching/reading/writing Drive files, reading/writing Sheets and Docs, listing contacts
- **Auth type:** OAuth 2.0 refresh token, auto-renews
- **Skill:** `google-workspace` — CLI via `google_api.py` (gmail search/get/send/reply, calendar list/create/delete, drive search, sheets get/update/append, docs get, contacts list)
- **Setup:** `python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check` to verify auth

### 7b — Google AI Studio / Gemini API — `~/.hermes/secrets/google_ai.env`
- **Key:** `AIzaSyCC4DZ9uRIW7lvbe-cVXsAuNYKWdmUQnz4` (stored as `GEMINI_API_KEY`)
- **What to use it for:** Quick text generation via the Gemini REST API (`https://generativelanguage.googleapis.com/v1beta/...`)
- **Limit:** Free tier with daily request caps — okay for small/fast tasks, not production volume
- **Auth type:** API key

### 7c — Vertex AI (Service Account) — `~/.hermes/secrets/trustoffice-489300-service-account.json`
- **Project:** `trustoffice-489300`
- **Service account:** `hermes-agent@trustoffice-489300.iam.gserviceaccount.com`
- **Region:** `us-central1`
- **What to use it for:** Production-grade content generation, high volume, Vertex-native features (Imagen image gen, long context, batch jobs)
- **Working models (Vertex):**
  - `gemini-2.5-flash` ✅ (use bare name, not `-001`)
  - `gemini-2.0-flash` ❌ (not deployed to this project/region)
- **Endpoint pattern:**
  ```
  POST https://us-central1-aiplatform.googleapis.com/v1/projects/trustoffice-489300/locations/us-central1/publishers/google/models/{MODEL_NAME}:generateContent
  ```
- **Auth type:** Service account JWT + OAuth token exchange (auto-renewed per request)
- **Rate limits:** Much higher than AI Studio free tier
- **Billing:** Linked to `jeff@socialize.video` payment method

### When to use which

| Task | Tool | Reason |
|---|---|---|
| Read Jeff's email / calendar | Workspace OAuth | Has access to his data |
| Draft + send an email | Workspace OAuth | `gmail.send` scope granted |
| Quick text prompt, <10 calls/day | AI Studio key | Fastest, no auth dance |
| Social content, ads, bulk generation | **Vertex AI** | Higher quotas, production billing, more models |
| Image generation (Imagen) | **Vertex AI** | AI Studio free tier doesn't include Imagen |
| Video analysis, long context, batch | **Vertex AI** | Enterprise features, better limits |

**Default choice for content generation:** Vertex AI service account. It's authenticated, has headroom, and unlocks all Google AI features.

**Never** commit these keys to repos. They live in `~/.hermes/secrets/` (`.env` loads them automatically) and 1Password (vault: OpenClaw).

## Rule 8: YouTube Data API access

Kit can read, upload, and manage YouTube content for Jeff's channels.

### Channels accessible

| Channel | ID | Handle | Subs |
|---|---|---|---|
| **TrustOffice** | `UCDy6M-wAxXWxhgTZhSdZ4RA` | `@trustofficeapp` | 13 |

The channel is on the same Google account (`jeff@socialize.video`) and accessible via the same OAuth token.

### 8a — Full access token (includes YouTube)

- **Path:** `~/.hermes/google_token.json` (updated with YouTube scopes)
- **Scopes:** `youtube.readonly`, `youtube.upload` + all Workspace scopes
- **What to use it for:**
  - Upload videos to either channel
  - Pull video metadata, transcripts, comments
  - Update titles, descriptions, tags, thumbnails
  - Read playlists and analytics

### 8b — Quick access token

- **Path:** `~/.hermes/secrets/google_ai_youtube.env` (`YOUTUBE_ACCESS_TOKEN`, `YOUTUBE_REFRESH_TOKEN`)
- **What to use it for:** One-off curl or script calls that need just YouTube

### Known limitation

The YouTube API `mine=true` endpoint only returns whichever channel is "active" in the account switcher. To get data for the other channel, use the channel ID directly (`?id=UC...`) rather than `?mine=true`.

### What I can do now

- Upload new videos to TrustOffice
- Download transcripts from existing videos for blog/social repurposing
- Update descriptions, tags, playlists
- Read comments and respond programmatically
- Pull basic channel stats (subscribers, views, etc.)
