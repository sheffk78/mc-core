/**
 * Migration: Add blocked_on, parent_task_id, source, lane, checkpoint fields to tasks
 *           + Create task_comments and task_status_history tables
 * 
 * Run with: bun run server/scripts/migrate-v2.ts
 */

import { Database } from "bun:sqlite";

const dbPath = process.env.DB_PATH ?? "./data/mc.db";

console.log(`[migrate-v2] Opening database: ${dbPath}`);
const db = new Database(dbPath);

// Enable WAL mode
db.exec("PRAGMA journal_mode = WAL");
db.exec("PRAGMA foreign_keys = ON");

console.log("[migrate-v2] Adding new columns to tasks table...");

// Add new columns to tasks (ignore if already exist)
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
    console.log(`  ✓ Added column: ${col.name}`);
  } catch (e: any) {
    if (e.message?.includes("duplicate column name")) {
      console.log(`  ✓ Column already exists: ${col.name}`);
    } else {
      throw e;
    }
  }
}

console.log("[migrate-v2] Creating task_comments table...");
db.exec(`
  CREATE TABLE IF NOT EXISTS task_comments (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    author TEXT NOT NULL DEFAULT 'kit' CHECK(author IN ('kit', 'jeff')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  )
`);
db.exec("CREATE INDEX IF NOT EXISTS idx_comments_task ON task_comments(task_id)");
db.exec("CREATE INDEX IF NOT EXISTS idx_comments_created ON task_comments(created_at)");

console.log("[migrate-v2] Creating task_status_history table...");
db.exec(`
  CREATE TABLE IF NOT EXISTS task_status_history (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    changed_by TEXT NOT NULL DEFAULT 'kit' CHECK(changed_by IN ('kit', 'jeff', 'system')),
    note TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  )
`);
db.exec("CREATE INDEX IF NOT EXISTS idx_history_task ON task_status_history(task_id)");
db.exec("CREATE INDEX IF NOT EXISTS idx_history_created ON task_status_history(created_at)");

console.log("[migrate-v2] Adding new status to tasks status enum...");
// SQLite doesn't support ALTER COLUMN, but we store status as TEXT anyway
// We need to add 'blocked' as a valid status
// The existing ALLOWED_TRANSITIONS in the route handler will be updated separately

console.log("[migrate-v2] Creating indexes on new columns...");
try {
  db.exec("CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id)");
  console.log("  ✓ idx_tasks_parent");
} catch (e: any) {
  console.log(`  ✓ idx_tasks_parent (already exists or skipped)`);
}

try {
  db.exec("CREATE INDEX IF NOT EXISTS idx_tasks_source ON tasks(source)");
  console.log("  ✓ idx_tasks_source");
} catch (e: any) {
  console.log(`  ✓ idx_tasks_source (already exists or skipped)`);
}

try {
  db.exec("CREATE INDEX IF NOT EXISTS idx_tasks_blocked ON tasks(blocked_on)");
  console.log("  ✓ idx_tasks_blocked");
} catch (e: any) {
  console.log(`  ✓ idx_tasks_blocked (already exists or skipped)`);
}

console.log("[migrate-v2] ✅ Migration complete!");
db.close();