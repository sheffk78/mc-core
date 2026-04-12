import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { eq, and, desc, asc, count, sql, ne } from "drizzle-orm";
import { db } from "../db";
import { brands, tasks, taskFiles, activities } from "../schema";
import { authMiddleware } from "../middleware/auth";
import { wsEmit } from "../ws";

export const tasksRouter = new Hono();

// ---------------------------------------------------------------------------
// Status transition map
// ---------------------------------------------------------------------------
const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  open: ["in_progress", "pending_review", "archived"],
  in_progress: ["pending_review", "completed", "archived"],
  pending_review: ["approved", "rejected", "in_progress"],
  approved: ["completed"],
  rejected: ["in_progress", "archived"],
  completed: ["archived"],
  archived: ["open"],
};

// ---------------------------------------------------------------------------
// GET / — List tasks with filtering + pagination
// ---------------------------------------------------------------------------
tasksRouter.get("/", async (c) => {
  const brandSlug = c.req.query("brand");
  const status = c.req.query("status");
  const assignee = c.req.query("assignee");
  const riskTier = c.req.query("risk_tier");
  const limit = Math.min(parseInt(c.req.query("limit") ?? "50", 10), 200);
  const offset = parseInt(c.req.query("offset") ?? "0", 10);

  // Build conditions
  const conditions: any[] = [];

  if (brandSlug) {
    const [brand] = await db
      .select({ id: brands.id })
      .from(brands)
      .where(eq(brands.slug, brandSlug))
      .limit(1);
    if (brand) {
      conditions.push(eq(tasks.brand_id, brand.id));
    } else {
      // Brand not found — return empty
      return c.json({ items: [], total: 0, limit, offset });
    }
  }

  if (status) conditions.push(eq(tasks.status, status as any));
  if (assignee) conditions.push(eq(tasks.assignee, assignee as any));
  if (riskTier) conditions.push(eq(tasks.risk_tier, riskTier as any));

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

  // Get total count
  const [{ total }] = await db
    .select({ total: count() })
    .from(tasks)
    .where(whereClause);

  // Get items with brand slug joined
  const items = await db
    .select({
      ...tasks,
      brand_slug: brands.slug,
      brand_name: brands.name,
      brand_color: brands.color,
    })
    .from(tasks)
    .leftJoin(brands, eq(tasks.brand_id, brands.id))
    .where(whereClause)
    .orderBy(
      // Risk tier priority: red > yellow > green
      sql`CASE ${tasks.risk_tier} WHEN 'red' THEN 0 WHEN 'yellow' THEN 1 ELSE 2 END`,
      desc(tasks.created_at)
    )
    .limit(limit)
    .offset(offset);

  return c.json({ items, total, limit, offset });
});

// ---------------------------------------------------------------------------
// GET /:id — Single task with linked files and approval history
// ---------------------------------------------------------------------------
tasksRouter.get("/:id", async (c) => {
  const id = c.req.param("id");

  const [task] = await db
    .select({
      ...tasks,
      brand_slug: brands.slug,
      brand_name: brands.name,
      brand_color: brands.color,
    })
    .from(tasks)
    .leftJoin(brands, eq(tasks.brand_id, brands.id))
    .where(eq(tasks.id, id))
    .limit(1);

  if (!task) {
    return c.json({ error: "Task not found" }, 404);
  }

  const files = await db
    .select()
    .from(taskFiles)
    .where(eq(taskFiles.task_id, id));

  const approvalHistory = await db.query.approvals.findMany({
    where: eq(sql`approvals.task_id`, id),
    orderBy: desc(sql`approvals.created_at`),
  });

  return c.json({
    ...task,
    linked_files: files,
    approval_history: approvalHistory,
  });
});

