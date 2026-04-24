import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { serveStatic } from "hono/bun";
import { Database } from "bun:sqlite";
import { mkdirSync, statSync } from "fs";

import { authMiddleware } from "../middleware/auth";
import { DiscordBot } from "../discord-bot";
import { createChatRouter } from "../routes/chat";
import { wsEmit } from "../ws";

// ── Database (shared across routes) ──
const dbPath = process.env.DB_PATH ?? "./data/mc.db";
const dbDir = dbPath.substring(0, dbPath.lastIndexOf("/"));
if (dbDir) mkdirSync(dbDir, { recursive: true });
const db = new Database(dbPath);
db.exec("PRAGMA journal_mode = WAL");
db.exec("PRAGMA foreign_keys = ON");

// ---------------------------------------------------------------------------
// Auto-migrate on first boot
// ---------------------------------------------------------------------------

function autoMigrate(db: Database) {
  // Check if tables exist
  const table = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='brands'").get();
  if (table) {
    // Tables exist, but check for new tables (chat) that need to be added
    autoMigrateChatTables(db);
    return;
  }

  console.log("⚡ Auto-migrating database...");

  db.exec(`
CREATE TABLE brands (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  color TEXT NOT NULL DEFAULT '#c85a2a',
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_brands_slug ON brands(slug);

CREATE TABLE tasks (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  brand_id TEXT NOT NULL REFERENCES brands(id),
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','in_progress','pending_review','approved','rejected','completed','archived')),
  priority TEXT NOT NULL DEFAULT 'normal' CHECK(priority IN ('low','normal','high','critical')),
  risk_tier TEXT NOT NULL DEFAULT 'yellow' CHECK(risk_tier IN ('green','yellow','red')),
  assignee TEXT NOT NULL DEFAULT 'kit' CHECK(assignee IN ('kit','jeff','unassigned')),
  category TEXT DEFAULT '',
  agent_note TEXT DEFAULT '',
  user_note TEXT DEFAULT '',
  due_date TEXT,
  completed_at TEXT,
  estimated_cost REAL,
  actual_cost REAL,
  model_used TEXT,
  tokens_in INTEGER,
  tokens_out INTEGER,
  confidence REAL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_tasks_brand ON tasks(brand_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_assignee ON tasks(assignee);
CREATE INDEX idx_tasks_risk ON tasks(risk_tier);
CREATE INDEX idx_tasks_due ON tasks(due_date);

CREATE TABLE task_files (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'context' CHECK(role IN ('skill','output','context','input','reference')),
  label TEXT DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE approvals (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  brand_id TEXT NOT NULL REFERENCES brands(id),
  task_id TEXT REFERENCES tasks(id),
  type TEXT NOT NULL DEFAULT 'content' CHECK(type IN ('content','email','social','spend','code','decision')),
  title TEXT NOT NULL,
  preview TEXT DEFAULT '',
  agent_reasoning TEXT DEFAULT '',
  risk_tier TEXT NOT NULL DEFAULT 'yellow' CHECK(risk_tier IN ('green','yellow','red')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected','expired','auto_approved')),
  feedback TEXT DEFAULT '',
  metadata TEXT DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  decided_at TEXT,
  decided_by TEXT
);

CREATE TABLE activities (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  brand_id TEXT REFERENCES brands(id),
  task_id TEXT REFERENCES tasks(id),
  actor TEXT NOT NULL DEFAULT 'kit' CHECK(actor IN ('kit','jeff','system','cron')),
  action TEXT NOT NULL,
  summary TEXT NOT NULL,
  detail TEXT DEFAULT '',
  model_used TEXT,
  tokens_used INTEGER,
  cost_usd REAL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE cron_jobs (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  brand_id TEXT REFERENCES brands(id),
  schedule_expr TEXT NOT NULL,
  schedule_ms INTEGER,
  cron_expr TEXT,
  enabled INTEGER NOT NULL DEFAULT 1,
  last_run_at TEXT,
  last_status TEXT DEFAULT 'unknown',
  last_duration_ms INTEGER,
  last_error TEXT,
  consecutive_errors INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE daily_costs (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  date TEXT NOT NULL,
  brand_id TEXT REFERENCES brands(id),
  model TEXT NOT NULL,
  tokens_in INTEGER NOT NULL DEFAULT 0,
  tokens_out INTEGER NOT NULL DEFAULT 0,
  cost_usd REAL NOT NULL DEFAULT 0.0,
  task_count INTEGER NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX idx_daily_costs_unique ON daily_costs(date, brand_id, model);

CREATE TABLE revenue_snapshots (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  brand_id TEXT NOT NULL REFERENCES brands(id),
  date TEXT NOT NULL,
  mrr REAL,
  arr REAL,
  subscribers INTEGER,
  source TEXT DEFAULT 'stripe',
  metadata TEXT DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_revenue_brand_date ON revenue_snapshots(brand_id, date);

CREATE TABLE notifications (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  channel TEXT NOT NULL CHECK(channel IN ('slack','email','dashboard')),
  recipient TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT DEFAULT '',
  related_id TEXT,
  sent_at TEXT NOT NULL DEFAULT (datetime('now')),
  status TEXT NOT NULL DEFAULT 'sent' CHECK(status IN ('sent','failed','read'))
);

CREATE TABLE webauthn_credentials (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  credential_id TEXT NOT NULL UNIQUE,
  public_key TEXT NOT NULL,
  counter INTEGER NOT NULL DEFAULT 0,
  device_type TEXT,
  backed_up INTEGER DEFAULT 0,
  transports TEXT DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_used_at TEXT
);

CREATE TABLE files (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  path TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  label TEXT DEFAULT '',
  category TEXT NOT NULL DEFAULT 'other' CHECK(category IN ('skill','brand_doc','daily_note','config','output','other')),
  brand_id TEXT REFERENCES brands(id),
  preview TEXT DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_channels (
  discord_channel_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  brand_id TEXT REFERENCES brands(id),
  last_message_at TEXT,
  unread_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_messages (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  channel_id TEXT NOT NULL,
  channel_slug TEXT NOT NULL,
  discord_message_id TEXT,
  discord_author_id TEXT,
  discord_author_name TEXT NOT NULL,
  discord_author_avatar TEXT,
  content TEXT NOT NULL,
  is_from_kit INTEGER NOT NULL DEFAULT 0,
  is_read INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_channel ON chat_messages(channel_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);
`);

  // Seed brands
  const insert = db.prepare("INSERT INTO brands (name, slug, color, sort_order) VALUES (?, ?, ?, ?)");
  const brands = [
    ["TrustOffice", "trustoffice", "#c85a2a", 1],
    ["WingPoint", "wingpoint", "#6b7c4a", 2],
    ["AgenticTrust", "agentictrust", "#3d5a7a", 3],
    ["True Joy Birthing", "truejoybirthing", "#a0522d", 4],
    ["General", "general", "#888888", 0],
  ];
  for (const b of brands) insert.run(...b);

  console.log("✅ Auto-migration complete — tables seeded");
}

