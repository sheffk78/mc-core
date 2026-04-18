/**
 * Discord Bot — Mission Control Chat Bridge
 *
 * Connects to Discord via discord.js, listens for messages in configured channels,
 * stores them in SQLite, and broadcasts to WebSocket clients.
 * Also exposes a send function for the Chat UI to post messages to Discord.
 */

import {
  Client,
  GatewayIntentBits,
  Events,
  Message,
  Partials,
  ChannelType,
} from "discord.js";
import { Database } from "bun:sqlite";

// ── Types ──

export interface DiscordChannelConfig {
  id: string;
  name: string;
  slug: string;
  brandId: string | null;
}

// ── Channel mapping from env ──

function loadChannels(): DiscordChannelConfig[] {
  return [
    {
      id: process.env.DISCORD_CHANNEL_GENERAL ?? "",
      name: "General",
      slug: "general",
      brandId: null,
    },
    {
      id: process.env.DISCORD_CHANNEL_TRUSTOFFICE ?? "",
      name: "TrustOffice",
      slug: "trustoffice",
      brandId: null, // resolved after brands load
    },
    {
      id: process.env.DISCORD_CHANNEL_AGENTICTRUST ?? "",
      name: "AgenticTrust",
      slug: "agentictrust",
      brandId: null,
    },
    {
      id: process.env.DISCORD_CHANNEL_TRUEJOYBIRTHING ?? "",
      name: "True Joy Birthing",
      slug: "truejoybirthing",
      brandId: null,
    },
    {
      id: process.env.DISCORD_CHANNEL_WINGPOINT ?? "",
      name: "WingPoint",
      slug: "wingpoint",
      brandId: null,
    },
  ].filter((c) => c.id !== "");
}

// ── Broadcast callback type ──

export type BroadcastFn = (event: string, data: unknown) => void;

// ── Bot class ──

export class DiscordBot {
  private client: Client | null = null;
  private channels: DiscordChannelConfig[] = [];
  private db: Database;
  private broadcast: BroadcastFn;
  private ready = false;

  constructor(db: Database, broadcast: BroadcastFn) {
    this.db = db;
    this.broadcast = broadcast;
    this.channels = loadChannels();
  }

  /** Start the Discord bot (non-blocking) */
  async start(): Promise<void> {
    const token = process.env.DISCORD_BOT_TOKEN;
    if (!token) {
      console.warn("[discord] No DISCORD_BOT_TOKEN — bot disabled");
      return;
    }

    if (this.channels.length === 0) {
      console.warn("[discord] No channels configured — bot disabled");
      return;
    }

    this.client = new Client({
      intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
      ],
      partials: [Partials.Channel],
    });

    this.client.once(Events.ClientReady, (client) => {
      console.log(`[discord] Connected as ${client.user.tag} (${client.user.id})`);
      this.ready = true;

      // Seed channel info into DB
      this.seedChannels();
    });

    this.client.on(Events.MessageCreate, (msg) => this.handleMessage(msg));

    this.client.on(Events.Error, (err) => {
      console.error("[discord] Client error:", err.message);
    });

    this.client.on(Events.Disconnect, () => {
      console.warn("[discord] Disconnected — will auto-reconnect");
      this.ready = false;
    });

    this.client.on(Events.Reconnecting, () => {
      console.log("[discord] Reconnecting...");
    });

    try {
      await this.client.login(token);
      console.log("[discord] Bot login initiated");
    } catch (err) {
      console.error("[discord] Login failed:", (err as Error).message);
    }
  }

  /** Stop the bot */
  async stop(): Promise<void> {
    if (this.client) {
      this.client.destroy();
      this.client = null;
      this.ready = false;
    }
  }

  /** Is the bot connected and ready? */
  isReady(): boolean {
    return this.ready && (this.client?.isReady() ?? false);
  }

  /** Get configured channels */
  getChannels(): DiscordChannelConfig[] {
    return this.channels;
  }

  /** Send a message to a Discord channel */
  async sendMessage(channelId: string, content: string): Promise<string | null> {
    if (!this.client || !this.ready) {
      console.warn("[discord] Bot not ready — cannot send message");
      return null;
    }

    try {
      const channel = this.client.channels.cache.get(channelId);
      if (!channel || !channel.isTextBased()) {
        console.error(`[discord] Channel ${channelId} not found or not text-based`);
        return null;
      }

      const msg = await channel.send(content);
      console.log(`[discord] Sent message to ${channelId}: ${msg.id}`);

      // Store the sent message in DB
      this.storeMessage(msg, true);

      return msg.id;
    } catch (err) {
      console.error(`[discord] Error sending to ${channelId}:`, (err as Error).message);
      return null;
    }
  }

  // ── Private ──

  private handleMessage(msg: Message): void {
    // Ignore bot messages and DMs
    if (msg.author.bot) return;
    if (!msg.guildId) return;

    // Check if message is in one of our channels
    const channelConfig = this.channels.find((c) => c.id === msg.channelId);
    if (!channelConfig) return;

    // Store in DB
    const messageId = this.storeMessage(msg, false);
    if (!messageId) return;

    // Broadcast to WebSocket clients
    this.broadcast("chat.message", {
      id: messageId,
      channel_id: msg.channelId,
      channel_slug: channelConfig.slug,
      discord_message_id: msg.id,
      discord_author_id: msg.author.id,
      discord_author_name: msg.author.displayName ?? msg.author.username,
      discord_author_avatar: msg.author.displayAvatarURL({ size: 64 }),
      content: msg.content,
      is_from_kit: 0,
      is_read: 0,
      created_at: new Date().toISOString(),
    });

    // Update channel last_message_at
    this.db
      .prepare(
        "UPDATE chat_channels SET last_message_at = ? WHERE discord_channel_id = ?"
      )
      .run(new Date().toISOString(), msg.channelId);
  }

  private storeMessage(msg: Message, isFromKit: boolean): string | null {
    try {
      const channelConfig = this.channels.find((c) => c.id === msg.channelId);
      if (!channelConfig) return null;

      const id = crypto.randomUUID().replace(/-/g, "").substring(0, 16);
      this.db
        .prepare(
          `INSERT INTO chat_messages (id, channel_id, channel_slug, discord_message_id, discord_author_id, discord_author_name, discord_author_avatar, content, is_from_kit, is_read, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .run(
          id,
          msg.channelId,
          channelConfig.slug,
          msg.id,
          msg.author.id,
          msg.author.displayName ?? msg.author.username,
          msg.author.displayAvatarURL({ size: 64 }),
          msg.content,
          isFromKit ? 1 : 0,
          0,
          new Date().toISOString()
        );

      return id;
    } catch (err) {
      console.error("[discord] Error storing message:", (err as Error).message);
      return null;
    }
  }

  private seedChannels(): void {
    const upsert = this.db.prepare(
      `INSERT OR REPLACE INTO chat_channels (discord_channel_id, name, slug, brand_id, last_message_at, unread_count)
       VALUES (?, ?, ?, ?, ?, ?)`
    );

    // Try to resolve brand IDs from the brands table
    const brands = this.db.prepare("SELECT id, slug FROM brands").all();
    const brandMap = new Map(brands.map((b: any) => [b.slug, b.id]));

    for (const ch of this.channels) {
      const brandId = ch.brandId ?? brandMap.get(ch.slug) ?? null;
      upsert.run(ch.id, ch.name, ch.slug, brandId, null, 0);
    }

    console.log(`[discord] Seeded ${this.channels.length} channels`);
  }
}