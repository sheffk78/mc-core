import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { Check, X, Clock, AlertCircle, ArrowRight, Plus, MessageSquare, ChevronDown, ChevronUp, Zap } from 'lucide-react';
import { useDataStore } from '../stores/data';
import { useDashboardStore } from '../stores/dashboard';
import { api } from '../lib/api';
import { Badge, Button } from '../components/ui';
import { TaskDetailModal } from '../components/tasks/TaskDetailModal';
import { NewTaskModal } from '../components/tasks/NewTaskModal';
import type { Task, Approval } from '../lib/types';

// ── Helpers ──

function relativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function timeAgoShort(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  return `${days}d`;
}

type UrgencyLevel = 'urgent' | 'attention' | 'aware';

function getUrgencyForApproval(approval: Approval): UrgencyLevel {
  if (['email', 'social', 'spend'].includes(approval.type)) return 'urgent';
  if (approval.risk_tier === 'red') return 'urgent';
  if (approval.risk_tier === 'yellow') return 'attention';
  return 'aware';
}

function getUrgencyForTask(task: Task): UrgencyLevel {
  if (task.status === 'blocked') return 'urgent';
  if (task.status === 'open' && task.assignee === 'jeff') {
    if (task.priority === 'critical') return 'urgent';
    if (task.priority === 'high') return 'attention';
    return 'aware';
  }
  if (task.status === 'pending_review') {
    if (task.risk_tier === 'red' || task.priority === 'critical') return 'urgent';
    if (task.risk_tier === 'yellow' || task.priority === 'high') return 'attention';
    return 'aware';
  }
  return 'aware';
}

const URGENCY_CONFIG: Record<UrgencyLevel, { color: string; bg: string; border: string; label: string }> = {
  urgent: {
    color: 'var(--mc-red)',
    bg: 'color-mix(in oklch, var(--mc-red) 8%, transparent)',
    border: 'color-mix(in oklch, var(--mc-red) 20%, transparent)',
    label: 'Urgent',
  },
  attention: {
    color: 'var(--mc-yellow)',
    bg: 'color-mix(in oklch, var(--mc-yellow) 8%, transparent)',
    border: 'color-mix(in oklch, var(--mc-yellow) 20%, transparent)',
    label: 'Soon',
  },
  aware: {
    color: 'var(--mc-ink-muted)',
    bg: 'color-mix(in oklch, var(--mc-ink-muted) 5%, transparent)',
    border: 'color-mix(in oklch, var(--mc-ink-muted) 10%, transparent)',
    label: '',
  },
};

const STATUS_COLORS: Record<string, string> = {
  open: '#3b82f6',
  in_progress: '#f59e0b',
  blocked: '#ef4444',
  pending_review: '#a855f7',
  approved: '#22c55e',
  rejected: '#ef4444',
  completed: '#10b981',
  archived: '#6b7280',
};

const STATUS_LABELS: Record<string, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  blocked: 'Blocked',
  pending_review: 'Review',
  approved: 'Approved',
  rejected: 'Rejected',
  completed: 'Done',
  archived: 'Archived',
};

// ── Quick Add Form ──