// ---------------------------------------------------------------------------
// POST / — Create a task (auth required)
// ---------------------------------------------------------------------------
const createTaskSchema = z.object({
  title: z.string().min(1),
  brand_slug: z.string().min(1),
  description: z.string().optional(),
  priority: z.enum(["low", "normal", "high", "critical"]).optional(),
  risk_tier: z.enum(["green", "yellow", "red"]).optional(),
  assignee: z.enum(["kit", "jeff", "unassigned"]).optional(),
  category: z.string().optional(),
  agent_note: z.string().optional(),
  user_note: z.string().optional(),
  due_date: z.string().optional(),
  estimated_cost: z.number().optional(),
  model_used: z.string().optional(),
  tokens_in: z.number().int().optional(),
  tokens_out: z.number().int().optional(),
  confidence: z.number().optional(),
  linked_files: z
    .array(
      z.object({
        path: z.string(),
        role: z.string(),
        label: z.string().optional(),
      })
    )
    .optional(),
});

tasksRouter.post(
  "/",
  authMiddleware,
  zValidator("json", createTaskSchema),
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

    // Insert task (and linked files in a transaction)
    const [created] = await db.transaction(async (tx) => {
      const [task] = await tx
        .insert(tasks)
        .values({
          brand_id: brand.id,
          title: body.title,
          description: body.description ?? "",
          priority: body.priority ?? "normal",
          risk_tier: body.risk_tier ?? "yellow",
          assignee: body.assignee ?? "kit",
          category: body.category ?? "",
          agent_note: body.agent_note ?? "",
          user_note: body.user_note ?? "",
          due_date: body.due_date ?? null,
          estimated_cost: body.estimated_cost ?? null,
          model_used: body.model_used ?? null,
          tokens_in: body.tokens_in ?? null,
          tokens_out: body.tokens_out ?? null,
          confidence: body.confidence ?? null,
        })
        .returning();

      // Insert linked files if provided
      if (body.linked_files && body.linked_files.length > 0) {
        await tx.insert(taskFiles).values(
          body.linked_files.map((f) => ({
            task_id: task.id,
            file_path: f.path,
            role: f.role as any,
            label: f.label ?? "",
          }))
        );
      }

      return [task];
    });

    // Auto-create activity
    await db.insert(activities).values({
      brand_id: brand.id,
      task_id: created.id,
      actor: "kit",
      action: "task.created",
      summary: `Task created: ${body.title}`,
    });

    // Broadcast WebSocket event
    wsEmit("task.created", created);

    return c.json(created, 201);
  }
);

// ---------------------------------------------------------------------------
// PATCH /:id — Update a task (auth required)
// ---------------------------------------------------------------------------
const updateTaskSchema = z.object({
  title: z.string().min(1).optional(),
  description: z.string().optional(),
  priority: z.enum(["low", "normal", "high", "critical"]).optional(),
  risk_tier: z.enum(["green", "yellow", "red"]).optional(),
  assignee: z.enum(["kit", "jeff", "unassigned"]).optional(),
  category: z.string().optional(),
  agent_note: z.string().optional(),
  user_note: z.string().optional(),
  due_date: z.string().optional().nullable(),
  estimated_cost: z.number().optional().nullable(),
  actual_cost: z.number().optional().nullable(),
  model_used: z.string().optional().nullable(),
  tokens_in: z.number().int().optional().nullable(),
  tokens_out: z.number().int().optional().nullable(),
  confidence: z.number().optional().nullable(),
  append_agent_note: z.string().optional(),
  append_user_note: z.string().optional(),
});

