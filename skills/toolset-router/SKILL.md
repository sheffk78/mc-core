---
name: toolset-router
description: Automatically enable/disable toolsets based on the active task. Load at session start or when task context changes. Run the check script, then enable needed toolsets before asking for /reset.
---

# Toolset Router

Dynamically route toolsets based on what the active task actually needs. Prevents "I can't do that" from missing tools while keeping the system prompt slim for smaller models.

## When to Load

- When a tool call fails with "tool not available"
- When switching to a different brand or task type mid-session and you need to check toolsets
- At session start if the cron job didn't run or ACTIVE-TASK.md changed recently

## Architecture

This is integrated with the **skill-registry MCP server** — the same server that provides `search_skills`, `suggest_skills`, `list_categories`, and `load_skill`. Toolset routing is the 5th tool: `route_toolsets`.

**3 access points:**

1. **MCP tool** (in-session, read-only): Call `mcp__skill_registry__route_toolsets` via the skill-registry MCP. Returns recommendations but doesn't write config. Use this to check what you need, then enable manually.

2. **Cron job** (background, zero tokens): `no_agent=True` script-only job runs `toolset-router.py` every 2h. Reads ACTIVE-TASK.md, writes config changes directly. Silent when no changes needed (empty stdout = no message delivered). Only messages you when toolsets actually changed.

3. **Manual script**: `python3 scripts/toolset-router.py` — same logic as cron. Flags: `--status` (show current state), `--reset` (back to core-only defaults).

## Toolset → Task Mapping

| Task Pattern | Toolsets Needed | Usually Disabled? |
|---|---|---|
| Blog/content creation | `image_gen` | Yes — enable |
| Voice messages / TTS | `tts` | Yes — enable |
| Video production | `video`, `image_gen` | Yes — enable both |
| Desktop app automation (1Password, LightPDF) | `computer_use` | Yes — enable |
| Uncertain task / need to ask Jeff | `clarify` | Yes — enable |
| Mobile app testing | `maestro` MCP | Yes — enable MCP |
| Ad research / competitor analysis | `adspirer`, `facebook_ads` | Already enabled |
| Web research / scraping | `web`, `browser` | Already enabled |
| Code / deployment | `terminal`, `file`, `code_execution` | Already enabled |
| Skill management | `skills` | Already enabled |
| Scheduled tasks | `cronjob` | Already enabled |
| Parallel work | `delegation` | Already enabled |

## Procedure

### Step 1: Run the auto-router script

```bash
python3 ~/.openclaw/workspace/scripts/toolset-router.py
```

This reads ACTIVE-TASK.md, matches keywords to the toolset mapping, and auto-enables/disables. It runs every 2h via cron job `toolset-auto-router` so the next session usually starts pre-configured.

Flags: `--status` (show current state), `--reset` (back to core-only defaults).

### Step 2: If the script missed something

Manually enable a toolset the script didn't catch:

```bash
hermes tools enable <toolset_name>
```

For MCP servers:
```bash
python3 -c "
import yaml
with open('$HOME/.hermes/config.yaml') as f:
    c = yaml.safe_load(f)
c['mcp_servers']['<name>']['enabled'] = True
with open('$HOME/.hermes/config.yaml', 'w') as f:
    yaml.dump(c, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
"
```

### Step 3: If any toolsets were enabled, request /reset

```
Enabled <toolset_list> for this task. Send /reset to activate.
```

Only request /reset if toolsets were actually changed. If everything needed is already enabled, proceed without interruption.

## Default Enabled Set (keep always on)

These 12 toolsets stay enabled for every session — they're the core operating set:

- `web` — search and extract
- `browser` — web interaction
- `terminal` — shell commands
- `file` — file operations
- `code_execution` — batch processing
- `vision` — image analysis
- `skills` — skill management
- `todo` — task tracking
- `memory` — persistent memory
- `session_search` — history recall
- `delegation` — parallel agents
- `cronjob` — scheduled tasks

## On-Demand Set (enable when needed, disable after)

- `image_gen` — blog images, OG images, visual content
- `tts` — voice messages
- `video` — video analysis
- `computer_use` — desktop app automation
- `clarify` — when genuinely uncertain (rare — Jeff prefers autonomous action)

## MCP Servers

| Server | Status | When to Enable |
|---|---|---|
| `adspirer` | Always on | Ad management |
| `facebook_ads` | Always on | FB ad research |
| `skill-registry` | Always on | Skill discovery |
| `zapier` | Always on | App automation |
| `refero` | Disabled | Design references (rare) |
| `siteguru` | Disabled | SEO monitoring (rare) |
| `maestro` | Disabled | Mobile testing only |