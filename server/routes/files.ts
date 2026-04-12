import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { eq, and, desc, asc, count, like, or } from "drizzle-orm";
import { db } from "../db";
import { files, taskFiles, tasks, brands } from "../schema";
import { authMiddleware } from "../middleware/auth";

export const filesRouter = new Hono();

// ---------------------------------------------------------------------------
// GET / — List files with optional filters
// ---------------------------------------------------------------------------
filesRouter.get("/", async (c) => {
  const category = c.req.query("category");
  const brandSlug = c.req.query("brand");
  const search = c.req.query("search");
  const limit = Math.min(parseInt(c.req.query("limit") ?? "100", 10), 500);
  const offset = parseInt(c.req.query("offset") ?? "0", 10);

  const conditions: any[] = [];

  if (category) conditions.push(eq(files.category, category as any));

  if (brandSlug) {
    const [brand] = await db.select({ id: brands.id }).from(brands).where(eq(brands.slug, brandSlug)).limit(1);
    if (brand) conditions.push(eq(files.brand_id, brand.id));
  }

  if (search) {
    conditions.push(
      or(
        like(files.name, `%${search}%`),
        like(files.path, `%${search}%`),
        like(files.label, `%${search}%`)
      )
    );
  }

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

  const query = db
    .select({
      id: files.id,
      path: files.path,
      name: files.name,
      label: files.label,
      category: files.category,
      brand_id: files.brand_id,
      brand_name: brands.name,
      brand_slug: brands.slug,
      preview: files.preview,
      task_count: count(taskFiles.id),
      last_linked: files.updated_at,
      created_at: files.created_at,
    })
    .from(files)
    .leftJoin(brands, eq(files.brand_id, brands.id))
    .leftJoin(taskFiles, eq(taskFiles.file_path, files.path))
    .groupBy(files.id)
    .orderBy(asc(files.category), asc(files.name));

  const whereQuery = whereClause ? query.where(whereClause) : query;
  const items = await whereQuery.limit(limit).offset(offset);

  const [totalRow] = await db.select({ total: count() }).from(files).where(whereClause ?? undefined);

  return c.json({
    items: items.map((item) => ({
      ...item,
      task_count: Number(item.task_count) ?? 0,
    })),
    total: Number(totalRow?.total) ?? 0,
    limit,
    offset,
  });
});

// ---------------------------------------------------------------------------
// POST / — Register a file (Kit calls this)
// ---------------------------------------------------------------------------
const createFileSchema = z.object({
  path: z.string().min(1),
  name: z.string().min(1),
  label: z.string().default(""),
  category: z.enum(["skill", "brand_doc", "daily_note", "config", "output", "other"]).default("other"),
  brand_slug: z.string().optional(),
  preview: z.string().default(""),
});

filesRouter.post("/", zValidator("json", createFileSchema), async (c) => {
  const body = c.req.valid("json");

  // Resolve brand
  let brand_id: string | null = null;
  if (body.brand_slug) {
    const [brand] = await db.select({ id: brands.id }).from(brands).where(eq(brands.slug, body.brand_slug)).limit(1);
    if (brand) brand_id = brand.id;
  }

  // Upsert — update if path exists, insert if not
  const [existing] = await db.select({ id: files.id }).from(files).where(eq(files.path, body.path)).limit(1);

  if (existing) {
    await db
      .update(files)
      .set({
        name: body.name,
        label: body.label,
        category: body.category,
        brand_id,
        preview: body.preview,
        updated_at: new Date().toISOString().replace("T", " ").substring(0, 19),
      })
      .where(eq(files.id, existing.id));

    const [item] = await db.select().from(files).where(eq(files.id, existing.id)).limit(1);
    return c.json(item, 200);
  } else {
    await db.insert(files).values({
      path: body.path,
      name: body.name,
      label: body.label,
      category: body.category,
      brand_id,
      preview: body.preview,
    });

    const [item] = await db.select().from(files).where(eq(files.path, body.path)).limit(1);
    return c.json(item, 201);
  }
});

// ---------------------------------------------------------------------------
// DELETE /:id — Remove a file from registry
// ---------------------------------------------------------------------------
filesRouter.delete("/:id", authMiddleware, async (c) => {
  const id = c.req.param("id");
  await db.delete(files).where(eq(files.id, id));
  return c.json({ ok: true });
});

// ---------------------------------------------------------------------------
// GET /task-files/:taskId — Files linked to a specific task
// ---------------------------------------------------------------------------
filesRouter.get("/task-files/:taskId", authMiddleware, async (c) => {
  const taskId = c.req.param("taskId");

  const items = await db
    .select({
      id: taskFiles.id,
      task_id: taskFiles.task_id,
      file_path: taskFiles.file_path,
      role: taskFiles.role,
      label: taskFiles.label,
      created_at: taskFiles.created_at,
      // File registry info (if registered)
      registry_id: files.id,
      file_name: files.name,
      file_category: files.category,
      file_preview: files.preview,
    })
    .from(taskFiles)
    .leftJoin(files, eq(taskFiles.file_path, files.path))
    .where(eq(taskFiles.task_id, taskId))
    .orderBy(asc(taskFiles.role));

  return c.json({ items });
});

// ---------------------------------------------------------------------------
// POST /:id/link — Link a file to a task
// ---------------------------------------------------------------------------
const linkFileSchema = z.object({
  task_id: z.string(),
  role: z.enum(["skill", "output", "context", "input", "reference"]).default("context"),
  label: z.string().default(""),
});

filesRouter.post("/:id/link", authMiddleware, zValidator("json", linkFileSchema), async (c) => {
  const fileId = c.req.param("id");
  const body = c.req.valid("json");

  // Get file path
  const [file] = await db.select({ path: files.path }).from(files).where(eq(files.id, fileId)).limit(1);
  if (!file) return c.json({ error: "File not found" }, 404);

  await db.insert(taskFiles).values({
    task_id: body.task_id,
    file_path: file.path,
    role: body.role,
    label: body.label,
  });

  return c.json({ ok: true }, 201);
});