tasksRouter.patch(
  "/:id",
  authMiddleware,
  zValidator("json", updateTaskSchema),
  async (c) => {
    const id = c.req.param("id");
    const body = c.req.valid("json");

    // Check exists
    const [existing] = await db
      .select()
      .from(tasks)
      .where(eq(tasks.id, id))
      .limit(1);

    if (!existing) {
      return c.json({ error: "Task not found" }, 404);
    }

    // Handle additive note fields
    const updates: Record<string, any> = { ...body };
    delete updates.append_agent_note;
    delete updates.append_user_note;

    if (body.append_agent_note) {
      updates.agent_note = existing.agent_note
        ? `${existing.agent_note}\n---\n${body.append_agent_note}`
        : body.append_agent_note;
    }
    if (body.append_user_note) {
      updates.user_note = existing.user_note
        ? `${existing.user_note}\n---\n${body.append_user_note}`
        : body.append_user_note;
    }

    updates.updated_at = sql`datetime('now')`;

    const [updated] = await db
      .update(tasks)
      .set(updates)
      .where(eq(tasks.id, id))
      .returning();

    // Auto-create activity
    await db.insert(activities).values({
      brand_id: existing.brand_id,
      task_id: id,
      actor: "kit",
      action: "task.updated",
      summary: `Task updated: ${updated.title}`,
    });

    // Broadcast
    wsEmit("task.updated", updated);

    return c.json(updated);
  }
);

// ---------------------------------------------------------------------------
// PATCH /:id/status — Status transition with validation (auth required)
// ---------------------------------------------------------------------------
const statusSchema = z.object({
  status: z.enum([
    "open",
    "in_progress",
    "pending_review",
    "approved",
    "rejected",
    "completed",
    "archived",
  ]),
  note: z.string().optional(),
});

tasksRouter.patch(
  "/:id/status",
  authMiddleware,
  zValidator("json", statusSchema),
  async (c) => {
    const id = c.req.param("id");
    const { status: newStatus, note } = c.req.valid("json");

    // Get current task
    const [existing] = await db
      .select()
      .from(tasks)
      .where(eq(tasks.id, id))
      .limit(1);

    if (!existing) {
      return c.json({ error: "Task not found" }, 404);
    }

    // Validate transition
    const allowed = ALLOWED_TRANSITIONS[existing.status] ?? [];
    if (!allowed.includes(newStatus)) {
      return c.json(
        {
          error: `Invalid transition: ${existing.status} → ${newStatus}`,
          allowed_transitions: allowed,
        },
        422
      );
    }

    // Perform transition
    const updates: Record<string, any> = {
      status: newStatus,
      updated_at: sql`datetime('now')`,
    };

    if (newStatus === "completed") {
      updates.completed_at = sql`datetime('now')`;
    }

    const [updated] = await db
      .update(tasks)
      .set(updates)
      .where(eq(tasks.id, id))
      .returning();

    // Auto-create activity
    await db.insert(activities).values({
      brand_id: existing.brand_id,
      task_id: id,
      actor: "kit",
      action: "task.status_changed",
      summary: `Status: ${existing.status} → ${newStatus}`,
      detail: note ?? "",
    });

    // Broadcast
    wsEmit("task.status_changed", {
      id,
      old_status: existing.status,
      new_status: newStatus,
    });

    return c.json(updated);
  }
);

// ---------------------------------------------------------------------------
// DELETE /:id — Delete a task (soft by default, hard with ?hard=true)
// ---------------------------------------------------------------------------
tasksRouter.delete("/:id", authMiddleware, async (c) => {
  const id = c.req.param("id");
  const hard = c.req.query("hard") === "true";

  // Check exists
  const [existing] = await db
    .select()
    .from(tasks)
    .where(eq(tasks.id, id))
    .limit(1);

  if (!existing) {
    return c.json({ error: "Task not found" }, 404);
  }

  if (hard) {
    await db.delete(tasks).where(eq(tasks.id, id));
  } else {
    await db
      .update(tasks)
      .set({
        status: "archived",
        updated_at: sql`datetime('now')`,
      })
      .where(eq(tasks.id, id));
  }

  // Auto-create activity (for soft delete only)
  if (!hard) {
    await db.insert(activities).values({
      brand_id: existing.brand_id,
      task_id: id,
      actor: "kit",
      action: "task.archived",
      summary: `Task archived: ${existing.title}`,
    });
  }

  return c.body(null, 204);
});
