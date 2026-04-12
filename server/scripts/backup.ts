/**
 * backup.ts — Copy mc.db to a timestamped backup location.
 *
 * Usage:
 *   bun run server/scripts/backup.ts
 *   bun run server/scripts/backup.ts /path/to/custom/backup/dir
 */

const DEFAULT_DB_PATH = process.env.DB_PATH || "./data/mc.db";
const DEFAULT_BACKUP_DIR = "./data/backups";

async function backup() {
  const dbPath = Bun.resolveSync(DEFAULT_DB_PATH, process.cwd());
  const backupDir = process.argv[2]
    ? Bun.resolveSync(process.argv[2], process.cwd())
    : Bun.resolveSync(DEFAULT_BACKUP_DIR, process.cwd());

  // Ensure backup directory exists
  await Bun.write(Bun.file(`${backupDir}/.keep`), "");

  // Check that the database file exists
  const dbFile = Bun.file(dbPath);
  if (!(await dbFile.exists())) {
    console.error(`❌ Database not found at: ${dbPath}`);
    process.exit(1);
  }

  // Create timestamped backup filename
  const timestamp = new Date()
    .toISOString()
    .replace(/[:.]/g, "-")
    .slice(0, 19);
  const backupPath = `${backupDir}/mc-${timestamp}.db`;

  // Copy the database file
  const source = Bun.file(dbPath);
  const dest = Bun.file(backupPath);
  await Bun.write(dest, source);

  const size = (await Bun.file(backupPath).size) / 1024;
  console.log(`✅ Backup created: ${backupPath} (${size.toFixed(1)} KB)`);

  // List recent backups
  const { readdirSync, statSync } = await import("fs");
  const backups = readdirSync(backupDir)
    .filter((f) => f.startsWith("mc-") && f.endsWith(".db"))
    .sort()
    .reverse();

  console.log(`\n📁 Recent backups (${backups.length} total):`);
  for (const b of backups.slice(0, 5)) {
    const s = statSync(`${backupDir}/${b}`);
    console.log(`   ${b}  (${(s.size / 1024).toFixed(1)} KB)`);
  }

  // Prune backups older than 30 days
  const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
  let pruned = 0;
  for (const b of backups) {
    const s = statSync(`${backupDir}/${b}`);
    if (s.mtimeMs < thirtyDaysAgo) {
      const { unlinkSync } = await import("fs");
      unlinkSync(`${backupDir}/${b}`);
      pruned++;
    }
  }
  if (pruned > 0) {
    console.log(`\n🗑️  Pruned ${pruned} backup(s) older than 30 days`);
  }
}

backup().catch((err) => {
  console.error("❌ Backup failed:", err);
  process.exit(1);
});
