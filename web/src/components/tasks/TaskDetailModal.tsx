import React, { useState, useCallback } from 'react';
import { X, CheckCircle2, Clock, AlertCircle, User, Calendar, Tag, MessageSquare } from 'lucide-react';
import { api } from '../../lib/api';
import { Badge, Button } from '../ui';
import type { Task, TaskStatus } from '../../lib/types';

// ── Status transition map (must match server) ──

const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  open: ['in_progress', 'pending_review', 'archived'],
  in_progress: ['pending_review', 'completed', 'archived'],
  pending_review: ['approved', 'rejected', 'in_progress'],
  approved: ['completed'],
  rejected: ['in_progress', 'archived'],
  completed: ['archived'],
  archived: ['open'],
};

const STATUS_LABELS: Record<string, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  pending_review: 'Pending Review',
  approved: 'Approved',
  rejected: 'Rejected',
  completed: 'Completed',
  archived: 'Archived',
};

const RISK_COLORS = {
  green: 'var(--mc-green)',
  yellow: 'var(--mc-yellow)',
  red: 'var(--mc-red)',
} as const;

// ── Relative time ──

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

// ── Final statuses that auto-close the modal ──

const FINAL_STATUSES: TaskStatus[] = ['completed', 'approved', 'archived'];

// ── Modal ──

interface TaskDetailModalProps {
  task: Task;
  onClose: () => void;
  onUpdated?: (task: Task) => void;
}

export function TaskDetailModal({ task, onClose, onUpdated }: TaskDetailModalProps) {
  const [currentTask, setCurrentTask] = useState<Task>(task);
  const [transitioning, setTransitioning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleStatusChange = useCallback(
    async (newStatus: string) => {
      setTransitioning(newStatus);
      setError(null);
      try {
        const updated = await api.patch<Task>(`/tasks/${currentTask.id}/status`, {
          status: newStatus,
        });
        setCurrentTask(updated);
        onUpdated?.(updated);
        if (FINAL_STATUSES.includes(newStatus as TaskStatus)) {
          onClose();
        }
      } catch (err) {
        setError(`Failed to update status: ${(err as Error).message}`);
      } finally {
        setTransitioning(null);
      }
    },
    [currentTask, onUpdated, onClose],
  );

  const allowedNext = ALLOWED_TRANSITIONS[currentTask.status] ?? [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="mx-4 flex max-h-[85vh] w-full max-w-lg flex-col rounded-[1.25rem] border border-white/[0.08] bg-white/5 p-[6px] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── Header (sticky) ─────────────────────────── */}
        <div className="flex-none rounded-t-[calc(1.25rem-6px)] bg-[var(--mc-surface)] px-6 pt-6 pb-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <span
                className="mt-1.5 h-2.5 w-2.5 flex-shrink-0 rounded-full"
                style={{ backgroundColor: RISK_COLORS[currentTask.risk_tier] }}
              />
              <div>
                <h2 className="text-lg font-semibold leading-tight text-[var(--mc-ink)]">
                  {currentTask.title}
                </h2>
                <div className="mt-1 flex items-center gap-2">
                  <Badge className="text-[10px]">{STATUS_LABELS[currentTask.status]}</Badge>
                  <span className="text-[11px] text-[var(--mc-ink-muted)]">
                    {currentTask.brand_name ?? currentTask.brand_slug}
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-[var(--mc-ink-muted)] transition-colors hover:bg-white/5 hover:text-[var(--mc-ink)]"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* ── Scrollable body ─────────────────────────── */}
        <div className="min-h-0 flex-1 overflow-y-auto bg-[var(--mc-surface)] px-6 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
          {/* Metadata grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2 rounded-lg bg-white/[0.03] px-3 py-2">
              <User size={14} className="text-[var(--mc-ink-muted)]" />
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">Assignee</div>
                <div className="text-[13px] capitalize text-[var(--mc-ink)]">{currentTask.assignee}</div>
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-lg bg-white/[0.03] px-3 py-2">
              <AlertCircle size={14} className="text-[var(--mc-ink-muted)]" />
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">Priority</div>
                <div className="text-[13px] capitalize text-[var(--mc-ink)]">{currentTask.priority}</div>
              </div>
            </div>

            {currentTask.category && (
              <div className="flex items-center gap-2 rounded-lg bg-white/[0.03] px-3 py-2">
                <Tag size={14} className="text-[var(--mc-ink-muted)]" />
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">Category</div>
                  <div className="text-[13px] text-[var(--mc-ink)]">{currentTask.category}</div>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2 rounded-lg bg-white/[0.03] px-3 py-2">
              <Calendar size={14} className="text-[var(--mc-ink-muted)]" />
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">Created</div>
                <div className="text-[13px] text-[var(--mc-ink)]">{relativeTime(currentTask.created_at)}</div>
              </div>
            </div>
          </div>

          {/* Description */}
          {currentTask.description && (
            <div className="mt-4">
              <div className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">Description</div>
              <p className="mt-1 text-[13px] leading-relaxed text-[var(--mc-ink)]">{currentTask.description}</p>
            </div>
          )}

          {/* Agent note */}
          {currentTask.agent_note && (
            <div className="mt-4">
              <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
                <MessageSquare size={12} />
                Agent Note
              </div>
              <p className="mt-1 rounded-lg bg-white/[0.03] p-3 text-[13px] leading-relaxed text-[var(--mc-ink)]">
                {currentTask.agent_note}
              </p>
            </div>
          )}

          {/* User note */}
          {currentTask.user_note && (
            <div className="mt-4">
              <div className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">Your Note</div>
              <p className="mt-1 text-[13px] leading-relaxed text-[var(--mc-ink)]">{currentTask.user_note}</p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4 rounded-lg border border-[var(--mc-red)]/30 bg-[var(--mc-red)]/10 px-3 py-2 text-[12px] text-[var(--mc-red)]">
              {error}
            </div>
          )}

          {/* Completed at */}
          {currentTask.completed_at && (
            <div className="mt-3 flex items-center gap-1.5 text-[11px] text-[var(--mc-green)]">
              <CheckCircle2 size={12} />
              Completed {relativeTime(currentTask.completed_at)}
            </div>
          )}
        </div>

        {/* ── Actions (sticky bottom) ─────────────────── */}
        <div className="flex-none rounded-b-[calc(1.25rem-6px)] border-t border-white/[0.06] bg-[var(--mc-surface)] px-6 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
          {allowedNext.length > 0 && (
            <div>
              <div className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">Move to</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {allowedNext.map((status) => (
                  <Button
                    key={status}
                    size="sm"
                    variant={status === 'completed' || status === 'approved' ? 'default' : (status === 'rejected' ? 'destructive' : 'ghost')}
                    disabled={transitioning !== null}
                    onClick={() => handleStatusChange(status)}
                  >
                    {transitioning === status ? '…' : STATUS_LABELS[status]}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}