function QuickAddForm({ onCreated, brands }: { onCreated: () => void; brands: any[] }) {
  const [title, setTitle] = useState('');
  const [brandSlug, setBrandSlug] = useState('general');
  const [priority, setPriority] = useState('normal');
  const [description, setDescription] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Skills per brand
  const BRAND_SKILLS: Record<string, string[]> = {
    trustoffice: ['analytics', 'affiliate', 'content', 'seo', 'social', 'email', 'outreach', 'ads', 'competitor'],
    agentictrust: ['coding', 'research', 'positioning', 'competitor', 'content', 'devops'],
    wingpoint: ['content', 'community', 'email', 'outreach', 'seo'],
    truejoybirthing: ['content', 'social', 'email', 'community', 'seo'],
    general: ['research', 'coding', 'content', 'admin', 'competitor'],
  };
  const availableSkills = BRAND_SKILLS[brandSlug] || BRAND_SKILLS.general;
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || submitting) return;

    setSubmitting(true);
    try {
      await api.post('/tasks', {
        title: title.trim(),
        brand_slug: brandSlug,
        priority,
        description: description.trim() || undefined,
        assignee: 'kit',
        source: 'mc_ui',
        category: selectedSkills.length > 0 ? selectedSkills.join(',') : undefined,
        agent_note: selectedSkills.length > 0 ? `Relevant skills: ${selectedSkills.join(', ')}` : undefined,
      });
      setTitle('');
      setDescription('');
      setPriority('normal');
      setIsExpanded(false);
      onCreated();
    } catch (err) {
      console.error('Failed to create task:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-[1rem] border border-white/[0.08] bg-white/5 p-[6px]">
      <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
        <div className="flex items-center gap-2">
          <Plus size={16} className="text-[var(--mc-accent)]" />
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Add a task..."
            className="flex-1 bg-transparent text-sm text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:outline-none"
            onFocus={() => setIsExpanded(true)}
          />
          <Button size="sm" variant="default" disabled={!title.trim() || submitting} type="submit">
            {submitting ? '...' : 'Add'}
          </Button>
        </div>

        {isExpanded && (
          <div className="mt-3 space-y-2">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Details (optional)..."
              rows={2}
              className="w-full rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] px-3 py-2 text-sm text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:border-[var(--mc-accent)] focus:outline-none resize-none"
            />
            <div className="flex items-center gap-3">
              <select
                value={brandSlug}
                onChange={(e) => { setBrandSlug(e.target.value); setSelectedSkills([]); }}
                className="rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] px-2 py-1 text-xs text-[var(--mc-ink)] focus:outline-none"
              >
                {brands.map((b) => (
                  <option key={b.slug} value={b.slug}>{b.name}</option>
                ))}
              </select>
              {/* Skills multi-select */}
              <div className="flex flex-wrap gap-1">
                {availableSkills.map((skill) => (
                  <button
                    key={skill}
                    type="button"
                    onClick={() => setSelectedSkills(prev => 
                      prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]
                    )}
                    className={`rounded px-1.5 py-0.5 text-[10px] font-medium transition-all ${
                      selectedSkills.includes(skill)
                        ? 'bg-[var(--mc-accent)]/20 text-[var(--mc-accent)] border border-[var(--mc-accent)]/40'
                        : 'bg-white/5 text-[var(--mc-ink-muted)] border border-transparent hover:bg-white/10'
                    }`}
                  >
                    {skill}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1">
                {(['low', 'normal', 'high', 'critical'] as const).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPriority(p)}
                    className={`rounded px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider transition-all ${
                      priority === p
                        ? 'bg-[var(--mc-accent)] text-white'
                        : 'bg-white/5 text-[var(--mc-ink-muted)] hover:bg-white/10'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </form>
  );
}

// ── Task Card (compact) ──

function CompactTaskCard({ task, onClick }: { task: Task; onClick?: () => void }) {
  const urgency = getUrgencyForTask(task);
  const cfg = URGENCY_CONFIG[urgency];
  const statusColor = STATUS_COLORS[task.status] || '#6b7280';

  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-lg border bg-white/[0.03] p-3 transition-all duration-200 hover:border-white/[0.12]"
      style={{ borderColor: cfg.border }}
    >
      <div className="flex items-start gap-2">
        <div
          className="mt-1 h-2 w-2 rounded-full flex-shrink-0"
          style={{ backgroundColor: statusColor }}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[13px] font-medium text-[var(--mc-ink)] leading-tight line-clamp-2">
              {task.title}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
              {STATUS_LABELS[task.status] || task.status}
            </span>
            {task.category && (
              <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
                {task.category}
              </span>
            )}
            <span className="text-[11px] text-[var(--mc-ink-muted)]">
              {task.brand_name ?? task.brand_slug}
            </span>
          </div>
          {task.blocked_on && task.status === 'blocked' && (
            <div className="mt-1.5 flex items-center gap-1 text-[11px] text-[var(--mc-red)]">
              <AlertCircle size={10} />
              <span className="line-clamp-1">Blocked: {task.blocked_on}</span>
            </div>
          )}
          {task.checkpoint_summary && task.status === 'in_progress' && (
            <div className="mt-1 text-[11px] text-[var(--mc-ink-muted)] line-clamp-1">
              {task.checkpoint_summary}
            </div>
          )}
        </div>
        <span className="text-[10px] text-[var(--mc-ink-muted)] whitespace-nowrap">
          {timeAgoShort(task.created_at)}
        </span>
      </div>
    </div>
  );
}

// ── Approval Card ──

function ApprovalItem({
  approval,
  urgency,
  onAction,
}: {
  approval: Approval;
  urgency: UrgencyLevel;
  onAction: (id: string, action: 'approved' | 'rejected') => void;
}) {
  const [acting, setActing] = useState(false);
  const cfg = URGENCY_CONFIG[urgency];

  const handleAction = async (action: 'approved' | 'rejected') => {
    setActing(true);
    try {
      await api.patch(`/approvals/${approval.id}`, { status: action });
      onAction(approval.id, action);
    } catch {
      // Revert on error
    } finally {
      setActing(false);
    }
  };

  return (
    <div
      className="rounded-lg border bg-white/[0.03] p-3 transition-all duration-200 hover:border-white/[0.12]"
      style={{ borderColor: cfg.border }}
    >
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[13px] font-medium text-[var(--mc-ink)] leading-tight">
              {approval.title}
            </span>
          </div>
          <div className="mt-0.5 flex items-center gap-2">
            <Badge className="text-[10px]">{approval.type}</Badge>
            <span className="text-[11px] text-[var(--mc-ink-muted)]">
              {approval.brand_name ?? approval.brand_slug}
            </span>
          </div>
        </div>
        <span className="text-[10px] text-[var(--mc-ink-muted)] whitespace-nowrap">
          {timeAgoShort(approval.created_at)}
        </span>
      </div>
      {approval.preview && (
        <div className="mt-2 line-clamp-2 text-[12px] text-[var(--mc-ink-muted)]">
          {approval.preview}
        </div>
      )}
      {approval.status === 'pending' && (
        <div className="mt-2 flex items-center gap-2">
          <Button
            size="sm"
            variant="default"
            disabled={acting}
            onClick={() => handleAction('approved')}
            className="flex items-center gap-1"
          >
            <Check size={12} />
            Approve
          </Button>
          <Button
            size="sm"
            variant="destructive"
            disabled={acting}
            onClick={() => handleAction('rejected')}
            className="flex items-center gap-1"
          >
            <X size={12} />
            Reject
          </Button>
        </div>
      )}
    </div>
  );
}

// ── Section header ──

function SectionHeader({
  icon,
  title,
  subtitle,
  count,
  color,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  count: number;
  color: string;
}) {
  return (
    <div className="flex items-center gap-2 px-1">
      {icon}
      <div className="flex-1">
        <h2 className="text-sm font-medium uppercase tracking-wider" style={{ color }}>
          {title}
        </h2>
        {subtitle && <p className="text-[11px] text-[var(--mc-ink-muted)]">{subtitle}</p>}
      </div>
      <span
        className="inline-flex items-center justify-center rounded-full min-w-[20px] h-5 px-1.5 text-[11px] font-medium"
        style={{
          backgroundColor: `color-mix(in oklch, ${color} 15%, transparent)`,
          color,
        }}
      >
        {count}
      </span>
    </div>
  );
}

// ── Main JeffIntake View ──

export default function JeffIntakeView() {
  const { tasks, jeffOpenTasks, approvals, loading, fetchTasks, fetchJeffOpenTasks, fetchApprovals, fetchJeffQueue } = useDataStore();
  const { brands } = useDataStore();
  const activeBrand = useDashboardStore((s) => s.activeBrand);
  const [removedApprovalIds, setRemovedApprovalIds] = useState<Set<string>>(new Set());
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showNewTask, setShowNewTask] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Fetch all queue data
  const refresh = useCallback(() => {
    fetchJeffQueue();
    fetchApprovals({ status: 'pending', brand: activeBrand ?? undefined });
    // Fetch all active tasks for kit — this populates the "Kit Working" column
    fetchTasks({ status: 'open,in_progress,blocked,pending_review', assignee: 'kit', brand: activeBrand ?? undefined });
    // Fetch tasks needing jeff's attention
    fetchJeffOpenTasks(activeBrand ?? undefined);
    setRefreshKey((k) => k + 1);
  }, [activeBrand, fetchJeffQueue, fetchApprovals, fetchTasks, fetchJeffOpenTasks]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Auto-refresh every 30s
  useEffect(() => {
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  // Re-fetch on approval action
  const handleApprovalAction = useCallback(
    (_id: string, _action: 'approved' | 'rejected') => {
      setRemovedApprovalIds((prev) => new Set(prev).add(_id));
      refresh();
    },
    [refresh],
  );

  // ── Categorize items ──
  const visibleApprovals = approvals.filter(
    (a) => !removedApprovalIds.has(a.id) && a.status === 'pending',
  );

  const blockedTasks = tasks.filter((t) => t.status === 'blocked');
  const reviewTasks = tasks.filter((t) => t.status === 'pending_review');
  const openJeffTasks = jeffOpenTasks; // status=open, assignee=jeff

  const needsJeffItems = [
    ...visibleApprovals.map((a) => ({ kind: 'approval' as const, data: a, urgency: getUrgencyForApproval(a) })),
    ...blockedTasks.map((t) => ({ kind: 'task' as const, data: t, urgency: getUrgencyForTask(t) })),
    ...reviewTasks.map((t) => ({ kind: 'task' as const, data: t, urgency: getUrgencyForTask(t) })),
    ...openJeffTasks.map((t) => ({ kind: 'task' as const, data: t, urgency: getUrgencyForTask(t) })),
  ].sort((a, b) => {
    const order: Record<UrgencyLevel, number> = { urgent: 0, attention: 1, aware: 2 };
    return order[a.urgency] - order[b.urgency];
  });

  // Kit Working: open + in_progress + blocked tasks assigned to kit
  const kitWorkingTasks = tasks.filter((t) => 
    ['open', 'in_progress', 'blocked'].includes(t.status) && t.assignee === 'kit'
  ).sort((a, b) => {
    const order: Record<string, number> = { in_progress: 0, blocked: 1, open: 2 };
    return (order[a.status] ?? 3) - (order[b.status] ?? 3);
  });
  const recentlyCompleted = tasks.filter((t) => t.status === 'completed').slice(0, 5);

  const isLoading = loading.tasks || loading.approvals;

  return (
    <div className="flex min-h-full flex-col gap-6 px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">Mission Control</h1>
          <p className="text-sm text-[var(--mc-ink-muted)]">Add tasks, review work, see what Kit is doing</p>
        </div>
      </div>

      {/* Quick Add */}
      <QuickAddForm onCreated={refresh} brands={brands} />

      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left column: Needs Jeff */}
        <div className="flex flex-col gap-6">
          {/* NEEDS JEFF */}
          <div className="rounded-[1rem] border border-white/[0.08] bg-white/5 p-[6px]">
            <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
              <SectionHeader
                icon={<AlertCircle size={14} className="text-[var(--mc-red)]" />}
                title="Needs You"
                subtitle="Approvals, blocked items, reviews"
                count={needsJeffItems.length}
                color="var(--mc-red)"
              />
              <div className="mt-4 flex flex-col gap-2">
                {isLoading ? (
                  <>
                    <div className="h-16 animate-pulse rounded-lg bg-white/5" />
                    <div className="h-16 animate-pulse rounded-lg bg-white/5" />
                  </>
                ) : needsJeffItems.length === 0 ? (
                  <div className="flex items-center gap-3 rounded-lg bg-white/[0.02] px-4 py-6">
                    <Check size={18} className="text-[var(--mc-green)]/40" />
                    <span className="text-sm text-[var(--mc-ink-muted)]/60">Nothing needs your attention right now</span>
                  </div>
                ) : (
                  needsJeffItems.map((item) =>
                    item.kind === 'approval' ? (
                      <ApprovalItem
                        key={`approval-${item.data.id}`}
                        approval={item.data as Approval}
                        urgency={item.urgency}
                        onAction={handleApprovalAction}
                      />
                    ) : (
                      <CompactTaskCard
                        key={`task-${(item.data as Task).id}`}
                        task={item.data as Task}
                        onClick={() => setSelectedTask(item.data as Task)}
                      />
                    ),
                  )
                )}
              </div>
            </div>
          </div>

          {/* RECENTLY COMPLETED */}
          {recentlyCompleted.length > 0 && (
            <div className="rounded-[1rem] border border-white/[0.08] bg-white/5 p-[6px]">
              <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
                <SectionHeader
                  icon={<Check size={14} className="text-[var(--mc-green)]" />}
                  title="Done"
                  subtitle="Recently completed"
                  count={recentlyCompleted.length}
                  color="var(--mc-green)"
                />
                <div className="mt-4 flex flex-col gap-2">
                  {recentlyCompleted.map((task) => (
                    <CompactTaskCard
                      key={task.id}
                      task={task}
                      onClick={() => setSelectedTask(task)}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right column: Kit's Active Work */}
        <div className="flex flex-col gap-6">
          {/* KIT IS WORKING ON */}
          <div className="rounded-[1rem] border border-white/[0.08] bg-white/5 p-[6px]">
            <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
              <SectionHeader
                icon={<Zap size={14} className="text-[var(--mc-accent)]" />}
                title="Kit Working"
                subtitle="Active, blocked, and queued"
                count={kitWorkingTasks.length}
                color="var(--mc-accent)"
              />
              <div className="mt-4 flex flex-col gap-2">
                {isLoading ? (
                  <>
                    <div className="h-16 animate-pulse rounded-lg bg-white/5" />
                    <div className="h-16 animate-pulse rounded-lg bg-white/5" />
                  </>
                ) : kitWorkingTasks.length === 0 ? (
                  <div className="flex items-center gap-3 rounded-lg bg-white/[0.02] px-4 py-6">
                    <Clock size={18} className="text-[var(--mc-ink-muted)]/40" />
                    <span className="text-sm text-[var(--mc-ink-muted)]/60">Kit isn't actively working on anything</span>
                  </div>
                ) : (
                  kitWorkingTasks.map((task) => (
                    <CompactTaskCard
                      key={task.id}
                      task={task}
                      onClick={() => setSelectedTask(task)}
                    />
                  ))
                )}
              </div>
            </div>
          </div>

          {/* OPEN TASKS (kit-assigned) */}
          {tasks.filter((t) => t.status === 'open' && t.assignee === 'kit').length > 0 && (
            <div className="rounded-[1rem] border border-white/[0.08] bg-white/5 p-[6px]">
              <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
                <SectionHeader
                  icon={<Clock size={14} className="text-[var(--mc-ink-muted)]" />}
                  title="Queued"
                  subtitle="Waiting for Kit to pick up"
                  count={tasks.filter((t) => t.status === 'open' && t.assignee === 'kit').length}
                  color="var(--mc-ink-muted)"
                />
                <div className="mt-4 flex flex-col gap-2">
                  {tasks
                    .filter((t) => t.status === 'open' && t.assignee === 'kit')
                    .slice(0, 5)
                    .map((task) => (
                      <CompactTaskCard
                        key={task.id}
                        task={task}
                        onClick={() => setSelectedTask(task)}
                      />
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <TaskDetailModal
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          onUpdated={(updated) => {
            setSelectedTask(updated);
            refresh();
          }}
        />
      )}
    </div>
  );
}