// ── Incremental migration for chat tables ──
function autoMigrateChatTables(db: Database) {
  const chatChannels = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_channels'").get();
  if (chatChannels) return; // Already migrated

  console.log("⚡ Adding chat tables...");
  db.exec(`
CREATE TABLE chat_channels (
  discord_channel_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  brand_id TEXT REFERENCES brands(id),
  last_message_at TEXT,
  unread_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE chat_messages (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  channel_id TEXT NOT NULL,
  channel_slug TEXT NOT NULL,
  discord_message_id TEXT,
  discord_author_id TEXT,
  discord_author_name TEXT NOT NULL,
  discord_author_avatar TEXT,
  content TEXT NOT NULL,
  is_from_kit INTEGER NOT NULL DEFAULT 0,
  is_read INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_chat_messages_channel ON chat_messages(channel_id);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at);
  `);
  console.log("✅ Chat tables created");
}

// ── Incremental migration for news table ──
function autoMigrateNewsTable(db: Database) {
  const exists = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='news'").get();
  if (exists) return; // Already migrated

  console.log("⚡ Adding news table...");
  db.exec(`
CREATE TABLE news (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  brand_id TEXT NOT NULL REFERENCES brands(id),
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_name TEXT DEFAULT '',
  category TEXT DEFAULT '',
  risk_tier TEXT NOT NULL DEFAULT('red') CHECK(risk_tier IN ('green','yellow','red')),
  jeff_comment TEXT DEFAULT '',
  jeff_recommends INTEGER NOT NULL DEFAULT(0),
  is_read INTEGER NOT NULL DEFAULT(0),
  intel_run_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT(datetime('now')),
  updated_at TEXT NOT NULL DEFAULT(datetime('now'))
);
CREATE INDEX idx_news_brand ON news(brand_id);
CREATE INDEX idx_news_risk ON news(risk_tier);
CREATE INDEX idx_news_run ON news(intel_run_id);
CREATE INDEX idx_news_created ON news(created_at);
  `);
  console.log("✅ News table created");
}

