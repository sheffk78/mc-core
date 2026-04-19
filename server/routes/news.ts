import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { eq, and, desc, count, sql, inArray } from "drizzle-orm";
import { db, sqlite } from "../db";
import { brands, news } from "../schema";
import { authMiddleware } from "../middleware/auth";
import { wsEmit } from "../ws";

export const newsRouter = new Hono();

// ---------------------------------------------------------------------------
// GET / — List news with 4-run window
// ---------------------------------------------------------------------------
newsRouter.get("/", async (c) => {
  const brandSlug = c.req.query("brand");
  const riskTier = c.req.query("risk_tier");
  const intelRunId = c.req.query("intel_run_id");
  const limit = Math.min(parseInt(c.req.query("limit") ?? "50", 10), 200);
  const offset = parseInt(c.req.query("offset") ?? "0", 10);

  // Resolve brand_id if filtering by slug
  let brandId: string | undefined;
  if (brandSlug) {
    const [brand] = await db
      .select({ id: brands.id })
      .from(brands)
      .where(eq(brands.slug, brandSlug))
      .limit(1);
    if (brand) {
      brandId = brand.id;
    } else {
      return c.json({ items: [], total: 0, limit, offset });
    }
  }

  // Build base conditions
  const conditions: any[] = [];
  if (brandId) conditions.push(eq(news.brand_id, brandId));
  if (riskTier) conditions.push(eq(news.risk_tier, riskTier as any));

  // 4-run window logic: if no specific intel_run_id provided,
  // filter to only the 4 most recent distinct intel_run_ids
  let runIds: string[] | null = null;

  if (intelRunId) {
    conditions.push(eq(news.intel_run_id, intelRunId));
  } else {
    // Get the 4 most recent distinct intel_run_ids using parameterized query
    const stmt = brandId
      ? sqlite.prepare('SELECT DISTINCT intel_run_id FROM news WHERE brand_id = ? ORDER BY created_at DESC LIMIT 4')
      : sqlite.prepare('SELECT DISTINCT intel_run_id FROM news ORDER BY created_at DESC LIMIT 4');
    const runRows = (brandId ? stmt.all(brandId) : stmt.all()) as { intel_run_id: string }[];
    runIds = runRows.map((r) => r.intel_run_id);

    if (runIds.length > 0) {
      conditions.push(inArray(news.intel_run_id, runIds));
    } else {
      // No news at all — return empty
      return c.json({ items: [], total: 0, limit, offset });
    }
  }

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

  // Get total count
  const [{ total }] = await db
    .select({ total: count() })
    .from(news)
    .where(whereClause);

  // Get items with brand join
  const items = await db
    .select({
      ...news,
      brand_slug: brands.slug,
      brand_name: brands.name,
      brand_color: brands.color,
    })
    .from(news)
    .leftJoin(brands, eq(news.brand_id, brands.id))
    .where(whereClause)
    .orderBy(
      // Risk tier priority: red > yellow > green
      sql`CASE ${news.risk_tier} WHEN 'red' THEN 0 WHEN 'yellow' THEN 1 ELSE 2 END`,
      desc(news.created_at)
    )
    .limit(limit)
    .offset(offset);

  return c.json({ items, total, limit, offset });
});

// ---------------------------------------------------------------------------
// GET /:id — Single news item with brand join
// ---------------------------------------------------------------------------
newsRouter.get("/:id", async (c) => {
  const id = c.req.param("id");

  const [item] = await db
    .select({
      ...news,
      brand_slug: brands.slug,
      brand_name: brands.name,
      brand_color: brands.color,
    })
    .from(news)
    .leftJoin(brands, eq(news.brand_id, brands.id))
    .where(eq(news.id, id))
    .limit(1);

  if (!item) {
    return c.json({ error: "News item not found" }, 404);
  }

  return c.json(item);
});

// ---------------------------------------------------------------------------
// POST / — Create a news item (auth required)
// ---------------------------------------------------------------------------
const createNewsSchema = z.object({
  brand_slug: z.string().min(1),
  title: z.string().min(1),
  summary: z.string().min(1),
  source_url: z.string().min(1),
  source_name: z.string().optional(),
  category: z.string().optional(),
  risk_tier: z.enum(["green", "yellow", "red"]).optional(),
  intel_run_id: z.string().min(1),
});

newsRouter.post(
  "/",
  authMiddleware,
  zValidator("json", createNewsSchema),
  async (c) => {
    const body = c.req.valid("json");

    // Resolve brand_id from slug
    const [brand] = await db
      .select({ id: brands.id })
      .from(brands)
      .where(eq(brands.slug, body.brand_slug))
      .limit(1);

    if (!brand) {
      return c.json({ error: `Brand '${body.brand_slug}' not found` }, 422);
    }

    const [created] = await db
      .insert(news)
      .values({
        brand_id: brand.id,
        title: body.title,
        summary: body.summary,
        source_url: body.source_url,
        source_name: body.source_name ?? "",
        category: body.category ?? "",
        risk_tier: body.risk_tier ?? "red",
        intel_run_id: body.intel_run_id,
      })
      .returning();

    // Re-query with brand join for WS event
    const [createdWithBrand] = await db
      .select({
        ...news,
        brand_slug: brands.slug,
        brand_name: brands.name,
        brand_color: brands.color,
      })
      .from(news)
      .leftJoin(brands, eq(news.brand_id, brands.id))
      .where(eq(news.id, created.id))
      .limit(1);

    // Broadcast WebSocket event with brand info
    wsEmit("news.created", createdWithBrand);

    return c.json(created, 201);
  }
);

// ---------------------------------------------------------------------------
// PATCH /:id — Update a news item (auth required)
// ---------------------------------------------------------------------------
const updateNewsSchema = z.object({
  jeff_comment: z.string().optional(),
  jeff_recommends: z.number().min(0).max(1).optional(),
  is_read: z.number().min(0).max(1).optional(),
  title: z.string().optional(),
  summary: z.string().optional(),
});

newsRouter.patch(
  "/:id",
  authMiddleware,
  zValidator("json", updateNewsSchema),
  async (c) => {
    const id = c.req.param("id");
    const body = c.req.valid("json");

    // Check exists
    const [existing] = await db
      .select()
      .from(news)
      .where(eq(news.id, id))
      .limit(1);

    if (!existing) {
      return c.json({ error: "News item not found" }, 404);
    }

    const updates: Record<string, any> = { ...body };
    updates.updated_at = sql`datetime('now')`;

    const [updated] = await db
      .update(news)
      .set(updates)
      .where(eq(news.id, id))
      .returning();

    // Re-query with brand join for WS event
    const [updatedWithBrand] = await db
      .select({
        ...news,
        brand_slug: brands.slug,
        brand_name: brands.name,
        brand_color: brands.color,
      })
      .from(news)
      .leftJoin(brands, eq(news.brand_id, brands.id))
      .where(eq(news.id, updated.id))
      .limit(1);

    // Broadcast with brand info
    wsEmit("news.updated", updatedWithBrand);

    return c.json(updated);
  }
);

// ---------------------------------------------------------------------------
// DELETE /:id — Hard delete (auth required)
// ---------------------------------------------------------------------------
newsRouter.delete("/:id", authMiddleware, async (c) => {
  const id = c.req.param("id");

  // Check exists
  const [existing] = await db
    .select()
    .from(news)
    .where(eq(news.id, id))
    .limit(1);

  if (!existing) {
    return c.json({ error: "News item not found" }, 404);
  }

  await db.delete(news).where(eq(news.id, id));

  return c.body(null, 204);
});