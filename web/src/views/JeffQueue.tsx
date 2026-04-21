import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { Check, X, Clock, AlertCircle, ArrowRight } from 'lucide-react';
import { useDataStore } from '../stores/data';
import { useDashboardStore } from '../stores/dashboard';
import { api } from '../lib/api';
import { Badge, Button } from '../components/ui';
import { TaskDetailModal } from '../components/tasks/TaskDetailModal';
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

/** Map urgency level to a color variable and label */
type UrgencyLevel = 'urgent' | 'attention' | 'aware';

function getUrgencyForApproval(approval: Approval): UrgencyLevel {
  // Public-facing types are always urgent — they block external output
  if (['email', 'social', 'spend'].includes(approval.type)) return 'urgent';
  // Red risk_tier = needs Jeff's call now
  if (approval.risk_tier === 'red') return 'urgent';
  // Yellow risk_tier = should review soon
  if (approval.risk_tier === 'yellow') return 'attention';
  // Green risk_tier = low risk, can wait
  return 'aware';
}

function getUrgencyForTask(task: Task): UrgencyLevel {
  // Open tasks assigned to Jeff — they need his action
  if (task.status === 'open' && task.assignee === 'jeff') {
    if (task.priority === 'critical') return 'urgent';
    if (task.priority === 'high') return 'attention';
    return 'aware';
  }
  // Pending review — Kit finished, Jeff needs to review
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

// ── Empty state ──

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-white/[0.02] px-4 py-6">
      <Check size={18} className="text-[var(--mc-green)]/40" />
      <span className="text-sm text-[var(--mc-ink-muted)]/60">{message}</span>
    </div>
  );
}

// ── Urgency badge ──

function UrgencyBadge({ level }: { level: UrgencyLevel }) {
  const cfg = URGENCY_CONFIG[level];
  if (!cfg.label) return null;
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider"
      style={{
        color: cfg.color,
        backgroundColor: `color-mix(in oklch, ${cfg.color} 15%, transparent)`,
      }}
    >
      {level === 'urgent' && <AlertCircle size={10} />}
      {cfg.label}
    </span>
  );
}

// ── Queue item types ──

type QueueItem =
  | { kind: 'approval'; data: Approval; urgency: UrgencyLevel }
  | { kind: 'task'; data: Task; urgency: UrgencyLevel };

