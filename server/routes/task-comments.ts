/**
 * Task Comments & Status History Routes
 * 
 * POST /api/v1/tasks/:id/comments — Add a comment
 * GET  /api/v1/tasks/:id/comments — Get comments for a task
 * GET  /api/v1/tasks/:id/history — Get status change history
 * POST /api/v1/tasks/:id/history — Record a status change
 */

import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { eq, desc } from "drizzle-orm";
import { db } from "../db";
import { taskComments, taskStatusHistory, tasks, activities } from "../schema";
import { authMiddleware } from "../middleware/auth";
import { wsEmit } from "../ws";

export const taskCommentsRouter = new Hono();

// ── GET /tasks/:id/comments — Get comments for a task ──

taskCommentsRouter.get("/:id/comments", async (c) => {
  const taskId = c.req.param("id");

  // Verify task exists
  const [task] = await db
    .select({ id: tasks.id })
    .from(tasks)
    .where(eq(tasks.id, taskId))
    .limit(1);

  if (!task) {
    return c.json({ error: "Task not found" }, 404);
  }

  const limit = Math.min(parseInt(c.req.query("limit") ?? "50", 10), 200);
  const offset = parseInt(c.req.query("offset") ?? "0", 10);

  const comments = await db
    .select()
    .from(taskComments)
    .where(eq(taskComments.task_id, taskId))
    .orderBy(desc(taskComments.created_at))
    .limit(limit)
    .offset(offset);

  return c.json({ comments, count: comments.length });
});

// ── POST /tasks/:id/comments — Add a comment to a task ──

const createCommentSchema = z.object({
  author: z.enum(["kit", "jeff"]).default("kit"),
  content: z.string().min(1).max(5000),
});

taskCommentsRouter.post(
  "/:id/comments",
  authMiddleware,
  zValidator("json", createCommentSchema),
  async (c) => {
    const taskId = c.req.param("id");
    const body = c.req.valid("json");

    // Verify task exists
    const [task] = await db
      .select({ id: tasks.id, brand_id: tasks.brand_id, title: tasks.title })
      .from(tasks)
      .where(eq(tasks.id, taskId))
      .limit(1);

    if (!task) {
      return c.json({ error: "Task not found" }, 404);
    }

    const [comment] = await db
      .insert(taskComments)
      .values({
        task_id: taskId,
        author: body.author,
        content: body.content,
      })
      .returning();

    // Auto-create activity
    await db.insert(activities).values({
      brand_id: task.brand_id,
      task_id: taskId,
      actor: body.author,
      action: "task.comment_added",
      summary: `Comment added by ${body.author} on: ${task.title}`,
    });

    // Broadcast
    wsEmit("task.comment_added", { task_id: taskId, comment });

    return c.json(comment, 201);
  }
);

// ── GET /tasks/:id/history — Get status change history ──

taskCommentsRouter.get("/:id/history", async (c) => {
  const taskId = c.req.param("id");

  // Verify task exists
  const [task] = await db
    .select({ id: tasks.id })
    .from(tasks)
    .where(eq(tasks.id, taskId))
    .limit(1);

  if (!task) {
    return c.json({ error: "Task not found" }, 404);
  }

  const history = await db
    .select()
    .from(taskStatusHistory)
    .where(eq(taskStatusHistory.task_id, taskId))
    .orderBy(desc(taskStatusHistory.created_at));

  return c.json({ history, count: history.length });
});

// ── POST /tasks/:id/history — Record a manual status change entry ──

const createHistorySchema = z.object({
  from_status: z.string(),
  to_status: z.string(),
  changed_by: z.enum(["kit", "jeff", "system"]).default("kit"),
  note: z.string().default(""),
});

taskCommentsRouter.post(
  "/:id/history",
  authMiddleware,
  zValidator("json", createHistorySchema),
  async (c) => {
    const taskId = c.req.param("id");
    const body = c.req.valid("json");

    // Verify task exists
    const [task] = await db
      .select({ id: tasks.id })
      .from(tasks)
      .where(eq(tasks.id, taskId))
      .limit(1);

    if (!task) {
      return c.json({ error: "Task not found" }, 404);
    }

    const [entry] = await db
      .insert(taskStatusHistory)
      .values({
        task_id: taskId,
        from_status: body.from_status,
        to_status: body.to_status,
        changed_by: body.changed_by,
        note: body.note,
      })
      .returning();

    return c.json(entry, 201);
  }
);