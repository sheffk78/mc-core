# TOOLS/social-posting-api.md

Primary content posting adapter for TikTok, Instagram, YouTube, Pinterest, LinkedIn, Facebook. Video posts, slideshows, Studio AI image/video, packs, analytics, full pipeline.

- **Skill:** `~/.openclaw/workspace/skills/social-posting-api/SKILL.md` ← full API command routing lives in the skill, not here
- **Script:** `~/.openclaw/workspace/skills/social-posting-api/scripts/genviral.sh`
- **Auth:** `GENVIRAL_API_KEY` env var, format `public_id.secret` (1Password)
- **Approval gate:** Kit drafts and renders; **Jeff approves before `create-post`**. Always.

## Core flow

```bash
# generate → render → REVIEW → post → log
genviral.sh generate --pack-id <id> --prompt "..."
genviral.sh render --slideshow-id <id>
genviral.sh create-post --slideshow-id <id> --accounts "..."
genviral.sh analytics-posts --json

# Studio AI
genviral.sh studio-generate-image --prompt "..." --model-id "google/nano-banana-2"
genviral.sh studio-generate-video --prompt "..."
```

## Non-negotiables

1. Always use `pinned_images` when generating with a pack — never bare `--pack-id`
2. Always visually review rendered slides before posting (hard gate)
3. Always log to `workspace/performance/log.json` after posting
4. Always add a hook-tracker entry after posting
5. Never use em-dashes in generated content

For per-endpoint command details (accounts, folders, posts, slideshows, packs, templates, analytics, studio, subscription, pipeline, errors), open the skill file above — it has the full routing table.