// ── Approval Item ──

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
      // Revert on error — re-fetch handled by parent
    } finally {
      setActing(false);
    }
  };

  return (
    <div
      className="rounded-[0.75rem] border bg-white/[0.03] p-[4px] transition-all duration-200 hover:border-white/[0.12]"
      style={{ borderColor: cfg.border }}
    >
      <div
        className="rounded-[calc(0.75rem-4px)] p-3"
        style={{ backgroundColor: cfg.bg }}
      >
        {/* Header row */}
        <div className="flex items-start gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-medium text-[var(--mc-ink)] leading-tight">
                {approval.title}
              </span>
              <UrgencyBadge level={urgency} />
            </div>
            <div className="mt-0.5 flex items-center gap-2">
              <Badge className="text-[10px]">{approval.type}</Badge>
              <span className="text-[11px] text-[var(--mc-ink-muted)]">
                {approval.brand_name ?? approval.brand_slug}
              </span>
            </div>
          </div>
          <span className="text-[11px] text-[var(--mc-ink-muted)] whitespace-nowrap">
            {relativeTime(approval.created_at)}
          </span>
        </div>

        {/* Preview */}
        {approval.preview && (
          <div className="mt-2 line-clamp-2 text-[12px] text-[var(--mc-ink-muted)]">
            {approval.preview}
          </div>
        )}

        {/* Action buttons — always show for pending */}
        {approval.status === 'pending' && (
          <div className="mt-3 flex items-center gap-2">
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
    </div>
  );
}

// ── Task Item ──

function TaskItem({ task, urgency, onClick }: { task: Task; urgency: UrgencyLevel; onClick?: () => void }) {
  const cfg = URGENCY_CONFIG[urgency];

  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-[0.75rem] border bg-white/[0.03] p-[4px] transition-all duration-200 hover:border-white/[0.12]"
      style={{ borderColor: cfg.border, transitionTimingFunction: 'cubic-bezier(0.32, 0.72, 0, 1)' }}
    >
      <div
        className="rounded-[calc(0.75rem-4px)] p-3"
        style={{ backgroundColor: cfg.bg }}
      >
        <div className="flex items-start gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-medium text-[var(--mc-ink)] leading-tight line-clamp-2">
                {task.title}
              </span>
              <UrgencyBadge level={urgency} />
            </div>
            <div className="mt-0.5 flex items-center gap-2">
              {task.category && (
                <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
                  {task.category}
                </span>
              )}
              <span className="text-[11px] text-[var(--mc-ink-muted)]">
                {task.brand_name ?? task.brand_slug}
              </span>
            </div>
          </div>
          <span className="text-[11px] text-[var(--mc-ink-muted)] whitespace-nowrap">
            {relativeTime(task.created_at)}
          </span>
        </div>

        {task.agent_note && (
          <div className="mt-2 line-clamp-2 text-[12px] text-[var(--mc-ink-muted)]">
            {task.agent_note}
          </div>
        )}

        {/* Status indicator */}
        {task.status === 'pending_review' && (
          <div className="mt-2 flex items-center gap-1 text-[11px]" style={{ color: cfg.color }}>
            <ArrowRight size={10} />
            <span>Kit finished — needs your review</span>
          </div>
        )}
        {task.status === 'open' && task.assignee === 'jeff' && (
          <div className="mt-2 flex items-center gap-1 text-[11px]" style={{ color: cfg.color }}>
            <ArrowRight size={10} />
            <span>Waiting on you</span>
          </div>
        )}
      </div>
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
        <h2
          className="text-sm font-medium uppercase tracking-wider"
          style={{ color }}
        >
          {title}
        </h2>
        {subtitle && (
          <p className="text-[11px] text-[var(--mc-ink-muted)]">{subtitle}</p>
        )}
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

// ── Main JeffQueue View ──

export default function JeffQueueView() {
  const { tasks, jeffOpenTasks, approvals, loading, fetchTasks, fetchJeffOpenTasks, fetchApprovals } = useDataStore();
  const fetchJeffQueue = useDataStore((s) => s.fetchJeffQueue);
  const activeBrand = useDashboardStore((s) => s.activeBrand);
  const [removedApprovalIds, setRemovedApprovalIds] = useState<Set<string>>(new Set());
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  // Fetch all queue data
  useEffect(() => {
    fetchJeffQueue();
    fetchApprovals({ status: 'pending', brand: activeBrand ?? undefined });
    fetchTasks({ status: 'pending_review', brand: activeBrand ?? undefined });
    fetchJeffOpenTasks(activeBrand ?? undefined);
    // NOTE: We intentionally do NOT fetch completed tasks anymore
  }, [activeBrand, fetchJeffQueue, fetchApprovals, fetchTasks, fetchJeffOpenTasks]);

  // Re-fetch on approval action
  const handleApprovalAction = useCallback(
    (_id: string, _action: 'approved' | 'rejected') => {
      setRemovedApprovalIds((prev) => new Set(prev).add(_id));
      fetchJeffQueue();
      fetchApprovals({ status: 'pending', brand: activeBrand ?? undefined });
    },
    [fetchJeffQueue, fetchApprovals, activeBrand],
  );

  // ── Build queue items with mutually exclusive categorization ──
  const { needsJeffItems, inProgressItems } = useMemo(() => {
    const visibleApprovals = approvals.filter(
      (a) => !removedApprovalIds.has(a.id) && a.status === 'pending',
    );
    const reviewTasks = tasks.filter((t) => t.status === 'pending_review');
    const openJeffTasks = jeffOpenTasks; // status=open, assignee=jeff

    // ── "Needs Jeff" ──
    // Everything that requires Jeff's direct action right now:
    //   1. Pending approvals (all of them — Jeff must approve/reject)
    //   2. Tasks in pending_review (Kit finished, Jeff must review)
    //   3. Open tasks assigned to Jeff (Jeff is the blocker)
    const needsJeffItems: QueueItem[] = [
      ...visibleApprovals.map((a) => ({
        kind: 'approval' as const,
        data: a,
        urgency: getUrgencyForApproval(a),
      })),
      ...reviewTasks.map((t) => ({
        kind: 'task' as const,
        data: t,
        urgency: getUrgencyForTask(t),
      })),
      ...openJeffTasks.map((t) => ({
        kind: 'task' as const,
        data: t,
        urgency: getUrgencyForTask(t),
      })),
    ];

    // Sort by urgency (urgent → attention → aware), then by created_at ASC (oldest first within tier)
    const urgencyOrder: Record<UrgencyLevel, number> = { urgent: 0, attention: 1, aware: 2 };
    needsJeffItems.sort((a, b) => {
      const uDiff = urgencyOrder[a.urgency] - urgencyOrder[b.urgency];
      if (uDiff !== 0) return uDiff;
      return (a.data.created_at ?? '').localeCompare(b.data.created_at ?? '');
    });

    // ── "In Progress" ──
    // Items Kit is actively working on that Jeff should be aware of but doesn't need to act on yet.
    // This is intentionally empty for now — we don't fetch in_progress tasks yet.
    // Future: add tasks where status='in_progress' and assignee='kit'
    const inProgressItems: QueueItem[] = [];

    return { needsJeffItems, inProgressItems };
  }, [approvals, tasks, jeffOpenTasks, removedApprovalIds]);

  const isLoading = loading.jeffQueue || loading.approvals || loading.tasks;

  // Urgency counts for the badge
  const urgentCount = needsJeffItems.filter((i) => i.urgency === 'urgent').length;

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      {/* Page header */}
      <div className="flex items-baseline justify-between">
        <div className="flex items-baseline gap-3">
          <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">
            Jeff's Queue
          </h1>
          {urgentCount > 0 && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--mc-red)]/15 px-2.5 py-0.5 text-[12px] font-medium text-[var(--mc-red)]">
              <AlertCircle size={12} />
              {urgentCount} urgent
            </span>
          )}
        </div>
        <span className="text-sm text-[var(--mc-ink-muted)]">
          {isLoading ? '…' : `${needsJeffItems.length + inProgressItems.length} items`}
        </span>
      </div>

      <div className="mt-8 flex flex-col gap-8">
        {/* ── NEEDS JEFF ── */}
        <div className="rounded-[1rem] border border-white/[0.08] bg-white/5 p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
            <SectionHeader
              icon={<AlertCircle size={14} className="text-[var(--mc-accent)]" />}
              title="Needs Jeff"
              subtitle="Approvals, reviews, and tasks waiting on you"
              count={needsJeffItems.length}
              color="var(--mc-accent)"
            />
            <div className="mt-4 flex flex-col gap-2">
              {isLoading ? (
                <>
                  <div className="h-16 animate-pulse rounded-lg bg-white/5" />
                  <div className="h-16 animate-pulse rounded-lg bg-white/5" />
                </>
              ) : needsJeffItems.length === 0 ? (
                <EmptyState message="Nothing needs your attention right now" />
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
                    <TaskItem
                      key={`task-${(item.data as Task).id}`}
                      task={item.data as Task}
                      urgency={item.urgency}
                      onClick={() => setSelectedTask(item.data as Task)}
                    />
                  ),
                )
              )}
            </div>
          </div>
        </div>

        {/* ── IN PROGRESS ── */}
        {/* Show this section only when there are in-progress items */}
        {inProgressItems.length > 0 && (
          <div className="rounded-[1rem] border border-white/[0.08] bg-white/5 p-[6px]">
            <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
              <SectionHeader
                icon={<Clock size={14} className="text-[var(--mc-ink-muted)]" />}
                title="In Progress"
                subtitle="Kit is working on these — no action needed from you yet"
                count={inProgressItems.length}
                color="var(--mc-ink-muted)"
              />
              <div className="mt-4 flex flex-col gap-2">
                {inProgressItems.map((item) =>
                  item.kind === 'approval' ? (
                    <ApprovalItem
                      key={`approval-${item.data.id}`}
                      approval={item.data as Approval}
                      urgency={item.urgency}
                      onAction={handleApprovalAction}
                    />
                  ) : (
                    <TaskItem
                      key={`task-${(item.data as Task).id}`}
                      task={item.data as Task}
                      urgency={item.urgency}
                      onClick={() => setSelectedTask(item.data as Task)}
                    />
                  ),
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <TaskDetailModal
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          onUpdated={(updated) => {
            setSelectedTask(updated);
            fetchJeffQueue();
            fetchJeffOpenTasks(activeBrand ?? undefined);
          }}
        />
      )}
    </div>
  );
}