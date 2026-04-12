import { Hono } from "hono";
import { eq, and, sql, count, desc, asc } from "drizzle-orm";
import { db } from "../db";
import {
  brands,
  tasks,
  approvals,
  activities,
  cronJobs,
  taskFiles,
  dailyCosts,
} from "../schema";
import { authMiddleware } from "../middleware/auth";

export const statsRouter = new Hono();

// Helper: today's date as YYYY-MM-DD
function todayDate(): string {
  return new Date().toISOString().slice(0, 10);
}

// ---------------------------------------------------------------------------
// GET / — Dashboard summary (no auth required)
// ---------------------------------------------------------------------------
statsRouter.get("/", async (c) => {
  const date = todayDate();
  const budgetLimit = parseFloat(process.env.DAILY_BUDGET_USD ?? "2.00");

  // Run all queries in parallel
  const [
    pendingApprovalsResult,
    openTasksResult,
    pendingReviewResult,
    todayCostsResult,
    activeCronResult,
    connectedFilesResult,
    brandsActiveResult,
  ] = await Promise.all([
    // Pending approvals count
    db
      .select({ count: count() })
      .from(approvals)
      .where(eq(approvals.status, "pending")),

    // Open tasks count (open + in_progress)
    db
      .select({ count: count() })
      .from(tasks)
      .where(
        sql`${tasks.status} IN ('open', 'in_progress')`
      ),

    // Pending review tasks count
    db
      .select({ count: count() })
      .from(tasks)
      .where(eq(tasks.status, "pending_review")),

    // Today's total cost
    db
      .select({ cost_usd: dailyCosts.cost_usd })
      .from(dailyCosts)
      .where(eq(dailyCosts.date, date)),

    // Active cron jobs count
    db
      .select({ count: count() })
      .from(cronJobs)
      .where(eq(cronJobs.enabled, 1)),

    // Total connected files
    db.select({ count: count() }).from(taskFiles),

    // Brands with at least 1 non-archived task
    db
      .select({ count: count() })
      .from(brands)
      .where(
        sql`EXISTS (SELECT 1 FROM tasks WHERE tasks.brand_id = brands.id AND tasks.status != 'archived')`
      ),
  ]);

  const todayCostUsd = todayCostsResult.reduce((sum, r) => sum + r.cost_usd, 0);
  const budgetPctUsed =
    budgetLimit > 0 ? (todayCostUsd / budgetLimit) * 100 : 0;

  return c.json({
    pending_approvals: pendingApprovalsResult[0]?.count ?? 0,
    open_tasks: openTasksResult[0]?.count ?? 0,
    pending_review_tasks: pendingReviewResult[0]?.count ?? 0,
    today_cost_usd: Math.round(todayCostUsd * 10000) / 10000,
    today_budget_limit: budgetLimit,
    today_budget_pct_used: Math.round(budgetPctUsed * 100) / 100,
    active_cron_jobs: activeCronResult[0]?.count ?? 0,
    connected_files: connectedFilesResult[0]?.count ?? 0,
    brands_active: brandsActiveResult[0]?.count ?? 0,
  });
});

// ---------------------------------------------------------------------------
// GET /jeff-queue — Jeff's decision queue (auth required)
// ---------------------------------------------------------------------------
statsRouter.get("/jeff-queue", authMiddleware, async (c) => {
  // Get pending approvals
  const pendingApprovals = await db
    .select({
      id: approvals.id,
      risk_tier: approvals.risk_tier,
      title: approvals.title,
      created_at: approvals.created_at,
      brand_slug: brands.slug,
      brand_color: brands.color,
      agent_reasoning: approvals.agent_reasoning,
    })
    .from(approvals)
    .leftJoin(brands, eq(approvals.brand_id, brands.id))
    .where(eq(approvals.status, "pending"));

  // Get pending review tasks
  const pendingReviewTasks = await db
    .select({
      id: tasks.id,
      risk_tier: tasks.risk_tier,
      title: tasks.title,
      created_at: tasks.created_at,
      category: tasks.category,
      assignee: tasks.assignee,
      agent_note: tasks.agent_note,
      brand_slug: brands.slug,
      brand_color: brands.color,
    })
    .from(tasks)
    .leftJoin(brands, eq(tasks.brand_id, brands.id))
    .where(eq(tasks.status, "pending_review"));

  // Map to QueueItem shape
  const approvalItems = pendingApprovals.map((a) => ({
    id: a.id,
    type: "approval" as const,
    risk_tier: a.risk_tier,
    title: a.title,
    brand_slug: a.brand_slug,
    brand_color: a.brand_color,
    created_at: a.created_at,
    category: undefined,
    assignee: undefined,
    agent_note_preview: (a.agent_reasoning ?? "").slice(0, 200),
  }));

  const taskItems = pendingReviewTasks.map((t) => ({
    id: t.id,
    type: "task" as const,
    risk_tier: t.risk_tier,
    title: t.title,
    brand_slug: t.brand_slug,
    brand_color: t.brand_color,
    created_at: t.created_at,
    category: t.category ?? undefined,
    assignee: t.assignee,
    agent_note_preview: (t.agent_note ?? "").slice(0, 200),
  }));

  // Combine and sort: risk_tier (red > yellow > green), then created_at ASC
  const allItems = [...approvalItems, ...taskItems].sort((a, b) => {
    const tierOrder: Record<string, number> = { red: 0, yellow: 1, green: 2 };
    const tierDiff =
      (tierOrder[a.risk_tier] ?? 3) - (tierOrder[b.risk_tier] ?? 3);
    if (tierDiff !== 0) return tierDiff;
    return (a.created_at ?? "").localeCompare(b.created_at ?? "");
  });

  // Count by tier
  const counts = { red: 0, yellow: 0, green: 0 };
  for (const item of allItems) {
    if (item.risk_tier in counts) {
      counts[item.risk_tier as keyof typeof counts]++;
    }
  }

  return c.json({
    items: allItems,
    counts,
    total: allItems.length,
  });
});
