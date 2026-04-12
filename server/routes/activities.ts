import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { eq, and, desc, count, sql, gte } from "drizzle-orm";
import { db } from "../db";
import { brands, activities } from "../schema";
import { authMiddleware } from "../middleware/auth";
import { wsEmit } from "../ws";

export const activitiesRouter = new Hono();

// ---------------------------------------------------------------------------
// GET / — List activities with filtering
// ---------------------------------------------------------------------------
activitiesRouter.get("/", async (c) => {
  const brandSlug = c.req.query("brand");
  const actor = c.req.query("actor");
  const since = c.req.query("since");
  const limit = Math.min(parseInt(c.req.query("limit") ?? "50", 10), 200);
  const offset = parseInt(c.req.query("offset") ?? "0", 10);

  const conditions: any[] = [];

  if (brandSlug) {
    const [brand] = await db
      .select({ id: brands.id })
      .from(brands)
      .where(eq(brands.slug, brandSlug))
      .limit(1);
    if (brand) {
      conditions.push(eq(activities.brand_id, brand.id));
    } else {
      return c.json({ items: [], total: 0 });
    }
  }

  if (actor) {
    conditions.push(eq(activities.actor, actor as any));
  }

  if (since) {
    conditions.push(gte(activities.created_at, since));
  }

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

  // Get total count
  const [{ total }] = await db
    .select({ total: count() })
    .from(activities)
    .where(whereClause);

  // Get items ordered by created_at DESC
  const items = await db
    .select({
      ...activities,
      brand_slug: brands.slug,
      brand_name: brands.name,
      brand_color: brands.color,
    })
    .from(activities)
    .leftJoin(brands, eq(activities.brand_id, brands.id))
    .where(whereClause)
    .orderBy(desc(activities.created_at))
    .limit(limit)
    .offset(offset);

  return c.json({ items, total });
});

// ---------------------------------------------------------------------------
// POST / — Create an activity (auth required)
// ---------------------------------------------------------------------------
const createActivitySchema = z.object({
  brand_slug: z.string().optional(),
  task_id: z.string().optional(),
  actor: z.enum(["kit", "jeff", "system", "cron"]).optional(),
  action: z.string().min(1),
  summary: z.string().min(1),
  detail: z.string().optional(),
  model_used: z.string().optional(),
  tokens_used: z.number().int().optional(),
  cost_usd: z.number().optional(),
});

activitiesRouter.post(
  "/",
  authMiddleware,
  zValidator("json", createActivitySchema),
  async (c) => {
    const body = c.req.valid("json");

    // Resolve brand_id from slug if provided
    let brandId: string | null = null;
    if (body.brand_slug) {
      const [brand] = await db
        .select({ id: brands.id })
        .from(brands)
        .where(eq(brands.slug, body.brand_slug))
        .limit(1);
      brandId = brand?.id ?? null;
    }

    const [created] = await db
      .insert(activities)
      .values({
        brand_id: brandId,
        task_id: body.task_id ?? null,
        actor: body.actor ?? "kit",
        action: body.action,
        summary: body.summary,
        detail: body.detail ?? "",
        model_used: body.model_used ?? null,
        tokens_used: body.tokens_used ?? null,
        cost_usd: body.cost_usd ?? null,
      })
      .returning();

    // Broadcast
    wsEmit("activity.new", created);

    return c.json(created, 201);
  }
);
