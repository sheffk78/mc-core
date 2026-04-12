import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { serveStatic } from "hono/bun";

import { authMiddleware } from "../middleware/auth";

// ---------------------------------------------------------------------------
// Auto-migrate on first boot
// ---------------------------------------------------------------------------
import { Database } from "bun:sqlite";
import { mkdirSync, existsSync } from "fs";
import { join } from "path";

function autoMigrate() {
  const dbPath = process.env.DB_PATH ?? "./data/mc.db";
  const dbDir = dbPath.substring(0, dbPath.lastIndexOf("/"));
  if (dbDir) mkdirSync(dbDir, { recursive: true });

  const db = new Database(dbPath);
  db.exec("PRAGMA journal_mode = WAL");
  db.exec("PRAGMA foreign_keys = ON");

  // Check if tables exist
  const table = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='brands'").get();
  if (table) { db.close(); return; }

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
`);

  // Seed brands
  const insert = db.prepare("INSERT INTO brands (name, slug, color, sort_order) VALUES (?, ?, ?, ?)");
  const brands = [
    ["TrustOffice", "trustoffice", "#c85a2a", 1],
    ["WingPoint", "wingpoint", "#6b7c4a", 2],
    ["AgenticTrust", "agentictrust", "#3d5a7a", 3],
    ["True Joy Birthing", "truejoybirthing", "#a0522d", 4],
  ];
  for (const b of brands) insert.run(...b);

  db.close();
  console.log("✅ Auto-migration complete — 10 tables, 4 brands seeded");
}

autoMigrate();
import { brandsRouter } from "../routes/brands";
import { tasksRouter } from "../routes/tasks";
import { approvalsRouter } from "../routes/approvals";
import { activitiesRouter } from "../routes/activities";
import { costsRouter } from "../routes/costs";
import { statsRouter } from "../routes/stats";
import { revenueRouter } from "../routes/revenue";
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
  return c.json({
    status: "ok",
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

// ---------------------------------------------------------------------------
// API v1 routes (auth required)
// ---------------------------------------------------------------------------
app.use("/api/v1/*", authMiddleware);

app.route("/api/v1/brands", brandsRouter);
app.route("/api/v1/tasks", tasksRouter);
app.route("/api/v1/approvals", approvalsRouter);
app.route("/api/v1/activities", activitiesRouter);
app.route("/api/v1/costs", costsRouter);
app.route("/api/v1/stats", statsRouter);
app.route("/api/v1/revenue", revenueRouter);

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
