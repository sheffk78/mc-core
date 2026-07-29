# TOOLS/google-ai.md

Google AI access — three authenticated connections for content generation and API work.

## 7a — Google Workspace (OAuth)

- **Token:** `~/.hermes/google_token.json`
- **Account:** `jeff@socialize.video`
- **Scopes:** Gmail (read/send/modify), Calendar (read/write), Drive (read/write), Sheets (read/write), Docs (read/write), Contacts (read), YouTube (readonly/upload)
- **All APIs verified:** Gmail ✅ Calendar ✅ Drive ✅ Sheets ✅ Docs ✅ Contacts ✅ (June 30, 2026)
- **Skill:** `google-workspace` — CLI via `google_api.py`
- **Setup check:** `python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check`

## 7b — Google AI Studio / Gemini API

- **Key:** `~/.hermes/secrets/google_ai.env` (`GEMINI_API_KEY`)
- **Use for:** Quick text generation via Gemini REST API
- **Limit:** Free tier with daily caps — small/fast tasks only

## 7c — Vertex AI (Service Account)

- **Key:** `~/.hermes/secrets/trustoffice-489300-service-account.json`
- **Project:** `trustoffice-489300`
- **Service account:** `hermes-agent@trustoffice-489300.iam.gserviceaccount.com`
- **Region:** `us-central1`
- **Working models:** `gemini-2.5-flash` ✅ (use bare name, not `-001`), `gemini-2.0-flash` ❌
- **Endpoint:** `POST https://us-central1-aiplatform.googleapis.com/v1/projects/trustoffice-489300/locations/us-central1/publishers/google/models/{MODEL_NAME}:generateContent`
- **Use for:** Production-grade content, Imagen image gen, high volume, batch jobs

## When to use which

| Task | Tool | Reason |
|---|---|---|
| Read Jeff's email / calendar | Workspace OAuth | Has access to his data |
| Draft + send email | Workspace OAuth | `gmail.send` scope granted |
| Quick text prompt, <10 calls/day | AI Studio key | Fastest, no auth dance |
| Social content, ads, bulk generation | Vertex AI | Higher quotas, production billing |
| Image generation (Imagen) | Vertex AI | Free tier doesn't include Imagen |
| Video analysis, long context, batch | Vertex AI | Enterprise features |

**Default for content generation:** Vertex AI. Authenticated, headroom, all features.

**Never** commit keys to repos. They live in `~/.hermes/secrets/` and 1Password (vault: OpenClaw).