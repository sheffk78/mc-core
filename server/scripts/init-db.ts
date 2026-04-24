import { Database } from "bun:sqlite";
import { mkdirSync } from "fs";

const dbPath = process.env.DB_PATH ?? "./data/mc.db";
const dbDir = dbPath.substring(0, dbPath.lastIndexOf("/"));
if (dbDir) mkdirSync(dbDir, { recursive: true });

const db = new Database(dbPath);
db.exec("PRAGMA journal_mode = WAL");
db.exec("PRAGMA foreign_keys = ON");

// Check if tables already exist
const tableCount = db
  .prepare("SELECT count(*) as cnt FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
  .get() as { cnt: number };

if (tableCount.cnt >= 11) {
  console.log("✅ Database already initialized (tables: " + tableCount.cnt + ") — running incremental migrations");
  
  // ── V2 Migration: Add 'blocked' to tasks status CHECK constraint ──
  // SQLite doesn't support ALTER COLUMN, so we recreate the tasks table
  const statusCheck = db
    .prepare("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
    .get() as { sql: string } | null;
  
  if (statusCheck && !statusCheck.sql.includes('blocked')) {
    console.log("⚡ Migrating tasks table to add 'blocked' status...");
    try {
      db.exec(`
        CREATE TABLE tasks_new (
          id TEXT PRIMARY KEY,
          brand_id TEXT NOT NULL REFERENCES brands(id),
          title TEXT NOT NULL,
          description TEXT DEFAULT '',
          status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','in_progress','blocked','pending_review','approved','rejected','completed','archived')),
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
          blocked_on TEXT DEFAULT '',
          parent_task_id TEXT,
          source TEXT DEFAULT 'mc_ui',
          lane TEXT DEFAULT '',
          checkpoint_summary TEXT DEFAULT '',
          checkpoint_at TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
      `);
      
      // Copy data from old table to new
      db.exec(`
        INSERT INTO tasks_new SELECT 
          id, brand_id, title, description, status, priority, risk_tier, assignee, 
          category, agent_note, user_note, due_date, completed_at, estimated_cost, 
          actual_cost, model_used, tokens_in, tokens_out, confidence,
          '', NULL, 'mc_ui', '', '', NULL,
          created_at, updated_at
        FROM tasks;
      `);
      
      // Drop old table and rename
      db.exec("DROP TABLE tasks;");
      db.exec("ALTER TABLE tasks_new RENAME TO tasks;");
      
      // Recreate indexes
      db.exec("CREATE INDEX idx_tasks_brand ON tasks(brand_id);");
      db.exec("CREATE INDEX idx_tasks_status ON tasks(status);");
      db.exec("CREATE INDEX idx_tasks_assignee ON tasks(assignee);");
      db.exec("CREATE INDEX idx_tasks_risk ON tasks(risk_tier);");
      db.exec("CREATE INDEX idx_tasks_due ON tasks(due_date);");
      db.exec("CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id);");
      db.exec("CREATE INDEX IF NOT EXISTS idx_tasks_source ON tasks(source);");
      db.exec("CREATE INDEX IF NOT EXISTS idx_tasks_blocked ON tasks(blocked_on);");
      
      console.log("✅ Tasks table migrated with 'blocked' status + new columns");
    } catch (e: any) {
      console.error("❌ Migration failed:", e.message);
      // Continue — the server's auto-migrate might handle it
    }
  }
  
  // ── V2 Migration: Add task_comments and task_status_history tables ──
  const commentsExist = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='task_comments'").get();
  if (!commentsExist) {
    console.log("⚡ Adding task_comments table...");
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
    console.log("✅ task_comments table created");
  }
  
  const historyExist = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='task_status_history'").get();
  if (!historyExist) {
    console.log("⚡ Adding task_status_history table...");
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
    console.log("✅ task_status_history table created");
  }
  
  process.exit(0);
}

console.log("🔧 Creating tables...");

db.exec(`
CREATE TABLE IF NOT EXISTS brands (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  color TEXT NOT NULL DEFAULT '#c85a2a',
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_brands_slug ON brands(slug);

CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  brand_id TEXT NOT NULL REFERENCES brands(id),
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','in_progress','blocked','pending_review','approved','rejected','completed','archived')),
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
CREATE INDEX IF NOT EXISTS idx_tasks_brand ON tasks(brand_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee);
CREATE INDEX IF NOT EXISTS idx_tasks_risk ON tasks(risk_tier);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);

CREATE TABLE IF NOT EXISTS task_files (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'context' CHECK(role IN ('skill','output','context','input','reference')),
  label TEXT DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_task_files_task ON task_files(task_id);
CREATE INDEX IF NOT EXISTS idx_task_files_path ON task_files(file_path);

CREATE TABLE IF NOT EXISTS approvals (
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
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_approvals_brand ON approvals(brand_id);
CREATE INDEX IF NOT EXISTS idx_approvals_risk ON approvals(risk_tier);

CREATE TABLE IF NOT EXISTS activities (
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
CREATE INDEX IF NOT EXISTS idx_activities_brand ON activities(brand_id);
CREATE INDEX IF NOT EXISTS idx_activities_created ON activities(created_at);
CREATE INDEX IF NOT EXISTS idx_activities_actor ON activities(actor);
CREATE INDEX IF NOT EXISTS idx_activities_brand_created ON activities(brand_id, created_at);

CREATE TABLE IF NOT EXISTS cron_jobs (
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

CREATE TABLE IF NOT EXISTS daily_costs (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  date TEXT NOT NULL,
  brand_id TEXT REFERENCES brands(id),
  model TEXT NOT NULL,
  tokens_in INTEGER NOT NULL DEFAULT 0,
  tokens_out INTEGER NOT NULL DEFAULT 0,
  cost_usd REAL NOT NULL DEFAULT 0.0,
  task_count INTEGER NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_costs_unique ON daily_costs(date, brand_id, model);
CREATE INDEX IF NOT EXISTS idx_daily_costs_date ON daily_costs(date);

CREATE TABLE IF NOT EXISTS revenue_snapshots (
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
CREATE UNIQUE INDEX IF NOT EXISTS idx_revenue_brand_date ON revenue_snapshots(brand_id, date);
CREATE INDEX IF NOT EXISTS idx_revenue_date ON revenue_snapshots(date);

CREATE TABLE IF NOT EXISTS notifications (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  channel TEXT NOT NULL CHECK(channel IN ('slack','email','dashboard')),
  recipient TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT DEFAULT '',
  related_id TEXT,
  sent_at TEXT NOT NULL DEFAULT (datetime('now')),
  status TEXT NOT NULL DEFAULT 'sent' CHECK(status IN ('sent','failed','read'))
);

CREATE TABLE IF NOT EXISTS webauthn_credentials (
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
CREATE INDEX IF NOT EXISTS idx_webauthn_user ON webauthn_credentials(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_webauthn_credential ON webauthn_credentials(credential_id);
`);

console.log("✅ Tables created");

// ── Incremental: ensure news table exists (added v2.1) ──
const newsExists = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='news'").get();
if (!newsExists) {
  console.log("⚡ Adding news table...");
  db.exec(`
CREATE TABLE IF NOT EXISTS news (
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
CREATE INDEX IF NOT EXISTS idx_news_brand ON news(brand_id);
CREATE INDEX IF NOT EXISTS idx_news_risk ON news(risk_tier);
CREATE INDEX IF NOT EXISTS idx_news_run ON news(intel_run_id);
CREATE INDEX IF NOT EXISTS idx_news_created ON news(created_at);
  `);
  console.log("✅ News table created");
}

// Seed brands (idempotent)
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

console.log("✅ Seed complete — 4 brands ensured");
