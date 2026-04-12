import React, { useEffect, useState, useCallback } from 'react';
import { Check, X, Clock, CheckCircle2, AlertCircle, Filter } from 'lucide-react';
import { useDataStore } from '../stores/data';
import { useDashboardStore } from '../stores/dashboard';
import { api } from '../lib/api';
import { Badge, Button } from '../components/ui';
import type { Approval } from '../lib/types';

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

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  pending: { label: 'Pending', color: 'var(--mc-yellow)', icon: <Clock size={12} /> },
  approved: { label: 'Approved', color: 'var(--mc-green)', icon: <CheckCircle2 size={12} /> },
  rejected: { label: 'Rejected', color: 'var(--mc-red)', icon: <X size={12} /> },
  expired: { label: 'Expired', color: 'var(--mc-ink-muted)', icon: <Clock size={12} /> },
};

const TYPE_LABELS: Record<string, string> = {
  content: 'Content',
  email: 'Email',
  social: 'Social',
  spend: 'Spend',
  code: 'Code',
  decision: 'Decision',
};

// ── Approval Card ──

function ApprovalCard({
  approval,
  onAction,
}: {
  approval: Approval;
  onAction: (id: string, action: 'approved' | 'rejected') => void;
}) {
  const [acting, setActing] = useState(false);
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [feedback, setFeedback] = useState('');

  const statusCfg = STATUS_CONFIG[approval.status] ?? STATUS_CONFIG.pending;

  const handleApprove = async () => {
    setActing(true);
    try {
      await api.post(`/approvals/${approval.id}/approve`);
      onAction(approval.id, 'approved');
    } catch (e) {
      console.error(e);
    } finally {
      setActing(false);
    }
  };

  const handleReject = async () => {
    if (!showRejectInput) {
      setShowRejectInput(true);
      return;
    }
    if (!feedback.trim()) return;
    setActing(true);
    try {
      await api.post(`/approvals/${approval.id}/reject`, { feedback });
      onAction(approval.id, 'rejected');
    } catch (e) {
      console.error(e);
    } finally {
      setActing(false);
      setShowRejectInput(false);
    }
  };

  return (
    <div className="rounded-[0.75rem] border border-black/[0.08] bg-black/[0.03] p-[4px] transition-all duration-200 hover:border-black/[0.14]"
      style={{ transitionTimingFunction: 'cubic-bezier(0.32, 0.72, 0, 1)' }}>
      <div className="rounded-[calc(0.75rem-4px)] bg-[var(--mc-surface)] p-4 shadow-sm">
        {/* Header */}
        <div className="flex items-start gap-3">
          {/* Risk dot */}
          <span className="mt-1.5 h-2.5 w-2.5 flex-shrink-0 rounded-full" style={{
            backgroundColor: approval.risk_tier === 'red' ? 'var(--mc-red)'
              : approval.risk_tier === 'yellow' ? 'var(--mc-yellow)'
              : 'var(--mc-green)',
          }} />

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-medium text-[var(--mc-ink)]">{approval.title}</span>
            </div>
            <div className="mt-1 flex items-center gap-2">
              <Badge>{TYPE_LABELS[approval.type] ?? approval.type}</Badge>
              <span className="text-[11px] text-[var(--mc-ink-muted)]">
                {approval.brand_name ?? approval.brand_slug}
              </span>
              <span className="text-[11px] text-[var(--mc-ink-muted)]">
                · {relativeTime(approval.created_at)}
              </span>
            </div>
          </div>

          {/* Status badge */}
          <div className="flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium"
            style={{
              backgroundColor: `color-mix(in oklch, ${statusCfg.color} 12%, transparent)`,
              color: statusCfg.color,
            }}>
            {statusCfg.icon}
            {statusCfg.label}
          </div>
        </div>

        {/* Preview */}
        {approval.preview && (
          <div className="mt-3 rounded-lg bg-black/[0.03] p-3 text-[13px] text-[var(--mc-ink)] leading-relaxed">
            {approval.preview}
          </div>
        )}

        {/* Agent reasoning */}
        {approval.agent_reasoning && (
          <div className="mt-2">
            <div className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)] mb-1">Kit's reasoning</div>
            <div className="text-[12px] text-[var(--mc-ink-muted)] leading-relaxed">
              {approval.agent_reasoning}
            </div>
          </div>
        )}

        {/* Feedback (if rejected) */}
        {approval.feedback && (
          <div className="mt-2 rounded-lg bg-[var(--mc-red)]/5 p-2.5 text-[12px] text-[var(--mc-red)]">
            <span className="font-medium">Feedback:</span> {approval.feedback}
          </div>
        )}

        {/* Actions */}
        {approval.status === 'pending' && (
          <div className="mt-4">
            {showRejectInput ? (
              <div className="flex flex-col gap-2">
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Why are you rejecting this?"
                  className="w-full rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] p-2.5 text-[13px] text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:border-[var(--mc-accent)] focus:outline-none resize-none"
                  rows={2}
                  autoFocus
                />
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="destructive" disabled={acting || !feedback.trim()} onClick={handleReject}>
                    <X size={12} /> Confirm Reject
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => { setShowRejectInput(false); setFeedback(''); }}>
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Button size="sm" variant="default" disabled={acting} onClick={handleApprove} className="flex items-center gap-1">
                  <Check size={12} /> Approve
                </Button>
                <Button size="sm" variant="destructive" disabled={acting} onClick={handleReject} className="flex items-center gap-1">
                  <X size={12} /> Reject
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Approvals Page ──

export default function ApprovalsPage() {
  const { approvals, approvalsTotal, loading, fetchApprovals } = useDataStore();
  const activeBrand = useDashboardStore((s) => s.activeBrand);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [removedIds, setRemovedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchApprovals({
      status: statusFilter === 'all' ? undefined : statusFilter as any,
      brand: activeBrand ?? undefined,
    });
  }, [activeBrand, statusFilter, fetchApprovals]);

  const handleAction = useCallback(
    (id: string) => {
      setRemovedIds((prev) => new Set(prev).add(id));
      fetchApprovals({
        status: statusFilter === 'all' ? undefined : statusFilter as any,
        brand: activeBrand ?? undefined,
      });
    },
    [fetchApprovals, activeBrand, statusFilter],
  );

  const visibleApprovals = approvals.filter((a) => !removedIds.has(a.id));
  const isLoading = loading.approvals;

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      {/* Header */}
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">Approvals</h1>
          <p className="mt-0.5 text-sm text-[var(--mc-ink-muted)]">
            Review and decide on items Kit needs your input for
          </p>
        </div>
        <span className="text-sm text-[var(--mc-ink-muted)]">
          {isLoading ? '…' : `${approvalsTotal} total`}
        </span>
      </div>

      {/* Filters */}
      <div className="mt-6 flex items-center gap-2">
        <Filter size={14} className="text-[var(--mc-ink-muted)]" />
        {['all', 'pending', 'approved', 'rejected'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`rounded-lg px-3 py-1.5 text-[12px] font-medium transition-colors duration-150 ${
              statusFilter === status
                ? 'bg-[var(--mc-accent)]/10 text-[var(--mc-accent)]'
                : 'text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]'
            }`}
          >
            {status === 'all' ? 'All' : STATUS_CONFIG[status]?.label ?? status}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="mt-6 flex flex-col gap-3">
        {isLoading && visibleApprovals.length === 0 ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-black/5" />
          ))
        ) : visibleApprovals.length === 0 ? (
          <div className="flex items-center gap-3 rounded-lg bg-black/[0.03] px-4 py-8">
            <CheckCircle2 size={20} className="text-[var(--mc-green)]/40" />
            <div>
              <div className="text-sm text-[var(--mc-ink)]">All clear</div>
              <div className="text-[12px] text-[var(--mc-ink-muted)]">
                {statusFilter === 'pending' ? 'No pending approvals' : `No ${statusFilter} approvals`}
              </div>
            </div>
          </div>
        ) : (
          visibleApprovals.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              onAction={handleAction}
            />
          ))
        )}
      </div>
    </div>
  );
}
