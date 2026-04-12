import {
  sqliteTable,
  text,
  integer,
  real,
  index,
  uniqueIndex,
} from "drizzle-orm/sqlite-core";
import { sql, relations } from "drizzle-orm";
import type { InferInsertModel, InferSelectModel } from "drizzle-orm";

// ---------------------------------------------------------------------------
// 1. brands
// ---------------------------------------------------------------------------
export const brands = sqliteTable(
  "brands",
  {
    id: text("id")
      .primaryKey()
      .default(sql`lower(hex(randomblob(8)))`),
    name: text("name").notNull().unique(),
    slug: text("slug").notNull().unique(),
    color: text("color").notNull().default("#c85a2a"),
    sort_order: integer("sort_order").notNull().default(0),
    created_at: text("created_at")
      .notNull()
      .default(sql`datetime('now')`),
    updated_at: text("updated_at")
      .notNull()
      .default(sql`datetime('now')`),
  },
  (t) => [index("idx_brands_slug").on(t.slug)]
);

// ---------------------------------------------------------------------------
// 2. tasks
// ---------------------------------------------------------------------------
export const tasks = sqliteTable(
  "tasks",
  {
    id: text("id")
      .primaryKey()
      .default(sql`lower(hex(randomblob(8)))`),
    brand_id: text("brand_id")
      .notNull()
      .references(() => brands.id),
    title: text("title").notNull(),
    description: text("description").default(""),
    status: text("status", {
      enum: [
        "open",
        "in_progress",
        "pending_review",
        "approved",
        "rejected",
        "completed",
        "archived",
      ],
    })
      .notNull()
      .default("open"),
    priority: text("priority", {
      enum: ["low", "normal", "high", "critical"],
    })
      .notNull()
      .default("normal"),
    risk_tier: text("risk_tier", {
      enum: ["green", "yellow", "red"],
    })
      .notNull()
      .default("yellow"),
    assignee: text("assignee", {
      enum: ["kit", "jeff", "unassigned"],
    })
      .notNull()
      .default("kit"),
    category: text("category").default(""),
    agent_note: text("agent_note").default(""),
    user_note: text("user_note").default(""),
    due_date: text("due_date"),
    completed_at: text("completed_at"),
    estimated_cost: real("estimated_cost"),
    actual_cost: real("actual_cost"),
    model_used: text("model_used"),
    tokens_in: integer("tokens_in"),
    tokens_out: integer("tokens_out"),
    confidence: real("confidence"),
    created_at: text("created_at")
      .notNull()
      .default(sql`datetime('now')`),
    updated_at: text("updated_at")
      .notNull()
      .default(sql`datetime('now')`),
  },
  (t) => [
    index("idx_tasks_brand").on(t.brand_id),
    index("idx_tasks_status").on(t.status),
    index("idx_tasks_assignee").on(t.assignee),
    index("idx_tasks_risk").on(t.risk_tier),
    index("idx_tasks_due").on(t.due_date),
  ]
);

// ---------------------------------------------------------------------------
// 3. task_files
// ---------------------------------------------------------------------------
export const taskFiles = sqliteTable(
  "task_files",
  {
    id: text("id")
      .primaryKey()
      .default(sql`lower(hex(randomblob(8)))`),
    task_id: text("task_id")
      .notNull()
      .references(() => tasks.id, { onDelete: "cascade" }),
    file_path: text("file_path").notNull(),
    role: text("role", {
      enum: ["skill", "output", "context", "input", "reference"],
    })
      .notNull()
      .default("context"),
    label: text("label").default(""),
    created_at: text("created_at")
      .notNull()
      .default(sql`datetime('now')`),
  },
  (t) => [
    index("idx_task_files_task").on(t.task_id),
    index("idx_task_files_path").on(t.file_path),
  ]
);

