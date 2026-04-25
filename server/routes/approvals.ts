import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { eq, and, desc, asc, count, sql } from "drizzle-orm";
import { db } from "../db";
import { brands, approvals, tasks, activities } from "../schema";
import { authMiddleware } from "../middleware/auth";
import { wsEmit } from "../ws";

export const approvalsRouter = new Hono();

// ---------------------------------------------------------------------------
// GET / — List approvals with filtering + pagination
// ---------------------------------------------------------------------------
approvalsRouter.get("/", async (c) => {
  const status = c.req.query("status") ?? "pending";
  const brandSlug = c.req.query("brand");
  const riskTier = c.req.query("risk_tier");
  const type = c.req.query("type");
  const limit = Math.min(parseInt(c.req.query("limit") ?? "50", 10), 200);
  const offset = parseInt(c.req.query("offset") ?? "0", 10);

  const conditions: any[] = [];

  if (status && status !== "all") {
    conditions.push(eq(approvals.status, status as any));
  }
  if (brandSlug) {
    const [brand] = await db
      .select({ id: brands.id })
      .from(brands)
      .where(eq(brands.slug, brandSlug))
      .limit(1);
    if (brand) {
      conditions.push(eq(approvals.brand_id, brand.id));
    } else {
      return c.json({ items: [], total: 0, limit, offset });
    }
  }
  if (riskTier) conditions.push(eq(approvals.risk_tier, riskTier as any));
  if (type) conditions.push(eq(approvals.type, type as any));

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

  const [{ total }] = await db
    .select({ total: count() })
    .from(approvals)
    .where(whereClause);

  const items = await db
    .select({
      ...approvals,
      brand_slug: brands.slug,
      brand_name: brands.name,
      brand_color: brands.color,
    })
    .from(approvals)
    .leftJoin(brands, eq(approvals.brand_id, brands.id))
    .where(whereClause)
    .orderBy(
      // Risk tier priority: red > yellow > green
      sql`CASE ${approvals.risk_tier} WHEN 'red' THEN 0 WHEN 'yellow' THEN 1 ELSE 2 END`,
      asc(approvals.created_at)
    )
    .limit(limit)
    .offset(offset);

  return c.json({ items, total, limit, offset });
});

// ---------------------------------------------------------------------------
// GET /:id — Single approval with linked task
// ---------------------------------------------------------------------------
approvalsRouter.get("/:id", async (c) => {
  const id = c.req.param("id");

  const [approval] = await db
    .select({
      ...approvals,
      brand_slug: brands.slug,
      brand_name: brands.name,
      brand_color: brands.color,
    })
    .from(approvals)
    .leftJoin(brands, eq(approvals.brand_id, brands.id))
    .where(eq(approvals.id, id))
    .limit(1);

  if (!approval) {
    return c.json({ error: "Approval not found" }, 404);
  }

  // Include linked task if task_id is set
  let linkedTask = null;
  if (approval.task_id) {
    const [task] = await db
      .select({
        id: tasks.id,
        title: tasks.title,
        status: tasks.status,
        brand_slug: brands.slug,
      })
      .from(tasks)
      .leftJoin(brands, eq(tasks.brand_id, brands.id))
      .where(eq(tasks.id, approval.task_id))
      .limit(1);
    linkedTask = task ?? null;
  }

  return c.json({ ...approval, linked_task: linkedTask });
});

// ---------------------------------------------------------------------------
// POST / — Create an approval (auth required)
// ---------------------------------------------------------------------------
const createApprovalSchema = z.object({
  brand_slug: z.string().min(1),
  task_id: z.string().optional(),
  type: z.enum(["content", "email", "social", "spend", "code", "decision"]),
  title: z.string().min(1),
  preview: z.string().optional(),
  agent_reasoning: z.string().optional(),
  risk_tier: z.enum(["green", "yellow", "red"]).optional(),
  metadata: z.record(z.unknown()).optional(),
});

