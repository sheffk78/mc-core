/**
 * V2 Migration: Add 'blocked' status to CHECK constraint + new columns + new tables
 * 
 * This MUST run before the server starts because SQLite CHECK constraints
 * are immutable — we have to recreate the tasks table.
 */

import { Database } from "bun:sqlite";

export function migrateV2(db: Database): void {
  let addedAny = false;

  // ── Step 1: Migrate tasks table to add 'blocked' to CHECK constraint ──
  const tasksSchema = db
    .prepare("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
    .get() as { sql: string } | null;
  
  if (tasksSchema && !tasksSchema.sql.includes('blocked')) {
    console.log("⚡ Migrating tasks table to add 'blocked' status...");
    try {
      // Turn off foreign keys for the table recreation
      db.exec("PRAGMA foreign_keys = OFF;");
      
      db.exec(`
        CREATE TABLE tasks_new (
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
      
      // Copy data from old table — new columns get defaults
      db.exec(`
        INSERT INTO tasks_new 
          (id, brand_id, title, description, status, priority, risk_tier, assignee, 
           category, agent_note, user_note, due_date, completed_at, estimated_cost, 
           actual_cost, model_used, tokens_in, tokens_out, confidence,
           blocked_on, parent_task_id, source, lane, checkpoint_summary, checkpoint_at,
           created_at, updated_at)
        SELECT 
          id, brand_id, title, description, status, priority, risk_tier, assignee, 
          category, agent_note, user_note, due_date, completed_at, estimated_cost, 
          actual_cost, model_used, tokens_in, tokens_out, confidence,
          '', NULL, 'mc_ui', '', '', NULL,
          created_at, updated_at
        FROM tasks;
      `);
      
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
      
      // Re-enable foreign keys
      db.exec("PRAGMA foreign_keys = ON;");
      
      console.log("✅ Tasks table migrated: 'blocked' status + new columns");
      addedAny = true;
    } catch (e: any) {
      db.exec("PRAGMA foreign_keys = ON;");
      console.error("❌ Tasks table migration failed:", e.message);
      // Don't throw — let the server try to start anyway
    }
  } else if (tasksSchema) {
    // Table already has 'blocked' — just add columns if missing
    const newColumns = [
      { name: "blocked_on", type: "TEXT DEFAULT ''" },
      { name: "parent_task_id", type: "TEXT" },
      { name: "source", type: "TEXT DEFAULT 'mc_ui'" },
      { name: "lane", type: "TEXT DEFAULT ''" },
      { name: "checkpoint_summary", type: "TEXT DEFAULT ''" },
      { name: "checkpoint_at", type: "TEXT" },
    ];

    for (const col of newColumns) {
      try {
        db.exec(`ALTER TABLE tasks ADD COLUMN ${col.name} ${col.type}`);
        addedAny = true;
      } catch (e: any) {
        if (!e.message?.includes("duplicate column name")) throw e;
      }
    }
  }

  // ── Step 2: Create task_comments table ──
  const commentsExist = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='task_comments'").get();
  if (!commentsExist) {
    db.exec(`
CREATE TABLE IF NOT EXISTS task_comments (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  author TEXT NOT NULL DEFAULT 'kit' CHECK(author IN ('kit', 'jeff')),
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_comments_task ON task_comments(task_id);
CREATE INDEX IF NOT EXISTS idx_comments_created ON task_comments(created_at);
    `);
    addedAny = true;
  }

  // ── Step 3: Create task_status_history table ──
  const historyExist = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='task_status_history'").get();
  if (!historyExist) {
    db.exec(`
CREATE TABLE IF NOT EXISTS task_status_history (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
  task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL,
  changed_by TEXT NOT NULL DEFAULT 'kit' CHECK(changed_by IN ('kit', 'jeff', 'system')),
  note TEXT DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_history_task ON task_status_history(task_id);
CREATE INDEX IF NOT EXISTS idx_history_created ON task_status_history(created_at);
    `);
    addedAny = true;
  }

  // ── Step 4: Ensure indexes exist ──
  const indexChecks = [
    "CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_source ON tasks(source)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_blocked ON tasks(blocked_on)",
  ];
  for (const idx of indexChecks) {
    db.exec(idx);
  }

  if (addedAny) console.log("✅ V2 migration applied");
}