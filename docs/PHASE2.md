# Phase 2 — Discord Chat Integration

**Status:** ✅ Complete and committed  
**Commits:** `0a8d7f1` (initial build), `9ce8a89` (bug fixes)  
**Date:** April 17, 2026

## What Was Built

### 1. Discord Bot (`server/discord-bot.ts`)
- Connects as Kit#5842 to the AgenticTrust Discord guild
- Listens to 5 channels: General, TrustOffice, AgenticTrust, TJB, WingPoint
- Stores incoming messages in `chat_messages` SQLite table
- Broadcasts new messages to WebSocket clients in real-time
- Sends messages from the Chat UI back to Discord channels
- Auto-reconnects on disconnection
- Seeds `chat_channels` table with brand IDs resolved from the brands table

### 2. Chat API Routes (`server/routes/chat.ts`)
- `GET /api/v1/chat/channels` — list channels with unread counts
- `GET /api/v1/chat/messages/:channelId` — paginated messages (newest last)
- `POST /api/v1/chat/messages` — send message to Discord channel
- `POST /api/v1/chat/messages/:id/read` — mark message as read
- `POST /api/v1/chat/read-all/:channelId` — mark all in channel as read
- `POST /api/v1/chat/transcribe` — Whisper voice transcription (local or OpenAI API)

### 3. Database Tables
- `chat_channels` — discord_channel_id (PK), name, slug, brand_id, last_message_at, unread_count
- `chat_messages` — id, channel_id, channel_slug, discord_message_id, discord_author_id, discord_author_name, discord_author_avatar, content, is_from_kit, is_read, created_at
- Both auto-created on startup via the migration in `server/src/index.ts`

### 4. Chat UI (`web/src/views/ChatView.tsx`)
- Left sidebar: 5 channels with brand color dots, unread badges, last message preview
- Main area: message bubbles with author avatars, names, timestamps
- Kit's own messages styled right-aligned with accent color
- Input area: text input + send button (Enter to send)
- Real-time updates via WebSocket

### 5. TTS (Text-to-Speech)
- 🔊 button on each message to read it aloud
- "Auto-read" toggle in channel header for new messages
- Voice selection dropdown (uses browser's `speechSynthesis.getVoices()`)
- Speed control (0.5x to 2x)
- Preferences persisted in localStorage

### 6. Voice Input (Whisper)
- 🎤 button records audio via MediaRecorder API (max 60 seconds)
- Red pulsing indicator while recording
- Audio sent to `POST /api/v1/chat/transcribe`
- Backend routes to local Whisper (if `WHISPER_VENV_PATH` set) or OpenAI API (if `OPENAI_API_KEY` set)
- Transcribed text fills input field for editing before send

### 7. Sidebar Integration
- "Chat" added to sidebar with MessageCircle icon from lucide-react
- 'chat' added to View type union in dashboard store

## Environment Variables

```
MC_AUTH_TOKEN=<set in .env>
DISCORD_BOT_TOKEN=<set in .env>
DISCORD_CHANNEL_GENERAL=<set in .env>
DISCORD_CHANNEL_TRUSTOFFICE=<set in .env>
DISCORD_CHANNEL_AGENTICTRUST=<set in .env>
DISCORD_CHANNEL_TRUEJOYBIRTHING=<set in .env>
DISCORD_CHANNEL_WINGPOINT=<set in .env>
DISCORD_GUILD_ID=<set in .env>
WHISPER_VENV_PATH=<set in .env, or omit for OpenAI API>
WHISPER_MODEL=base
DB_PATH=./data/mc.db
FRONTEND_URL=http://localhost:5173
```

The `.env` file lives at both `mc-core/.env` and `mc-core/server/.env` (Bun loads from CWD).

## Bug Fixes Applied (Minimax Review)

| Severity | Issue | Fix |
|----------|-------|-----|
| P0 | `require("fs")` in ESM context crashes /health | Replaced with `import { statSync }` |
| P0 | No file size limit on /chat/transcribe | Added 10MB limit |
| P1 | Pagination returns empty when `before` ID not found | Return 404 for missing ID |
| P1 | Race condition: send message returns before bot stores it | Add 200ms wait + provisional response |
| P1 | markAsRead silently no-ops on missing message | Return 404 |
| P1 | Graceful shutdown doesn't await Discord bot stop | Centralized async handler |
| P1 | ChatView useEffect creates duplicate subscriptions | Split into separate effects |
| P2 | Null safety on discord_author_name | Added `?? "?"` fallback |
| P2 | Empty transcription appends space | Added `.trim()` guard |
| P2 | wsEmit swallows errors silently | Added console.error logging |
| P2 | WebSocket message handler doesn't guard type | Added type check |

## How to Run

```bash
cd ~/.openclaw/workspace/mc-core
bun run dev   # starts both server (port 3000) and web (port 5173)
```

The Discord bot connects automatically if `DISCORD_BOT_TOKEN` is set.

## Known Limitations

- Voice input (Whisper) requires either local Whisper install (`WHISPER_VENV_PATH`) or OpenAI API key (`OPENAI_API_KEY`)
- TTS uses browser Web Speech API — voice availability depends on the browser/OS
- No message editing or deleting yet
- No file/image attachments yet
- No DM support (guild channels only)
- Channel list is static (configured via env vars, not dynamic)

## Phase 1 Context

Phase 1 built the initial Discord bot connection and basic Chat UI in a previous session. That session hit 82% context and compacted before committing, so the code was lost. Phase 2 rebuilt everything from scratch with improvements.