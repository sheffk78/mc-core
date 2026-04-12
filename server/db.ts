import { Database } from "bun:sqlite";
import { drizzle } from "drizzle-orm/bun-sqlite";
import * as schema from "./schema";
import { mkdirSync } from "fs";

// Ensure data directory exists
const dbPath = process.env.DB_PATH ?? "./data/mc.db";
const dbDir = dbPath.substring(0, dbPath.lastIndexOf("/"));
if (dbDir) {
  mkdirSync(dbDir, { recursive: true });
}

// Create SQLite connection using Bun's built-in SQLite
const sqlite = new Database(dbPath);

// Enable WAL mode for concurrent read performance
sqlite.exec("PRAGMA journal_mode = WAL");

// Enable foreign key enforcement
sqlite.exec("PRAGMA foreign_keys = ON");

// Export Drizzle instance with full schema (enables relational queries)
export const db = drizzle(sqlite, { schema });

// Export raw connection for migration use
export { sqlite };
