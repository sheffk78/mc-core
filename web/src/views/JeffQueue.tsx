import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { Check, X, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { useDataStore } from '../stores/data';
import { useDashboardStore } from '../stores/dashboard';
import { api } from '../lib/api';
import { Badge, Button } from '../components/ui';
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

// ── Empty state ──

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-black/[0.03] px-4 py-6">
      <CheckCircle2 size={18} className="text-[var(--mc-green)]/40" />
      <span className="text-sm text-[var(--mc-ink-muted)]/60">{message}</span>
    </div>
  );
}

// ── Queue Item Card (for approvals) ──

function ApprovalItem({
  approval,
  onAction,
}: {
  approval: Approval;
  onAction: (id: string, action: 'approved' | 'rejected') => void;
}) {
  const [acting, setActing] = useState(false);

  const handleAction = async (action: 'approved' | 'rejected') => {
    setActing(true);
    try {
      await api.patch(`/approvals/${approval.id}`, { status: action });
      onAction(approval.id, action);
    } catch {
      // Revert on error — re-fetch
    } finally {
      setActing(false);
    }
  };

  return (
    <div className="rounded-[0.75rem] border border-white/[0.06] bg-white/[0.03] p-[4px] transition-all duration-200 hover:border-white/[0.12]">
      <div className="rounded-[calc(0.75rem-4px)] bg-[var(--mc-surface)] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
        {/* Header row */}
        <div className="flex items-start gap-2">
          <span
            className="mt-1 h-2 w-2 flex-shrink-0 rounded-full"
            style={{
              backgroundColor:
                approval.risk_tier === 'red'
                  ? 'var(--mc-red)'
                  : approval.risk_tier === 'yellow'
                    ? 'var(--mc-yellow)'
                    : 'var(--mc-green)',
            }}
          />
          <div className="flex-1 min-w-0">
            <div className="text-[13px] font-medium text-[var(--mc-ink)] leading-tight">
              {approval.title}
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

        {/* Action buttons */}
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

// ── Queue Item Card (for tasks in review) ──

function ReviewTaskItem({ task }: { task: Task }) {
  const navigate = useDashboardStore((s) => s.setActiveView);

  return (
    <div
      onClick={() => navigate('tasks')}
      className="cursor-pointer rounded-[0.75rem] border border-white/[0.06] bg-white/[0.03] p-[4px] transition-all duration-200 hover:border-white/[0.12]"
      style={{ transitionTimingFunction: 'cubic-bezier(0.32, 0.72, 0, 1)' }}
    >
      <div className="rounded-[calc(0.75rem-4px)] bg-[var(--mc-surface)] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
        <div className="flex items-start gap-2">
          <span
            className="mt-1 h-2 w-2 flex-shrink-0 rounded-full"
            style={{
              backgroundColor:
                task.risk_tier === 'red'
                  ? 'var(--mc-red)'
                  : task.risk_tier === 'yellow'
                    ? 'var(--mc-yellow)'
                    : 'var(--mc-green)',
            }}
          />
          <div className="flex-1 min-w-0">
            <div className="text-[13px] font-medium text-[var(--mc-ink)] leading-tight line-clamp-2">
              {task.title}
            </div>
            <div className="mt-0.5 flex items-center gap-2">
              {task.category && (
                <span className="rounded bg-black/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
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
      </div>
    </div>
  );
}

// ── Completed task row ──

function CompletedTaskRow({ task }: { task: Task }) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-black/[0.03] px-4 py-2.5 transition-colors duration-150 hover:bg-black/[0.05]">
      <CheckCircle2 size={14} className="flex-shrink-0 text-[var(--mc-green)]/60" />
      <div className="flex-1 min-w-0">
        <span className="text-[13px] text-[var(--mc-ink)]/70 line-clamp-1">
          {task.title}
        </span>
      </div>
      <span className="text-[11px] text-[var(--mc-ink-muted)] whitespace-nowrap">
        {task.brand_name ?? task.brand_slug}
      </span>
      <span className="text-[11px] text-[var(--mc-ink-muted)] whitespace-nowrap">
        {task.completed_at ? relativeTime(task.completed_at) : '—'}
      </span>
    </div>
  );
}

// ── Section header ──

function SectionHeader({
  icon,
  title,
  count,
  color,
}: {
  icon: React.ReactNode;
  title: string;
  count: number;
  color: string;
}) {
  return (
    <div className="flex items-center gap-2 px-1">
      {icon}
      <h2
        className="text-sm font-medium uppercase tracking-wider"
        style={{ color }}
      >
        {title}
      </h2>
      <span
        className="ml-1 inline-flex items-center justify-center rounded-full min-w-[20px] h-5 px-1.5 text-[11px] font-medium"
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
  const { tasks, approvals, loading, fetchTasks, fetchApprovals } = useDataStore();
  const jeffQueue = useDataStore((s) => s.jeffQueue);
  const fetchJeffQueue = useDataStore((s) => s.fetchJeffQueue);
  const activeBrand = useDashboardStore((s) => s.activeBrand);
  const [removedApprovalIds, setRemovedApprovalIds] = useState<Set<string>>(new Set());

  // Fetch all queue data
  useEffect(() => {
    fetchJeffQueue();
    fetchApprovals({ status: 'pending', brand: activeBrand ?? undefined });
    fetchTasks({ status: 'pending_review', brand: activeBrand ?? undefined });
    fetchTasks({ status: 'completed', brand: activeBrand ?? undefined, limit: 20 });
  }, [activeBrand, fetchJeffQueue, fetchApprovals, fetchTasks]);

  // Re-fetch on approval action
  const handleApprovalAction = useCallback(
    (_id: string, _action: 'approved' | 'rejected') => {
      setRemovedApprovalIds((prev) => new Set(prev).add(_id));
      fetchJeffQueue();
      fetchApprovals({ status: 'pending', brand: activeBrand ?? undefined });
    },
    [fetchJeffQueue, fetchApprovals, activeBrand],
  );

  // Split approvals by risk tier (excluding acted-on ones)
  const { redApprovals, yellowGreenApprovals, reviewTasks, completedTasks } = useMemo(() => {
    const visibleApprovals = approvals.filter((a) => !removedApprovalIds.has(a.id));

    // Red tier = needs decision
    const redApprovals = visibleApprovals.filter((a) => a.risk_tier === 'red' && a.status === 'pending');

    // Yellow/Green tier = ready for review
    const yellowGreenApprovals = visibleApprovals.filter(
      (a) => a.risk_tier !== 'red' && a.status === 'pending',
    );

    // Tasks with pending_review status
    const reviewTasks = tasks.filter((t) => t.status === 'pending_review');

    // Completed tasks in last 24h
    const twentyFourAgo = Date.now() - 24 * 60 * 60 * 1000;
    const completedTasks = tasks
      .filter(
        (t) =>
          t.status === 'completed' &&
          t.completed_at &&
          new Date(t.completed_at).getTime() > twentyFourAgo,
      )
      .sort(
        (a, b) => new Date(b.completed_at!).getTime() - new Date(a.completed_at!).getTime(),
      );

    return { redApprovals, yellowGreenApprovals, reviewTasks, completedTasks };
  }, [approvals, tasks, removedApprovalIds]);

  const isLoading = loading.jeffQueue || loading.approvals || loading.tasks;

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      {/* Page header */}
      <div className="flex items-baseline justify-between">
        <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">
          Jeff's Queue
        </h1>
        <span className="text-sm text-[var(--mc-ink-muted)]">
          {isLoading ? '…' : `${jeffQueue?.total ?? 0} items`}
        </span>
      </div>

      <div className="mt-8 flex flex-col gap-8">
        {/* 🔴 NEEDS DECISION */}
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/5 p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <SectionHeader
              icon={<AlertCircle size={14} className="text-[var(--mc-red)]" />}
              title="Needs Decision"
              count={redApprovals.length}
              color="var(--mc-red)"
            />
            <div className="mt-4 flex flex-col gap-2">
              {isLoading ? (
                <div className="h-16 animate-pulse rounded-lg bg-black/5" />
              ) : redApprovals.length === 0 ? (
                <EmptyState message="Nothing needs your attention" />
              ) : (
                redApprovals.map((approval) => (
                  <ApprovalItem
                    key={approval.id}
                    approval={approval}
                    onAction={handleApprovalAction}
                  />
                ))
              )}
            </div>
          </div>
        </div>

        {/* 🟡 READY FOR REVIEW */}
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/5 p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <SectionHeader
              icon={<Clock size={14} className="text-[var(--mc-yellow)]" />}
              title="Ready for Review"
              count={yellowGreenApprovals.length + reviewTasks.length}
              color="var(--mc-yellow)"
            />
            <div className="mt-4 flex flex-col gap-2">
              {isLoading ? (
                <div className="h-16 animate-pulse rounded-lg bg-black/5" />
              ) : yellowGreenApprovals.length === 0 && reviewTasks.length === 0 ? (
                <EmptyState message="Nothing needs your attention" />
              ) : (
                <>
                  {yellowGreenApprovals.map((approval) => (
                    <ApprovalItem
                      key={approval.id}
                      approval={approval}
                      onAction={handleApprovalAction}
                    />
                  ))}
                  {reviewTasks.map((task) => (
                    <ReviewTaskItem key={task.id} task={task} />
                  ))}
                </>
              )}
            </div>
          </div>
        </div>

        {/* 🟢 RECENTLY COMPLETED */}
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/5 p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <SectionHeader
              icon={<CheckCircle2 size={14} className="text-[var(--mc-green)]" />}
              title="Recently Completed"
              count={completedTasks.length}
              color="var(--mc-green)"
            />
            <div className="mt-4 flex flex-col gap-1">
              {isLoading ? (
                <div className="h-12 animate-pulse rounded-lg bg-black/5" />
              ) : completedTasks.length === 0 ? (
                <EmptyState message="No completions in the last 24 hours" />
              ) : (
                completedTasks.map((task) => (
                  <CompletedTaskRow key={task.id} task={task} />
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
