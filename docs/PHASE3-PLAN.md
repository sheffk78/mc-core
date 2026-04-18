# Phase 3 — Kit Chat Integration Plan

## Problem
Jeff can send messages through the MC Chat UI, and they appear in Discord. But Kit (via OpenClaw) doesn't respond to messages from the MC Chat UI — Kit only sees messages that come through OpenClaw's Discord integration.

## Architecture

Current flow:
```
MC Chat UI → POST /api/v1/chat/messages → Discord Bot → Discord Channel
Discord Channel → Discord Bot → chat_messages DB → WebSocket → MC Chat UI
```

What's missing:
```
Discord Channel → OpenClaw Discord integration → Kit responds → Discord Bot → DB → UI
```

Kit *does* see Jeff's messages via OpenClaw's Discord integration (that's how Jeff is talking to Kit right now in #general). But when Jeff types in the MC Chat UI, the message goes to Discord, and Kit sees it as a Discord message from "kjkora" — which works.

The actual issue: **Kit's responses go back through OpenClaw's Discord message tool, not through the MC Chat API.** So in the MC Chat UI, Kit's responses appear because the Discord bot picks them up from Discord and stores them. But the bot name in production is "Wisper" not "Kit".

## Two issues to fix:

### 1. Bot identity mismatch
- Local dev: Kit#5842 (matches `is_from_kit = 1`)
- Production: Wisper#1212 (doesn't match — `is_from_kit` flag is hardcoded)

The Discord bot should detect its own messages by `msg.author.id === client.user.id`, not by name.

### 2. Direct MC Chat responses (Phase 3 proper)
For Kit to respond directly through the MC Chat API (without going through Discord), we'd need:
- A webhook endpoint that OpenClaw can call
- Or a new OpenClaw skill/tool that sends messages via the MC Chat API

This is the bigger feature. For now, the simplest fix is #1 — make the bot correctly identify its own messages.

## Implementation for #1
In `discord-bot.ts`, the `storeMessage` method should use `msg.author.id === this.client.user?.id` to set `is_from_kit`, not hardcode a name check.