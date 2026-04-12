import { Database } from "bun:sqlite";
import { mkdirSync } from "fs";

const dbPath = process.env.DB_PATH ?? "./data/mc.db";
const dbDir = dbPath.substring(0, dbPath.lastIndexOf("/"));
if (dbDir) mkdirSync(dbDir, { recursive: true });

const db = new Database(dbPath);
db.exec("PRAGMA journal_mode = WAL");
db.exec("PRAGMA foreign_keys = ON");

// Drop all tables for clean rebuild
db.exec(`
  DROP TABLE IF EXISTS webauthn_credentials;
  DROP TABLE IF EXISTS notifications;
  DROP TABLE IF EXISTS revenue_snapshots;
  DROP TABLE IF EXISTS daily_costs;
  DROP TABLE IF EXISTS cron_jobs;
  DROP TABLE IF EXISTS activities;
  DROP TABLE IF EXISTS approvals;
  DROP TABLE IF EXISTS task_files;
  DROP TABLE IF EXISTS tasks;
  DROP TABLE IF EXISTS brands;
`);

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
CREATE INDEX idx_task_files_task ON task_files(task_id);
CREATE INDEX idx_task_files_path ON task_files(file_path);

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
CREATE INDEX idx_approvals_status ON approvals(status);
CREATE INDEX idx_approvals_brand ON approvals(brand_id);
CREATE INDEX idx_approvals_risk ON approvals(risk_tier);

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
CREATE INDEX idx_activities_brand ON activities(brand_id);
CREATE INDEX idx_activities_created ON activities(created_at);
CREATE INDEX idx_activities_actor ON activities(actor);
CREATE INDEX idx_activities_brand_created ON activities(brand_id, created_at);

CREATE TABLE cron_jobs (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  brand_id TEXT REFERENCES brands(id),
  schedule_expr TEXT NOT NULL,
  schedule_ms INTEGER,
  cron_expr TEXT,
  enabled INTEGER NOT NULL DEFAULT 1,
  last_run_at TEXT,
  last_status TEXT DEFAULT 'unknown' CHECK(last_status IN ('success','error','running','unknown')),
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
CREATE INDEX idx_daily_costs_date ON daily_costs(date);

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
CREATE INDEX idx_revenue_date ON revenue_snapshots(date);

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
CREATE INDEX idx_webauthn_user ON webauthn_credentials(user_id);
CREATE UNIQUE INDEX idx_webauthn_credential ON webauthn_credentials(credential_id);
`);

console.log("✅ Migration complete — all 10 tables created (matching Drizzle schema)");

// Seed brands
const BRANDS = [
  { name: "TrustOffice", slug: "trustoffice", color: "#c85a2a", sort_order: 1 },
  { name: "WingPoint", slug: "wingpoint", color: "#6b7c4a", sort_order: 2 },
  { name: "AgenticTrust", slug: "agentictrust", color: "#3d5a7a", sort_order: 3 },
  { name: "True Joy Birthing", slug: "truejoybirthing", color: "#a0522d", sort_order: 4 },
];

const insert = db.prepare(
  "INSERT OR IGNORE INTO brands (name, slug, color, sort_order) VALUES (?, ?, ?, ?)"
);
for (const b of BRANDS) insert.run(b.name, b.slug, b.color, b.sort_order);

console.log("✅ Seed complete — 4 brands inserted");