approvalsRouter.post(
  "/",
  authMiddleware,
  zValidator("json", createApprovalSchema),
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

    // Force risk_tier to 'red' for public-facing types
    const forcedRiskTier = ["email", "social", "spend"].includes(body.type)
      ? "red"
      : (body.risk_tier ?? "yellow");

    const [created] = await db
      .insert(approvals)
      .values({
        brand_id: brand.id,
        task_id: body.task_id ?? null,
        type: body.type,
        title: body.title,
        preview: body.preview ?? "",
        agent_reasoning: body.agent_reasoning ?? "",
        risk_tier: forcedRiskTier,
        status: "pending",
        metadata: body.metadata ? JSON.stringify(body.metadata) : "{}",
      })
      .returning();

    // Auto-create activity
    await db.insert(activities).values({
      brand_id: brand.id,
      task_id: body.task_id ?? null,
      actor: "kit",
      action: "approval.created",
      summary: `Approval requested: ${body.title}`,
    });

    // Broadcast
    wsEmit("approval.created", created);

    return c.json(created, 201);
  }
);

// ---------------------------------------------------------------------------
// POST /:id/approve — Approve an item
// ---------------------------------------------------------------------------
const approveSchema = z.object({
  note: z.string().optional(),
});

approvalsRouter.post(
  "/:id/approve",
  authMiddleware,
  zValidator("json", approveSchema),
  async (c) => {
    const id = c.req.param("id");
    const body = c.req.valid("json");

    const [existing] = await db
      .select()
      .from(approvals)
      .where(eq(approvals.id, id))
      .limit(1);

    if (!existing) {
      return c.json({ error: "Approval not found" }, 404);
    }

    const [updated] = await db
      .update(approvals)
      .set({
        status: "approved",
        decided_at: sql`datetime('now')`,
        decided_by: "jeff",
        feedback: body.note ?? existing.feedback,
      })
      .where(eq(approvals.id, id))
      .returning();

    // Update linked task if it's pending_review
    if (existing.task_id) {
      const [linkedTask] = await db
        .select({ status: tasks.status })
        .from(tasks)
        .where(eq(tasks.id, existing.task_id))
        .limit(1);

      if (linkedTask?.status === "pending_review") {
        await db
          .update(tasks)
          .set({
            status: "approved",
            updated_at: sql`datetime('now')`,
          })
          .where(eq(tasks.id, existing.task_id));
      }
    }

    // Auto-create activity
    await db.insert(activities).values({
      brand_id: existing.brand_id,
      task_id: existing.task_id,
      actor: "jeff",
      action: "approval.approved",
      summary: `Approved: ${existing.title}`,
    });

    wsEmit("approval.approved", { id, title: existing.title });

    return c.json(updated);
  }
);

// ---------------------------------------------------------------------------
// POST /:id/reject — Reject with required feedback
// ---------------------------------------------------------------------------
const rejectSchema = z.object({
  feedback: z.string().min(1, "Feedback is required when rejecting"),
});

approvalsRouter.post(
  "/:id/reject",
  authMiddleware,
  zValidator("json", rejectSchema),
  async (c) => {
    const id = c.req.param("id");
    const body = c.req.valid("json");

    const [existing] = await db
      .select()
      .from(approvals)
      .where(eq(approvals.id, id))
      .limit(1);

    if (!existing) {
      return c.json({ error: "Approval not found" }, 404);
    }

    const [updated] = await db
      .update(approvals)
      .set({
        status: "rejected",
        feedback: body.feedback,
        decided_at: sql`datetime('now')`,
        decided_by: "jeff",
      })
      .where(eq(approvals.id, id))
      .returning();

    // Update linked task status to 'rejected'
    if (existing.task_id) {
      await db
        .update(tasks)
        .set({
          status: "rejected",
          updated_at: sql`datetime('now')`,
        })
        .where(eq(tasks.id, existing.task_id));
    }

    // Auto-create activity
    await db.insert(activities).values({
      brand_id: existing.brand_id,
      task_id: existing.task_id,
      actor: "jeff",
      action: "approval.rejected",
      summary: `Rejected: ${existing.title}`,
      detail: body.feedback,
    });

    wsEmit("approval.rejected", {
      id,
      title: existing.title,
      feedback: body.feedback,
    });

    return c.json(updated);
  }
);

// ---------------------------------------------------------------------------
// POST /:id/edit-approve — Edit and approve in one step
// ---------------------------------------------------------------------------
const editApproveSchema = z.object({
  edits: z.string().min(1),
  note: z.string().optional(),
});

