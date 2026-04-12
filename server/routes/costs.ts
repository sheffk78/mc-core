import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { eq, and, desc, sum, count, sql, between, gte, lte } from "drizzle-orm";
import { db } from "../db";
import { brands, dailyCosts } from "../schema";
import { authMiddleware } from "../middleware/auth";
import { wsEmit } from "../ws";

export const costsRouter = new Hono();

// Helper: today's date as YYYY-MM-DD
function todayDate(): string {
  return new Date().toISOString().slice(0, 10);
}

// ---------------------------------------------------------------------------
// GET /today — Today's cost summary (no auth required)
// ---------------------------------------------------------------------------
costsRouter.get("/today", async (c) => {
  const date = todayDate();
  const budgetLimit = parseFloat(process.env.DAILY_BUDGET_USD ?? "2.00");

  // Get today's costs grouped
  const rows = await db
    .select({
      brand_id: dailyCosts.brand_id,
      brand_name: brands.name,
      model: dailyCosts.model,
      tokens_in: dailyCosts.tokens_in,
      tokens_out: dailyCosts.tokens_out,
      cost_usd: dailyCosts.cost_usd,
      task_count: dailyCosts.task_count,
    })
    .from(dailyCosts)
    .leftJoin(brands, eq(dailyCosts.brand_id, brands.id))
    .where(eq(dailyCosts.date, date));

  // Aggregate by brand
  const byBrandMap = new Map<
    string,
    { brand_id: string; brand_name: string; cost_usd: number; task_count: number }
  >();
  // Aggregate by model
  const byModelMap = new Map<
    string,
    { model: string; cost_usd: number; tokens_in: number; tokens_out: number }
  >();

  let totalCost = 0;

  for (const row of rows) {
    totalCost += row.cost_usd;

    const brandKey = row.brand_id ?? "unassigned";
    const existing = byBrandMap.get(brandKey);
    if (existing) {
      existing.cost_usd += row.cost_usd;
      existing.task_count += row.task_count;
    } else {
      byBrandMap.set(brandKey, {
        brand_id: row.brand_id ?? "",
        brand_name: row.brand_name ?? "Unassigned",
        cost_usd: row.cost_usd,
        task_count: row.task_count,
      });
    }

    const modelKey = row.model;
    const existingModel = byModelMap.get(modelKey);
    if (existingModel) {
      existingModel.cost_usd += row.cost_usd;
      existingModel.tokens_in += row.tokens_in;
      existingModel.tokens_out += row.tokens_out;
    } else {
      byModelMap.set(modelKey, {
        model: row.model,
        cost_usd: row.cost_usd,
        tokens_in: row.tokens_in,
        tokens_out: row.tokens_out,
      });
    }
  }

  const budgetRemaining = Math.max(0, budgetLimit - totalCost);
  const budgetPctUsed = budgetLimit > 0 ? (totalCost / budgetLimit) * 100 : 0;

  return c.json({
    date,
    total_cost: Math.round(totalCost * 10000) / 10000,
    budget_limit: budgetLimit,
    budget_remaining: Math.round(budgetRemaining * 10000) / 10000,
    budget_pct_used: Math.round(budgetPctUsed * 100) / 100,
    by_brand: Array.from(byBrandMap.values()).map((b) => ({
      ...b,
      cost_usd: Math.round(b.cost_usd * 10000) / 10000,
    })),
    by_model: Array.from(byModelMap.values()).map((m) => ({
      ...m,
      cost_usd: Math.round(m.cost_usd * 10000) / 10000,
    })),
  });
});