// ── Incremental migration for v2 columns + tables ──
function autoMigrateV2(db: Database) {
  // Add new columns to tasks table
  const newColumns = [
    { name: "blocked_on", type: "TEXT DEFAULT ''" },
    { name: "parent_task_id", type: "TEXT" },
    { name: "source", type: "TEXT DEFAULT 'mc_ui'" },
    { name: "lane", type: "TEXT DEFAULT ''" },
    { name: "checkpoint_summary", type: "TEXT DEFAULT ''" },
    { name: "checkpoint_at", type: "TEXT" },
  ];

  let addedAny = false;
  for (const col of newColumns) {
    try {
      db.exec(`ALTER TABLE tasks ADD COLUMN ${col.name} ${col.type}`);
      addedAny = true;
    } catch (e: any) {
      if (!e.message?.includes("duplicate column name")) throw e;
    }
  }

  // Create task_comments table
  const commentsExist = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='task_comments'").get();
  if (!commentsExist) {
    db.exec(`
CREATE TABLE task_comments (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  author TEXT NOT NULL DEFAULT 'kit' CHECK(author IN ('kit', 'jeff')),
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_comments_task ON task_comments(task_id);
CREATE INDEX idx_comments_created ON task_comments(created_at);
    `);
    addedAny = true;
  }

  // Create task_status_history table
  const historyExist = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='task_status_history'").get();
  if (!historyExist) {
    db.exec(`
CREATE TABLE task_status_history (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL,
  changed_by TEXT NOT NULL DEFAULT 'kit' CHECK(changed_by IN ('kit', 'jeff', 'system')),
  note TEXT DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_history_task ON task_status_history(task_id);
CREATE INDEX idx_history_created ON task_status_history(created_at);
    `);
    addedAny = true;
  }

  // Add indexes on new columns
  const newIndexes = [
    "CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_source ON tasks(source)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_blocked ON tasks(blocked_on)",
  ];
  for (const idx of newIndexes) {
    db.exec(idx);
  }

  if (addedAny) console.log("✅ V2 migration applied");
}

autoMigrate(db);
autoMigrateNewsTable(db);
autoMigrateV2(db);
import { brandsRouter } from "../routes/brands";
import { tasksRouter } from "../routes/tasks";
import { taskCommentsRouter } from "../routes/task-comments";
import { approvalsRouter } from "../routes/approvals";
import { activitiesRouter } from "../routes/activities";
import { costsRouter } from "../routes/costs";
import { statsRouter } from "../routes/stats";
import { filesRouter } from "../routes/files";
import { revenueRouter } from "../routes/revenue";
import { newsRouter } from "../routes/news";
import { wsHandlers } from "../ws";

const app = new Hono();

