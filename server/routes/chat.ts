/**
 * Chat Routes — Discord Channel Bridge
 *
 * Provides REST endpoints for the Chat UI to:
 *  - List channels
 *  - Get messages for a channel
 *  - Send messages to Discord
 *  - Mark messages as read
 *  - Transcribe audio (Whisper)
 */

import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { Database } from "bun:sqlite";

// ── Types ──

interface ChatChannel {
  discord_channel_id: string;
  name: string;
  slug: string;
  brand_id: string | null;
  last_message_at: string | null;
  unread_count: number;
}

interface ChatMessage {
  id: string;
  channel_id: string;
  channel_slug: string;
  discord_message_id: string | null;
  discord_author_id: string | null;
  discord_author_name: string;
  discord_author_avatar: string | null;
  content: string;
  is_from_kit: number;
  is_read: number;
  created_at: string;
}

// ── Broadcast function type ──

type BroadcastFn = (event: string, data: unknown) => void;

// ── Router factory ──

export function createChatRouter(db: Database, broadcast: BroadcastFn, sendToDiscord: (channelId: string, content: string) => Promise<string | null>) {
  const router = new Hono();

  // ── GET /chat/channels — List all channels ──

  router.get("/channels", (c) => {
    const channels = db
      .prepare(
        `SELECT cc.*, 
          (SELECT COUNT(*) FROM chat_messages cm WHERE cm.channel_id = cc.discord_channel_id AND cm.is_read = 0) as unread_count,
          (SELECT created_at FROM chat_messages cm WHERE cm.channel_id = cc.discord_channel_id ORDER BY cm.created_at DESC LIMIT 1) as last_message_at
        FROM chat_channels cc
        ORDER BY cc.name`
      )
      .all();

    return c.json({ channels });
  });

  // ── GET /chat/messages/:channelId — Get messages for a channel ──

  const messageQuerySchema = z.object({
    limit: z.coerce.number().min(1).max(100).default(50),
    before: z.string().optional(),
  });

  router.get("/messages/:channelId", zValidator("query", messageQuerySchema), (c) => {
    const { channelId } = c.req.param();
    const { limit, before } = c.req.valid("query");

    let query: string;
    let params: any[];

    if (before) {
      // Get messages older than the given ID (for pagination)
      query = `SELECT * FROM chat_messages WHERE channel_id = ? AND created_at < (SELECT created_at FROM chat_messages WHERE id = ?) ORDER BY created_at ASC LIMIT ?`;
      params = [channelId, before, limit];
    } else {
      query = `SELECT * FROM chat_messages WHERE channel_id = ? ORDER BY created_at DESC LIMIT ?`;
      params = [channelId, limit];
    }

    const messages = db.prepare(query).all(...params);

    // If no 'before' param, reverse so newest is last (for display)
    const result = before ? messages : messages.reverse();

    return c.json({ messages: result, count: result.length });
  });

  // ── POST /chat/messages — Send a message to Discord ──

  const sendMessageSchema = z.object({
    channel_id: z.string().min(1),
    content: z.string().min(1).max(2000),
  });

  router.post("/messages", zValidator("json", sendMessageSchema), async (c) => {
    const { channel_id, content } = c.req.valid("json");

    // Send to Discord
    const discordMessageId = await sendToDiscord(channel_id, content);

    if (!discordMessageId) {
      return c.json({ error: "Failed to send message to Discord" }, 500);
    }

    // The bot's own message handler will store and broadcast it,
    // but we also return the stored message here for immediate UI feedback
    const message = db
      .prepare("SELECT * FROM chat_messages WHERE discord_message_id = ?")
      .get(discordMessageId);

    return c.json({ message: message ?? { discord_message_id: discordMessageId } });
  });

  // ── POST /chat/messages/:id/read — Mark a message as read ──

  router.post("/messages/:id/read", (c) => {
    const { id } = c.req.param();

    db.prepare("UPDATE chat_messages SET is_read = 1 WHERE id = ?").run(id);

    // Also update unread count for the channel
    const msg = db.prepare("SELECT channel_id FROM chat_messages WHERE id = ?").get(id) as ChatMessage | null;
    if (msg) {
      db.prepare(
        `UPDATE chat_channels SET unread_count = (SELECT COUNT(*) FROM chat_messages WHERE channel_id = ? AND is_read = 0) WHERE discord_channel_id = ?`
      ).run(msg.channel_id, msg.channel_id);
    }

    return c.json({ ok: true });
  });

  // ── POST /chat/read-all/:channelId — Mark all messages in a channel as read ──

  router.post("/read-all/:channelId", (c) => {
    const { channelId } = c.req.param();

    db.prepare("UPDATE chat_messages SET is_read = 1 WHERE channel_id = ?").run(channelId);
    db.prepare("UPDATE chat_channels SET unread_count = 0 WHERE discord_channel_id = ?").run(channelId);

    broadcast("chat.channel_updated", { channel_id: channelId, unread_count: 0 });

    return c.json({ ok: true });
  });

  // ── POST /chat/transcribe — Transcribe audio via Whisper ──

  router.post("/transcribe", async (c) => {
    const formData = await c.req.formData();
    const audioFile = formData.get("audio") as File | null;

    if (!audioFile) {
      return c.json({ error: "No audio file provided" }, 400);
    }

    const whisperVenvPath = process.env.WHISPER_VENV_PATH;
    const whisperModel = process.env.WHISPER_MODEL ?? "base";

    if (!whisperVenvPath) {
      // Fallback: try OpenAI Whisper API if OPENAI_API_KEY is set
      const apiKey = process.env.OPENAI_API_KEY;
      if (!apiKey) {
        return c.json({ error: "Whisper not configured" }, 501);
      }

      try {
        const buffer = Buffer.from(await audioFile.arrayBuffer());
        const blob = new Blob([buffer], { type: audioFile.type || "audio/webm" });
        const file = new File([blob], "audio.webm", { type: audioFile.type || "audio/webm" });

        const openaiFormData = new FormData();
        openaiFormData.append("file", file);
        openaiFormData.append("model", "whisper-1");
        openaiFormData.append("response_format", "json");

        const response = await fetch("https://api.openai.com/v1/audio/transcriptions", {
          method: "POST",
          headers: { Authorization: `Bearer ${apiKey}` },
          body: openaiFormData,
        });

        if (!response.ok) {
          const errText = await response.text();
          console.error("[whisper] OpenAI API error:", errText);
          return c.json({ error: "Transcription failed" }, 500);
        }

        const result = await response.json() as { text: string };
        return c.json({ text: result.text });
      } catch (err) {
        console.error("[whisper] OpenAI API error:", (err as Error).message);
        return c.json({ error: "Transcription failed" }, 500);
      }
    }

    // Local Whisper
    try {
      const tmpDir = `/tmp/mc-whisper`;
      await Bun.write(`${tmpDir}/audio_input`, Buffer.from(await audioFile.arrayBuffer()));

      const proc = Bun.spawn(
        [
          `${whisperVenvPath}/bin/python`,
          "-m",
          "whisper",
          "--model",
          whisperModel,
          "--output_format",
          "txt",
          "--output_dir",
          tmpDir,
          `${tmpDir}/audio_input`,
        ],
        { stdout: "pipe", stderr: "pipe" }
      );

      const exitCode = await proc.exited;

      if (exitCode !== 0) {
        const stderr = await new Response(proc.stderr).text();
        console.error("[whisper] Local whisper error:", stderr);
        return c.json({ error: "Transcription failed" }, 500);
      }

      const transcript = await Bun.file(`${tmpDir}/audio_input.txt`).text();
      return c.json({ text: transcript.trim() });
    } catch (err) {
      console.error("[whisper] Local whisper error:", (err as Error).message);
      return c.json({ error: "Transcription failed" }, 500);
    }
  });

  return router;
}