// ---------------------------------------------------------------------------
// GET /range — Aggregated costs over a date range
// ---------------------------------------------------------------------------
costsRouter.get("/range", async (c) => {
  const from = c.req.query("from");
  const to = c.req.query("to");
  const groupBy = c.req.query("group_by") ?? "day";

  if (!from || !to) {
    return c.json({ error: "from and to query params required (YYYY-MM-DD)" }, 400);
  }

  if (!["day", "brand", "model"].includes(groupBy)) {
    return c.json({ error: "group_by must be 'day', 'brand', or 'model'" }, 400);
  }

  // Get raw rows for the date range
  const rows = await db
    .select({
      date: dailyCosts.date,
      brand_id: dailyCosts.brand_id,
      brand_slug: brands.slug,
      brand_name: brands.name,
      model: dailyCosts.model,
      tokens_in: dailyCosts.tokens_in,
      tokens_out: dailyCosts.tokens_out,
      cost_usd: dailyCosts.cost_usd,
      task_count: dailyCosts.task_count,
    })
    .from(dailyCosts)
    .leftJoin(brands, eq(dailyCosts.brand_id, brands.id))
    .where(and(gte(dailyCosts.date, from), lte(dailyCosts.date, to)));

  // Group according to groupBy param
  if (groupBy === "day") {
    const dayMap = new Map<string, { date: string; cost_usd: number; task_count: number }>();
    for (const row of rows) {
      const existing = dayMap.get(row.date);
      if (existing) {
        existing.cost_usd += row.cost_usd;
        existing.task_count += row.task_count;
      } else {
        dayMap.set(row.date, {
          date: row.date,
          cost_usd: row.cost_usd,
          task_count: row.task_count,
        });
      }
    }
    const result = Array.from(dayMap.values())
      .sort((a, b) => a.date.localeCompare(b.date))
      .map((d) => ({
        ...d,
        cost_usd: Math.round(d.cost_usd * 10000) / 10000,
      }));
    return c.json(result);
  }

  if (groupBy === "brand") {
    const brandMap = new Map<
      string,
      { brand_slug: string; brand_name: string; cost_usd: number; task_count: number }
    >();
    for (const row of rows) {
      const key = row.brand_id ?? "unassigned";
      const existing = brandMap.get(key);
      if (existing) {
        existing.cost_usd += row.cost_usd;
        existing.task_count += row.task_count;
      } else {
        brandMap.set(key, {
          brand_slug: row.brand_slug ?? "",
          brand_name: row.brand_name ?? "Unassigned",
          cost_usd: row.cost_usd,
          task_count: row.task_count,
        });
      }
    }
    const result = Array.from(brandMap.values()).map((b) => ({
      ...b,
      cost_usd: Math.round(b.cost_usd * 10000) / 10000,
    }));
    return c.json(result);
  }

  // groupBy === "model"
  const modelMap = new Map<
    string,
    { model: string; cost_usd: number; tokens_in: number; tokens_out: number }
  >();
  for (const row of rows) {
    const existing = modelMap.get(row.model);
    if (existing) {
      existing.cost_usd += row.cost_usd;
      existing.tokens_in += row.tokens_in;
      existing.tokens_out += row.tokens_out;
    } else {
      modelMap.set(row.model, {
        model: row.model,
        cost_usd: row.cost_usd,
        tokens_in: row.tokens_in,
        tokens_out: row.tokens_out,
      });
    }
  }
  const result = Array.from(modelMap.values()).map((m) => ({
    ...m,
    cost_usd: Math.round(m.cost_usd * 10000) / 10000,
  }));
  return c.json(result);
});

// ---------------------------------------------------------------------------
// POST / — Log daily cost (auth required, upsert)
// ---------------------------------------------------------------------------
const logCostSchema = z.object({
  brand_slug: z.string().optional(),
  model: z.string().min(1),
  tokens_in: z.number().int(),
  tokens_out: z.number().int(),
  cost_usd: z.number(),
  task_count: z.number().int().optional(),
});

costsRouter.post(
  "/",
  authMiddleware,
  zValidator("json", logCostSchema),
  async (c) => {
    const body = c.req.valid("json");
    const date = todayDate();

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

    // Upsert: insert or update on conflict (date, brand_id, model)
    await db
      .insert(dailyCosts)
      .values({
        date,
        brand_id: brandId,
        model: body.model,
        tokens_in: body.tokens_in,
        tokens_out: body.tokens_out,
        cost_usd: body.cost_usd,
        task_count: body.task_count ?? 1,
      })
      .onConflictDoUpdate({
        target: [dailyCosts.date, dailyCosts.brand_id, dailyCosts.model],
        set: {
          tokens_in: sql`${dailyCosts.tokens_in} + excluded.tokens_in`,
          tokens_out: sql`${dailyCosts.tokens_out} + excluded.tokens_out`,
          cost_usd: sql`${dailyCosts.cost_usd} + excluded.cost_usd`,
          task_count: sql`${dailyCosts.task_count} + excluded.task_count`,
        },
      });

    // Get total today for broadcast
    const rows = await db
      .select({ cost_usd: dailyCosts.cost_usd })
      .from(dailyCosts)
      .where(eq(dailyCosts.date, date));

    const totalToday = rows.reduce((sum, r) => sum + r.cost_usd, 0);

    wsEmit("cost.updated", { date, total_today: totalToday });

    return c.json({ ok: true, date, total_today: totalToday }, 201);
  }
);

// ---------------------------------------------------------------------------
// POST /budget/check — Budget check (auth required, no side effects)
// ---------------------------------------------------------------------------
costsRouter.post("/budget/check", authMiddleware, async (c) => {
  const date = todayDate();
  const budgetLimit = parseFloat(process.env.DAILY_BUDGET_USD ?? "2.00");
  const threshold = parseFloat(process.env.BUDGET_WARN_THRESHOLD_USD ?? "0.20");

  // Get today's total spend
  const rows = await db
    .select({ cost_usd: dailyCosts.cost_usd })
    .from(dailyCosts)
    .where(eq(dailyCosts.date, date));

  const spent = rows.reduce((sum, r) => sum + r.cost_usd, 0);
  const remaining = Math.max(0, budgetLimit - spent);
  const allowed = remaining >= threshold;

  return c.json({
    allowed,
    spent: Math.round(spent * 10000) / 10000,
    remaining: Math.round(remaining * 10000) / 10000,
    budget_limit: budgetLimit,
    threshold,
  });
});