// ---------------------------------------------------------------------------
// Global middleware
// ---------------------------------------------------------------------------
const frontendUrl = process.env.FRONTEND_URL || "http://localhost:5173";
app.use(
  "*",
  cors({
    origin: [frontendUrl, "https://mc.agentictrust.app"],
    allowMethods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization", "X-MC-Key"],
    credentials: true,
  })
);
app.use("*", logger());

// ---------------------------------------------------------------------------
// Health endpoint (no auth)
// ---------------------------------------------------------------------------
app.get("/health", (c) => {
  const dbPath = process.env.DB_PATH ?? "./data/mc.db";
  let dbSizeKb = 0;
  try { dbSizeKb = Math.round(statSync(dbPath).size / 1024); } catch {}
  const tables = ["brands", "tasks", "approvals", "activities", "files", "daily_costs"];

  return c.json({
    status: "ok",
    version: "2.0.0",
    uptime_ms: Math.round(process.uptime() * 1000),
    db_size_kb: dbSizeKb,
    budget_limit: parseFloat(process.env.DAILY_BUDGET_USD ?? "2.00"),
    timestamp: new Date().toISOString(),
  });
});

// ---------------------------------------------------------------------------
// API v1 routes (auth required)
// ---------------------------------------------------------------------------
app.use("/api/v1/*", authMiddleware);

app.route("/api/v1/brands", brandsRouter);
app.route("/api/v1/tasks", tasksRouter);
app.route("/api/v1/tasks", taskCommentsRouter);
app.route("/api/v1/approvals", approvalsRouter);
app.route("/api/v1/activities", activitiesRouter);
app.route("/api/v1/costs", costsRouter);
app.route("/api/v1/stats", statsRouter);
app.route("/api/v1/files", filesRouter);
app.route("/api/v1/revenue", revenueRouter);
app.route("/api/v1/news", newsRouter);

// ── Chat routes (Discord bridge) ──
const chatRouter = createChatRouter(db, wsEmit, async (channelId: string, content: string) => {
  if (!discordBot) return null;
  return discordBot.sendMessage(channelId, content);
});
app.route("/api/v1/chat", chatRouter);

// ---------------------------------------------------------------------------
// Serve static frontend (built Vite output)
// ---------------------------------------------------------------------------
app.get(
  "/*",
  serveStatic({
    root: "./web/dist",
    rewriteRequestPath: (path) => {
      if (path.match(/\.\w+$/)) return path;
      return "/index.html";
    },
  })
);

// ---------------------------------------------------------------------------
// Start server with Bun native WebSocket support
// ---------------------------------------------------------------------------
const port = Number(process.env.PORT) || 3000;

Bun.serve({
  port,
  fetch(req, server) {
    // WebSocket upgrade handling
    if (new URL(req.url).pathname === "/ws") {
      const token = new URL(req.url).searchParams.get("token");
      if (token !== process.env.MC_AUTH_TOKEN) {
        return new Response("Unauthorized", { status: 401 });
      }
      if (server.upgrade(req)) {
        return; // WebSocket upgraded — no HTTP response needed
      }
      return new Response("WebSocket upgrade failed", { status: 400 });
    }
    // Everything else goes to Hono
    return app.fetch(req, server);
  },
  websocket: wsHandlers,
});

console.log(`🚀 Mission Control v2 running on port ${port}`);
console.log(`   Health: http://localhost:${port}/health`);
console.log(`   API:    http://localhost:${port}/api/v1`);
console.log(`   WS:     ws://localhost:${port}/ws`);

// ── Start Discord bot (non-blocking) ──
const discordBot = new DiscordBot(db, wsEmit);
discordBot.start().catch((err) => {
  console.error("[discord] Failed to start:", err.message);
});

// ── Graceful shutdown ──
const gracefulShutdown = async (signal: string) => {
  console.log(`\n🛑 Shutting down (${signal})...`);
  await discordBot.stop();
  db.close();
  process.exit(0);
};

process.on("SIGINT", () => gracefulShutdown("SIGINT"));
process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