// ---------------------------------------------------------------------------
// 4. approvals
// ---------------------------------------------------------------------------
export const approvals = sqliteTable(
  "approvals",
  {
    id: text("id")
      .primaryKey()
      .default(sql`lower(hex(randomblob(8)))`),
    brand_id: text("brand_id")
      .notNull()
      .references(() => brands.id),
    task_id: text("task_id").references(() => tasks.id),
    type: text("type", {
      enum: ["content", "email", "social", "spend", "code", "decision"],
    })
      .notNull()
      .default("content"),
    title: text("title").notNull(),
    preview: text("preview").default(""),
    agent_reasoning: text("agent_reasoning").default(""),
    risk_tier: text("risk_tier", {
      enum: ["green", "yellow", "red"],
    })
      .notNull()
      .default("yellow"),
    status: text("status", {
      enum: ["pending", "approved", "rejected", "expired", "auto_approved"],
    })
      .notNull()
      .default("pending"),
    feedback: text("feedback").default(""),
    metadata: text("metadata").default("{}"),
    created_at: text("created_at")
      .notNull()
      .default(sql`datetime('now')`),
    decided_at: text("decided_at"),
    decided_by: text("decided_by"),
  },
  (t) => [
    index("idx_approvals_status").on(t.status),
    index("idx_approvals_brand").on(t.brand_id),
    index("idx_approvals_risk").on(t.risk_tier),
  ]
);

// ---------------------------------------------------------------------------
// 5. activities
// ---------------------------------------------------------------------------
export const activities = sqliteTable(
  "activities",
  {
    id: text("id")
      .primaryKey()
      .default(sql`lower(hex(randomblob(8)))`),
    brand_id: text("brand_id").references(() => brands.id),
    task_id: text("task_id").references(() => tasks.id),
    actor: text("actor", {
      enum: ["kit", "jeff", "system", "cron"],
    })
      .notNull()
      .default("kit"),
    action: text("action").notNull(),
    summary: text("summary").notNull(),
    detail: text("detail").default(""),
    model_used: text("model_used"),
    tokens_used: integer("tokens_used"),
    cost_usd: real("cost_usd"),
    created_at: text("created_at")
      .notNull()
      .default(sql`datetime('now')`),
  },
  (t) => [
    index("idx_activities_brand").on(t.brand_id),
    index("idx_activities_created").on(t.created_at),
    index("idx_activities_actor").on(t.actor),
    index("idx_activities_brand_created").on(t.brand_id, t.created_at),
  ]
);

// ---------------------------------------------------------------------------
// 6. cron_jobs
// ---------------------------------------------------------------------------
export const cronJobs = sqliteTable("cron_jobs", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  brand_id: text("brand_id").references(() => brands.id),
  schedule_expr: text("schedule_expr").notNull(),
  schedule_ms: integer("schedule_ms"),
  cron_expr: text("cron_expr"),
  enabled: integer("enabled").notNull().default(1),
  last_run_at: text("last_run_at"),
  last_status: text("last_status", {
    enum: ["success", "error", "running", "unknown"],
  }).default("unknown"),
  last_duration_ms: integer("last_duration_ms"),
  last_error: text("last_error"),
  consecutive_errors: integer("consecutive_errors").default(0),
  created_at: text("created_at")
    .notNull()
    .default(sql`datetime('now')`),
  updated_at: text("updated_at")
    .notNull()
    .default(sql`datetime('now')`),
});

// ---------------------------------------------------------------------------
// 7. daily_costs
// ---------------------------------------------------------------------------
export const dailyCosts = sqliteTable(
  "daily_costs",
  {
    id: text("id")
      .primaryKey()
      .default(sql`lower(hex(randomblob(8)))`),
    date: text("date").notNull(),
    brand_id: text("brand_id").references(() => brands.id),
    model: text("model").notNull(),
    tokens_in: integer("tokens_in").notNull().default(0),
    tokens_out: integer("tokens_out").notNull().default(0),
    cost_usd: real("cost_usd").notNull().default(0.0),
    task_count: integer("task_count").notNull().default(0),
  },
  (t) => [
    uniqueIndex("idx_daily_costs_unique").on(t.date, t.brand_id, t.model),
    index("idx_daily_costs_date").on(t.date),
  ]
);

// ---------------------------------------------------------------------------
// 8. revenue_snapshots
// ---------------------------------------------------------------------------
export const revenueSnapshots = sqliteTable(
  "revenue_snapshots",
  {
    id: text("id")
      .primaryKey()
      .default(sql`lower(hex(randomblob(8)))`),
    brand_id: text("brand_id")
      .notNull()
      .references(() => brands.id),
    date: text("date").notNull(),
    mrr: real("mrr"),
    arr: real("arr"),
    subscribers: integer("subscribers"),
    source: text("source").default("stripe"),
    metadata: text("metadata").default("{}"),
    created_at: text("created_at")
      .notNull()
      .default(sql`datetime('now')`),
  },
  (t) => [
    uniqueIndex("idx_revenue_brand_date").on(t.brand_id, t.date),
    index("idx_revenue_date").on(t.date),
  ]
);

