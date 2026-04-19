// ── Enum types ──

export type TaskStatus =
  | 'open'
  | 'in_progress'
  | 'pending_review'
  | 'approved'
  | 'rejected'
  | 'completed'
  | 'archived';

export type Priority = 'low' | 'normal' | 'high' | 'critical';

export type RiskTier = 'green' | 'yellow' | 'red';

export type Assignee = 'kit' | 'jeff' | 'unassigned';

export type ApprovalType =
  | 'content'
  | 'email'
  | 'social'
  | 'spend'
  | 'code'
  | 'decision';

export type ApprovalStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'expired'
  | 'auto_approved';

export type Actor = 'kit' | 'jeff' | 'system' | 'cron';

export type NotificationChannel = 'slack' | 'email' | 'dashboard';

export type NotificationStatus = 'sent' | 'failed' | 'read';

// ── Domain models ──

export interface Brand {
  id: string;
  name: string;
  slug: string;
  color: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
  task_count?: number;
  pending_approval_count?: number;
}

export interface Task {
  id: string;
  brand_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: Priority;
  risk_tier: RiskTier;
  assignee: Assignee;
  category: string | null;
  agent_note: string | null;
  user_note: string | null;
  due_date: string | null;
  completed_at: string | null;
  estimated_cost: number | null;
  actual_cost: number | null;
  model_used: string | null;
  tokens_in: number | null;
  tokens_out: number | null;
  confidence: number | null;
  created_at: string;
  updated_at: string;
  brand_slug?: string;
  brand_name?: string;
  brand_color?: string;
  linked_files?: TaskFile[];
  approval_history?: Approval[];
}

export interface TaskFile {
  id: string;
  task_id: string;
  file_path: string;
  role: 'skill' | 'output' | 'context' | 'input' | 'reference';
  label: string | null;
  created_at: string;
}

export interface Approval {
  id: string;
  brand_id: string;
  task_id: string | null;
  type: ApprovalType;
  title: string;
  preview: string | null;
  agent_reasoning: string | null;
  risk_tier: RiskTier;
  status: ApprovalStatus;
  feedback: string | null;
  metadata: string;
  created_at: string;
  decided_at: string | null;
  decided_by: string | null;
  brand_slug?: string;
  brand_name?: string;
  brand_color?: string;
  linked_task?: {
    id: string;
    title: string;
    status: TaskStatus;
    brand_slug: string;
  };
}

export interface Activity {
  id: string;
  brand_id: string | null;
  task_id: string | null;
  actor: Actor;
  action: string;
  summary: string;
  detail: string | null;
  model_used: string | null;
  tokens_used: number | null;
  cost_usd: number | null;
  created_at: string;
}

export interface CronJob {
  id: string;
  name: string;
  brand_id: string | null;
  schedule_expr: string;
  schedule_ms: number | null;
  cron_expr: string | null;
  enabled: number;
  last_run_at: string | null;
  last_status: 'success' | 'error' | 'running' | 'unknown';
  last_duration_ms: number | null;
  last_error: string | null;
  consecutive_errors: number;
  created_at: string;
  updated_at: string;
}

export interface DailyCost {
  id: string;
  date: string;
  brand_id: string | null;
  model: string;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  task_count: number;
}

export interface RevenueSnapshot {
  id: string;
  brand_id: string;
  date: string;
  mrr: number | null;
  arr: number | null;
  subscribers: number | null;
  source: string;
  metadata: string;
  created_at: string;
}

export interface Notification {
  id: string;
  channel: NotificationChannel;
  recipient: string | null;
  title: string;
  body: string | null;
  related_id: string | null;
  sent_at: string;
  status: NotificationStatus;
}

// ── Filter types ──

export interface TaskFilters {
  brand?: string;
  status?: TaskStatus;
  assignee?: Assignee;
  risk_tier?: RiskTier;
  limit?: number;
  offset?: number;
}

export interface ApprovalFilters {
  status?: ApprovalStatus;
  brand?: string;
  risk_tier?: RiskTier;
  type?: ApprovalType;
  limit?: number;
  offset?: number;
}

export interface ActivityFilters {
  brand?: string;
  actor?: string;
  since?: string;
  limit?: number;
  offset?: number;
}

// ── API response types ──

export interface News {
  id: string;
  brand_id: string;
  title: string;
  summary: string;
  source_url: string;
  source_name: string | null;
  category: string | null;
  risk_tier: 'green' | 'yellow' | 'red';
  jeff_comment: string | null;
  jeff_recommends: number;
  is_read: number;
  intel_run_id: string;
  created_at: string;
  updated_at: string;
  brand_slug?: string;
  brand_name?: string;
  brand_color?: string;
}

export interface NewsFilters {
  brand?: string;
  risk_tier?: string;
  intel_run_id?: string;
  limit?: number;
  offset?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface StatsResponse {
  pending_approvals: number;
  open_tasks: number;
  pending_review_tasks: number;
  today_cost_usd: number;
  today_budget_limit: number;
  today_budget_pct_used: number;
  active_cron_jobs: number;
  connected_files: number;
  brands_active: number;
}

export interface QueueItem {
  id: string;
  type: 'approval' | 'task';
  risk_tier: RiskTier;
  title: string;
  brand_slug: string;
  brand_color: string;
  created_at: string;
  category: string | null;
  assignee: Assignee | null;
  agent_note_preview: string;
}

export interface JeffQueueResponse {
  items: QueueItem[];
  counts: {
    red: number;
    yellow: number;
    green: number;
  };
  total: number;
}

export interface CostToday {
  date: string;
  total_cost: number;
  budget_limit: number;
  budget_remaining: number;
  budget_pct_used: number;
  by_brand: Array<{
    brand_id: string;
    brand_name: string;
    cost_usd: number;
    task_count: number;
  }>;
  by_model: Array<{
    model: string;
    cost_usd: number;
    tokens_in: number;
    tokens_out: number;
  }>;
}

export interface BudgetCheck {
  allowed: boolean;
  spent: number;
  remaining: number;
  budget_limit: number;
  threshold: number;
}
