import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { eq, and, desc, asc, sql, gte, lte, max } from "drizzle-orm";
import { db } from "../db";
import { brands, revenueSnapshots } from "../schema";
import { authMiddleware } from "../middleware/auth";

export const revenueRouter = new Hono();

// ---------------------------------------------------------------------------
// GET / — Latest revenue snapshot per brand (no auth required)
// ---------------------------------------------------------------------------
revenueRouter.get("/", async (c) => {
  // Get all brands
  const allBrands = await db.select().from(brands).orderBy(brands.sort_order);

  // For each brand, get the most recent revenue snapshot
  const result = await Promise.all(
    allBrands.map(async (brand) => {
      const [latest] = await db
        .select()
        .from(revenueSnapshots)
        .where(eq(revenueSnapshots.brand_id, brand.id))
        .orderBy(desc(revenueSnapshots.date))
        .limit(1);

      return {
        brand_id: brand.id,
        brand_slug: brand.slug,
        brand_name: brand.name,
        date: latest?.date ?? null,
        mrr: latest?.mrr ?? null,
        arr: latest?.arr ?? null,
        subscribers: latest?.subscribers ?? null,
        source: latest?.source ?? null,
      };
    })
  );

  return c.json(result);
});

// ---------------------------------------------------------------------------
// GET /history — Revenue time series
// ---------------------------------------------------------------------------
revenueRouter.get("/history", async (c) => {
  const brandSlug = c.req.query("brand");
  const from = c.req.query("from");
  const to = c.req.query("to");

  const conditions: any[] = [];

  if (brandSlug) {
    const [brand] = await db
      .select({ id: brands.id })
      .from(brands)
      .where(eq(brands.slug, brandSlug))
      .limit(1);
    if (brand) {
      conditions.push(eq(revenueSnapshots.brand_id, brand.id));
    } else {
      return c.json([]);
    }
  }

  if (from) {
    conditions.push(gte(revenueSnapshots.date, from));
  }
  if (to) {
    conditions.push(lte(revenueSnapshots.date, to));
  }

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

  const items = await db
    .select({
      date: revenueSnapshots.date,
      brand_slug: brands.slug,
      mrr: revenueSnapshots.mrr,
      arr: revenueSnapshots.arr,
      subscribers: revenueSnapshots.subscribers,
    })
    .from(revenueSnapshots)
    .leftJoin(brands, eq(revenueSnapshots.brand_id, brands.id))
    .where(whereClause)
    .orderBy(asc(revenueSnapshots.date));

  return c.json(items);
});

// ---------------------------------------------------------------------------
// POST / — Log revenue snapshot (auth required, upsert)
// ---------------------------------------------------------------------------
const createRevenueSchema = z.object({
  brand_slug: z.string().min(1),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Date must be YYYY-MM-DD"),
  mrr: z.number().optional(),
  arr: z.number().optional(),
  subscribers: z.number().int().optional(),
  source: z.string().optional(),
  metadata: z.record(z.unknown()).optional(),
});

revenueRouter.post(
  "/",
  authMiddleware,
  zValidator("json", createRevenueSchema),
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

    // Upsert on (brand_id, date)
    await db
      .insert(revenueSnapshots)
      .values({
        brand_id: brand.id,
        date: body.date,
        mrr: body.mrr ?? null,
        arr: body.arr ?? null,
        subscribers: body.subscribers ?? null,
        source: body.source ?? "stripe",
        metadata: body.metadata ? JSON.stringify(body.metadata) : "{}",
      })
      .onConflictDoUpdate({
        target: [revenueSnapshots.brand_id, revenueSnapshots.date],
        set: {
          mrr: sql`excluded.mrr`,
          arr: sql`excluded.arr`,
          subscribers: sql`excluded.subscribers`,
          source: sql`excluded.source`,
          metadata: sql`excluded.metadata`,
        },
      });

    return c.json({ ok: true, brand: body.brand_slug, date: body.date }, 201);
  }
);