approvalsRouter.post(
  "/:id/edit-approve",
  authMiddleware,
  zValidator("json", editApproveSchema),
  async (c) => {
    const id = c.req.param("id");
    const body = c.req.valid("json");

    const [existing] = await db
      .select()
      .from(approvals)
      .where(eq(approvals.id, id))
      .limit(1);

    if (!existing) {
      return c.json({ error: "Approval not found" }, 404);
    }

    const [updated] = await db
      .update(approvals)
      .set({
        preview: body.edits,
        status: "approved",
        decided_at: sql`datetime('now')`,
        decided_by: "jeff",
        feedback: body.note ?? existing.feedback,
      })
      .where(eq(approvals.id, id))
      .returning();

    // Auto-create activity
    await db.insert(activities).values({
      brand_id: existing.brand_id,
      task_id: existing.task_id,
      actor: "jeff",
      action: "approval.edit_approved",
      summary: `Edit-approved: ${existing.title}`,
    });

    wsEmit("approval.approved", { id, title: existing.title });

    return c.json(updated);
  }
);

// ---------------------------------------------------------------------------
// PATCH /:id — Update an approval (status transition)
// ---------------------------------------------------------------------------
const updateApprovalSchema = z.object({
  status: z.enum(["approved", "rejected", "expired"]).optional(),
  feedback: z.string().optional(),
  preview: z.string().optional(),
  jeff_comment: z.string().optional(),
});

approvalsRouter.patch(
  "/:id",
  authMiddleware,
  zValidator("json", updateApprovalSchema),
  async (c) => {
    const id = c.req.param("id");
    const body = c.req.valid("json");

    const [existing] = await db
      .select()
      .from(approvals)
      .where(eq(approvals.id, id))
      .limit(1);

    if (!existing) {
      return c.json({ error: "Approval not found" }, 404);
    }

    // Build update object
    const updates: Record<string, any> = {};

    if (body.status) {
      updates.status = body.status;
      updates.decided_at = sql`datetime('now')`;
      updates.decided_by = "jeff";

      // If approving/rejecting, also update linked task status
      if (existing.task_id) {
        if (body.status === "approved") {
          const [linkedTask] = await db
            .select({ status: tasks.status })
            .from(tasks)
            .where(eq(tasks.id, existing.task_id))
            .limit(1);

          if (linkedTask?.status === "pending_review") {
            await db
              .update(tasks)
              .set({
                status: "approved",
                updated_at: sql`datetime('now')`,
              })
              .where(eq(tasks.id, existing.task_id));
          }
        } else if (body.status === "rejected") {
          if (existing.task_id) {
            await db
              .update(tasks)
              .set({
                status: "rejected",
                updated_at: sql`datetime('now')`,
              })
              .where(eq(tasks.id, existing.task_id));
          }
        }
      }
    }

    if (body.feedback !== undefined) updates.feedback = body.feedback;
    if (body.preview !== undefined) updates.preview = body.preview;

    const [updated] = await db
      .update(approvals)
      .set(updates)
      .where(eq(approvals.id, id))
      .returning();

    // Log activity if status changed
    if (body.status) {
      await db.insert(activities).values({
        brand_id: existing.brand_id,
        task_id: existing.task_id,
        actor: "jeff",
        action: `approval.${body.status}`,
        summary: `${body.status === 'approved' ? 'Approved' : body.status === 'rejected' ? 'Rejected' : 'Expired'}: ${existing.title}`,
        detail: body.feedback ?? "",
      });

      wsEmit(`approval.${body.status}`, {
        id,
        title: existing.title,
      });
    }

    return c.json(updated);
  }
);

// ---------------------------------------------------------------------------
// POST /bulk — Bulk approve or dismiss
// ---------------------------------------------------------------------------
const bulkSchema = z.object({
  ids: z.array(z.string()).min(1),
  action: z.enum(["approve", "dismiss"]),
});

approvalsRouter.post(
  "/bulk",
  authMiddleware,
  zValidator("json", bulkSchema),
  async (c) => {
    const body = c.req.valid("json");
    const newStatus = body.action === "approve" ? "approved" : "expired";

    const updated = await db.transaction(async (tx) => {
      let count = 0;
      for (const id of body.ids) {
        const result = await tx
          .update(approvals)
          .set({
            status: newStatus,
            decided_at: sql`datetime('now')`,
            decided_by: "jeff",
          })
          .where(eq(approvals.id, id));
        count += result.changes ?? 0;
      }
      return count;
    });

    return c.json({ updated });
  }
);
