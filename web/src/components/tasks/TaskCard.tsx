import React from 'react';
import { ChevronRight } from 'lucide-react';
import type { Task, TaskStatus } from '../../lib/types';

// ── Status badge config ──

const STATUS_CONFIG: Record<
  TaskStatus,
  { label: string; className: string }
> = {
  open: {
    label: 'Open',
    className: 'border border-[var(--mc-border)] bg-black/5 text-[var(--mc-ink-muted)]',
  },
  in_progress: {
    label: 'In Progress',
    className: 'bg-[var(--mc-accent)]/15 text-[var(--mc-accent)]',
  },
  pending_review: {
    label: 'Pending Review',
    className: 'bg-[var(--mc-yellow)]/15 text-[var(--mc-yellow)]',
  },
  approved: {
    label: 'Approved',
    className: 'bg-[var(--mc-green)]/15 text-[var(--mc-green)]',
  },
  rejected: {
    label: 'Rejected',
    className: 'bg-[var(--mc-red)]/15 text-[var(--mc-red)]',
  },
  completed: {
    label: 'Completed',
    className: 'bg-black/5 text-[var(--mc-ink-muted)]',
  },
  archived: {
    label: 'Archived',
    className: 'bg-white/3 text-[var(--mc-ink-muted)]/50 italic',
  },
};

// ── Risk tier dot color ──

const RISK_COLORS = {
  green: 'var(--mc-green)',
  yellow: 'var(--mc-yellow)',
  red: 'var(--mc-red)',
} as const;

// ── TaskCard ──

interface TaskCardProps {
  task: Task;
  onClick?: () => void;
}

export function TaskCard({ task, onClick }: TaskCardProps) {
  const statusCfg = STATUS_CONFIG[task.status];
  const isCompleted = task.status === 'completed';

  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-[1rem] border border-black/[0.08] bg-black/5 p-[6px] transition-all duration-200 hover:scale-[1.01] hover:border-white/[0.14]"
      style={{ transitionTimingFunction: 'cubic-bezier(0.32, 0.72, 0, 1)' }}
    >
      <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-3 shadow-sm">
        {/* Row 1 — Meta */}
        <div className="flex items-center gap-2">
          <span
            className="h-2 w-2 flex-shrink-0 rounded-full"
            style={{ backgroundColor: RISK_COLORS[task.risk_tier] }}
          />
          {task.category && (
            <span className="rounded bg-black/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
              {task.category}
            </span>
          )}
          <span className="ml-auto text-[11px] text-[var(--mc-ink-muted)]">
            {task.brand_name ?? task.brand_slug}
          </span>
        </div>

        {/* Row 2 — Title */}
        <div
          className={`mt-1 line-clamp-2 text-[14px] font-medium text-[var(--mc-ink)] ${
            isCompleted ? 'line-through' : ''
          }`}
        >
          {task.title}
        </div>

        {/* Row 3 — Agent note preview */}
        {task.agent_note && (
          <div className="mt-1 line-clamp-2 text-[12px] text-[var(--mc-ink-muted)]">
            {task.agent_note}
          </div>
        )}

        {/* Row 4 — Footer */}
        <div className="mt-2 flex items-center gap-2">
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] ${statusCfg.className}`}
          >
            {statusCfg.label}
          </span>

          <span className="rounded bg-black/5 px-1.5 text-[11px] capitalize text-[var(--mc-ink-muted)]">
            {task.assignee}
          </span>

          {task.due_date ? (
            <span className="ml-auto text-[11px] text-[var(--mc-ink-muted)]">
              {new Date(task.due_date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              })}
            </span>
          ) : (
            <ChevronRight size={16} className="ml-auto text-[var(--mc-ink-muted)]" />
          )}
        </div>
      </div>
    </div>
  );
}

// ── TaskCardSkeleton ──

export function TaskCardSkeleton() {
  return (
    <div className="rounded-[1rem] border border-black/[0.08] bg-black/5 p-[6px]">
      <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-3 shadow-sm">
        {/* Row 1 */}
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 animate-pulse rounded-full bg-white/10" />
          <div className="h-3 w-16 animate-pulse rounded bg-black/5" />
          <div className="ml-auto h-3 w-20 animate-pulse rounded bg-black/5" />
        </div>
        {/* Row 2 */}
        <div className="mt-2.5 h-4 w-3/4 animate-pulse rounded bg-black/5" />
        {/* Row 3 */}
        <div className="mt-2 h-3 w-full animate-pulse rounded bg-black/5" />
        {/* Row 4 */}
        <div className="mt-3 flex items-center gap-2">
          <div className="h-5 w-16 animate-pulse rounded-full bg-black/5" />
          <div className="h-5 w-10 animate-pulse rounded bg-black/5" />
          <div className="ml-auto h-3 w-12 animate-pulse rounded bg-black/5" />
        </div>
      </div>
    </div>
  );
}