// ---------------------------------------------------------------------------
// 9. notifications
// ---------------------------------------------------------------------------
export const notifications = sqliteTable("notifications", {
  id: text("id")
    .primaryKey()
    .default(sql`lower(hex(randomblob(8)))`),
  channel: text("channel", {
    enum: ["slack", "email", "dashboard"],
  }).notNull(),
  recipient: text("recipient").notNull(),
  title: text("title").notNull(),
  body: text("body").default(""),
  related_id: text("related_id"),
  sent_at: text("sent_at")
    .notNull()
    .default(sql`datetime('now')`),
  status: text("status", {
    enum: ["sent", "failed", "read"],
  })
    .notNull()
    .default("sent"),
});

// ---------------------------------------------------------------------------
// 10. webauthn_credentials
// ---------------------------------------------------------------------------
export const webauthnCredentials = sqliteTable(
  "webauthn_credentials",
  {
    id: text("id").primaryKey(),
    user_id: text("user_id").notNull(),
    credential_id: text("credential_id").notNull().unique(),
    public_key: text("public_key").notNull(),
    counter: integer("counter").notNull().default(0),
    device_type: text("device_type"),
    backed_up: integer("backed_up").default(0),
    transports: text("transports").default("[]"),
    created_at: text("created_at")
      .notNull()
      .default(sql`datetime('now')`),
    last_used_at: text("last_used_at"),
  },
  (t) => [
    index("idx_webauthn_user").on(t.user_id),
    uniqueIndex("idx_webauthn_credential").on(t.credential_id),
  ]
);

// ---------------------------------------------------------------------------
// Relations (for Drizzle relational queries)
// ---------------------------------------------------------------------------
export const brandsRelations = relations(brands, ({ many }) => ({
  tasks: many(tasks),
  approvals: many(approvals),
  activities: many(activities),
  cronJobs: many(cronJobs),
  dailyCosts: many(dailyCosts),
  revenueSnapshots: many(revenueSnapshots),
}));

export const tasksRelations = relations(tasks, ({ one, many }) => ({
  brand: one(brands, {
    fields: [tasks.brand_id],
    references: [brands.id],
  }),
  files: many(taskFiles),
  approvals: many(approvals),
  activities: many(activities),
}));

export const taskFilesRelations = relations(taskFiles, ({ one }) => ({
  task: one(tasks, {
    fields: [taskFiles.task_id],
    references: [tasks.id],
  }),
}));

export const approvalsRelations = relations(approvals, ({ one }) => ({
  brand: one(brands, {
    fields: [approvals.brand_id],
    references: [brands.id],
  }),
  task: one(tasks, {
    fields: [approvals.task_id],
    references: [tasks.id],
  }),
}));

export const activitiesRelations = relations(activities, ({ one }) => ({
  brand: one(brands, {
    fields: [activities.brand_id],
    references: [brands.id],
  }),
  task: one(tasks, {
    fields: [activities.task_id],
    references: [tasks.id],
  }),
}));

// ---------------------------------------------------------------------------
// Type exports
// ---------------------------------------------------------------------------
export type Brand = InferSelectModel<typeof brands>;
export type InsertBrand = InferInsertModel<typeof brands>;

export type Task = InferSelectModel<typeof tasks>;
export type InsertTask = InferInsertModel<typeof tasks>;

export type TaskFile = InferSelectModel<typeof taskFiles>;
export type InsertTaskFile = InferInsertModel<typeof taskFiles>;

export type Approval = InferSelectModel<typeof approvals>;
export type InsertApproval = InferInsertModel<typeof approvals>;

export type Activity = InferSelectModel<typeof activities>;
export type InsertActivity = InferInsertModel<typeof activities>;

export type CronJob = InferSelectModel<typeof cronJobs>;
export type InsertCronJob = InferInsertModel<typeof cronJobs>;

export type DailyCost = InferSelectModel<typeof dailyCosts>;
export type InsertDailyCost = InferInsertModel<typeof dailyCosts>;

export type RevenueSnapshot = InferSelectModel<typeof revenueSnapshots>;
export type InsertRevenueSnapshot = InferInsertModel<typeof revenueSnapshots>;

export type Notification = InferSelectModel<typeof notifications>;
export type InsertNotification = InferInsertModel<typeof notifications>;

export type WebauthnCredential = InferSelectModel<typeof webauthnCredentials>;
export type InsertWebauthnCredential = InferInsertModel<typeof webauthnCredentials>;
