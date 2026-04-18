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

    // Validate channel exists
    const channelExists = db
      .prepare("SELECT 1 FROM chat_channels WHERE discord_channel_id = ?")
      .get(channelId);
    if (!channelExists) {
      return c.json({ error: "Channel not found" }, 404);
    }

    let query: string;
    let params: any[];

    if (before) {
      // Validate the 'before' message exists
      const refMsg = db
        .prepare("SELECT created_at FROM chat_messages WHERE id = ?")
        .get(before) as { created_at: string } | null;
      if (!refMsg) {
        return c.json({ error: "Message not found" }, 404);
      }
      query = `SELECT * FROM chat_messages WHERE channel_id = ? AND created_at < ? ORDER BY created_at ASC LIMIT ?`;
      params = [channelId, refMsg.created_at, limit];
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

    // Wait briefly for the Discord bot's own message handler to store it,
    // then retrieve. Fallback to constructing a response if not yet stored.
    await new Promise((r) => setTimeout(r, 200));

    const message = db
      .prepare("SELECT * FROM chat_messages WHERE discord_message_id = ?")
      .get(discordMessageId);

    if (message) {
      return c.json({ message });
    }

    // Construct a provisional response if the bot handler hasn't stored it yet
    const channelRow = db
      .prepare("SELECT slug FROM chat_channels WHERE discord_channel_id = ?")
      .get(channel_id) as { slug: string } | null;
    return c.json({
      message: {
        id: "pending",
        channel_id,
        channel_slug: channelRow?.slug ?? "unknown",
        discord_message_id: discordMessageId,
        discord_author_id: null,
        discord_author_name: "Kit",
        discord_author_avatar: null,
        content,
        is_from_kit: 1,
        is_read: 0,
        created_at: new Date().toISOString(),
      },
    });
  });

  // ── POST /chat/messages/:id/read — Mark a message as read ──

  router.post("/messages/:id/read", (c) => {
    const { id } = c.req.param();

    const msg = db
      .prepare("SELECT channel_id FROM chat_messages WHERE id = ?")
      .get(id) as { channel_id: string } | null;
    if (!msg) {
      return c.json({ error: "Message not found" }, 404);
    }

    db.prepare("UPDATE chat_messages SET is_read = 1 WHERE id = ?").run(id);

    // Update unread count for the channel
    db.prepare(
      `UPDATE chat_channels SET unread_count = (SELECT COUNT(*) FROM chat_messages WHERE channel_id = ? AND is_read = 0) WHERE discord_channel_id = ?`
    ).run(msg.channel_id, msg.channel_id);

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

    // Limit audio file to 10MB
    if (audioFile.size > 10 * 1024 * 1024) {
      return c.json({ error: "Audio file too large (max 10MB)" }, 413);
    }

    const whisperVenvPath = process.env.WHISPER_VENV_PATH;
    const whisperModel = process.env.WHISPER_MODEL ?? "base";

    if (!whisperVenvPath) {
      // Fallback chain: Groq → OpenAI → error
      const groqApiKey = process.env.GROQ_API_KEY;
      const openaiApiKey = process.env.OPENAI_API_KEY;

      if (!groqApiKey && !openaiApiKey) {
        return c.json({ error: "Whisper not configured (set GROQ_API_KEY or OPENAI_API_KEY)" }, 501);
      }

      // Prefer Groq (free tier), fall back to OpenAI
      const apiUrl = groqApiKey
        ? "https://api.groq.com/openai/v1/audio/transcriptions"
        : "https://api.openai.com/v1/audio/transcriptions";
      const apiKey = groqApiKey || openaiApiKey!;
      // Groq uses "whisper-large-v3", OpenAI uses "whisper-1"
      const model = groqApiKey ? "whisper-large-v3" : "whisper-1";

      try {
        const buffer = Buffer.from(await audioFile.arrayBuffer());
        const blob = new Blob([buffer], { type: audioFile.type || "audio/webm" });
        const file = new File([blob], "audio.webm", { type: audioFile.type || "audio/webm" });

        const apiFormData = new FormData();
        apiFormData.append("file", file);
        apiFormData.append("model", model);
        apiFormData.append("response_format", "json");

        const provider = groqApiKey ? "groq" : "openai";
        console.log(`[whisper] Using ${provider} API`);

        const response = await fetch(apiUrl, {
          method: "POST",
          headers: { Authorization: `Bearer ${apiKey}` },
          body: apiFormData,
        });

        if (!response.ok) {
          const errText = await response.text();
          console.error(`[whisper] ${provider} API error:`, errText);
          return c.json({ error: "Transcription failed" }, 500);
        }

        const result = await response.json() as { text: string };
        return c.json({ text: result.text });
      } catch (err) {
        console.error("[whisper] API error:", (err as Error).message);
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