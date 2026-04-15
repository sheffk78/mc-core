import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { eq, and, count, sql } from "drizzle-orm";
import { db } from "../db";
import { brands, tasks, approvals } from "../schema";
import { authMiddleware } from "../middleware/auth";

export const brandsRouter = new Hono();

// ---------------------------------------------------------------------------
// GET / — List all brands with computed counts
// ---------------------------------------------------------------------------
brandsRouter.get("/", async (c) => {
  const allBrands = await db
    .select()
    .from(brands)
    .orderBy(brands.sort_order);

  // Compute task and approval counts per brand
  const result = await Promise.all(
    allBrands.map(async (brand) => {
      const [taskCount] = await db
        .select({ count: count() })
        .from(tasks)
        .where(and(eq(tasks.brand_id, brand.id), sql`${tasks.status} != 'archived'`));

      const [approvalCount] = await db
        .select({ count: count() })
        .from(approvals)
        .where(and(eq(approvals.brand_id, brand.id), eq(approvals.status, "pending")));

      return {
        ...brand,
        task_count: taskCount?.count ?? 0,
        pending_approval_count: approvalCount?.count ?? 0,
      };
    })
  );

  return c.json(result);
});

// ---------------------------------------------------------------------------
// GET /:slug — Single brand by slug
// ---------------------------------------------------------------------------
brandsRouter.get("/:slug", async (c) => {
  const slug = c.req.param("slug");
  const [brand] = await db
    .select()
    .from(brands)
    .where(eq(brands.slug, slug))
    .limit(1);

  if (!brand) {
    return c.json({ error: "Brand not found" }, 404);
  }

  const [taskCount] = await db
    .select({ count: count() })
    .from(tasks)
    .where(and(eq(tasks.brand_id, brand.id), sql`${tasks.status} != 'archived'`));

  const [approvalCount] = await db
    .select({ count: count() })
    .from(approvals)
    .where(and(eq(approvals.brand_id, brand.id), eq(approvals.status, "pending")));

  return c.json({
    ...brand,
    task_count: taskCount?.count ?? 0,
    pending_approval_count: approvalCount?.count ?? 0,
  });
});

// ---------------------------------------------------------------------------
// POST / — Create a brand (auth required)
// ---------------------------------------------------------------------------
const createBrandSchema = z.object({
  name: z.string().min(1),
  slug: z
    .string()
    .min(1)
    .regex(/^[a-z0-9]+$/, "Slug must be lowercase alphanumeric only"),
  color: z.string().optional(),
  sort_order: z.number().int().optional(),
});

brandsRouter.post(
  "/",
  authMiddleware,
  zValidator("json", createBrandSchema),
  async (c) => {
    const body = c.req.valid("json");

    try {
      const [created] = await db
        .insert(brands)
        .values({
          name: body.name,
          slug: body.slug,
          color: body.color ?? "#c85a2a",
          sort_order: body.sort_order ?? 0,
        })
        .returning();

      return c.json(created, 201);
    } catch (err: any) {
      // Unique constraint violation
      if (
        err?.message?.includes("UNIQUE constraint failed") ||
        err?.code === "SQLITE_CONSTRAINT_UNIQUE"
      ) {
        return c.json(
          { error: "A brand with that name or slug already exists" },
          409
        );
      }
      throw err;
    }
  }
);

// ---------------------------------------------------------------------------
// PATCH /:slug — Update a brand (auth required, slug is immutable)
// ---------------------------------------------------------------------------
const updateBrandSchema = z.object({
  name: z.string().min(1).optional(),
  color: z.string().optional(),
  sort_order: z.number().int().optional(),
});

brandsRouter.patch(
  "/:slug",
  authMiddleware,
  zValidator("json", updateBrandSchema),
  async (c) => {
    const slug = c.req.param("slug");
    const body = c.req.valid("json");

    const [existing] = await db
      .select()
      .from(brands)
      .where(eq(brands.slug, slug))
      .limit(1);

    if (!existing) {
      return c.json({ error: "Brand not found" }, 404);
    }

    const [updated] = await db
      .update(brands)
      .set({
        ...body,
        updated_at: sql`datetime('now')`,
      })
      .where(eq(brands.slug, slug))
      .returning();

    return c.json(updated);
  }
);
