import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Check, X, Clock, CheckCircle2, AlertCircle, Filter, CheckSquare, Square, Trash2, Edit3 } from 'lucide-react';
import { useDataStore } from '../stores/data';
import { useDashboardStore } from '../stores/dashboard';
import { api } from '../lib/api';
import { Badge, Button } from '../components/ui';
import type { Approval } from '../lib/types';

// ── Helpers ──

function relativeTime(dateStr: string): string {
  const now = Date.now();
  const normalized = dateStr.includes('Z') || dateStr.includes('+') ? dateStr : dateStr + 'Z';
  const then = new Date(normalized).getTime();
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

// ── Preview Renderers ──

function EmailPreview({ preview, metadata }: { preview: string; metadata?: Record<string, unknown> }) {
  const subject = metadata?.subject as string | undefined;
  const to = metadata?.to as string | undefined;

  return (
    <div className="rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] overflow-hidden">
      {/* Email header */}
      <div className="border-b border-[var(--mc-border)] bg-black/[0.02] px-3 py-2">
        {subject && (
          <div className="text-[12px]"><span className="text-[var(--mc-ink-muted)]">Subject:</span> <span className="font-medium text-[var(--mc-ink)]">{subject}</span></div>
        )}
        {to && (
          <div className="text-[11px] text-[var(--mc-ink-muted)]">To: {to}</div>
        )}
      </div>
      {/* Email body */}
      <div className="p-3 text-[13px] text-[var(--mc-ink)] leading-relaxed whitespace-pre-wrap">
        {preview}
      </div>
    </div>
  );
}

function ContentPreview({ preview }: { preview: string }) {
  return (
    <div className="rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] p-3 text-[13px] text-[var(--mc-ink)] leading-relaxed">
      {preview}
    </div>
  );
}

function CodePreview({ preview }: { preview: string }) {
  return (
    <pre className="rounded-lg border border-[var(--mc-border)] bg-[#1e1e1e] p-3 text-[12px] text-green-300 overflow-x-auto font-mono leading-relaxed">
      {preview}
    </pre>
  );
}

function SpendPreview({ preview, metadata }: { preview: string; metadata?: Record<string, unknown> }) {
  const amount = metadata?.amount as number | undefined;
  const service = metadata?.service as string | undefined;

  return (
    <div className="rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] p-3">
      {amount !== undefined && (
        <div className="mb-2 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-[var(--mc-ink)]">${amount.toFixed(2)}</span>
          <span className="text-[12px] text-[var(--mc-ink-muted)]">/month</span>
          {service && <Badge>{service}</Badge>}
        </div>
      )}
      <div className="text-[13px] text-[var(--mc-ink)] leading-relaxed">{preview}</div>
    </div>
  );
}

function GenericPreview({ preview }: { preview: string }) {
  return (
    <div className="rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] p-3 text-[13px] text-[var(--mc-ink)] leading-relaxed">
      {preview}
    </div>
  );
}

function ApprovalPreview({ approval }: { approval: Approval }) {
  const metadata = (approval.metadata ?? {}) as Record<string, unknown>;

  switch (approval.type) {
    case 'email': return <EmailPreview preview={approval.preview} metadata={metadata} />;
    case 'content': return <ContentPreview preview={approval.preview} />;
    case 'code': return <CodePreview preview={approval.preview} />;
    case 'spend': return <SpendPreview preview={approval.preview} metadata={metadata} />;
    default: return <GenericPreview preview={approval.preview} />;
  }
}

// ── Approval Card ──

function ApprovalCard({
  approval,
  selected,
  onSelect,
  onAction,
}: {
  approval: Approval;
  selected: boolean;
  onSelect: (id: string) => void;
  onAction: (id: string, action: 'approved' | 'rejected' | 'edit_approved', edits?: string) => void;
}) {
  const [acting, setActing] = useState(false);
  const [mode, setMode] = useState<'view' | 'reject' | 'edit'>('view');
  const [feedback, setFeedback] = useState('');
  const [editText, setEditText] = useState('');

  const statusCfg = STATUS_CONFIG[approval.status] ?? STATUS_CONFIG.pending;
  const isPending = approval.status === 'pending';

  const handleApprove = async () => {
    setActing(true);
    try {
      await api.post(`/approvals/${approval.id}/approve`);
      onAction(approval.id, 'approved');
    } catch (e) { console.error(e); } finally { setActing(false); }
  };

  const handleReject = async () => {
    if (mode !== 'reject') { setMode('reject'); return; }
    if (!feedback.trim()) return;
    setActing(true);
    try {
      await api.post(`/approvals/${approval.id}/reject`, { feedback });
      onAction(approval.id, 'rejected');
    } catch (e) { console.error(e); } finally { setActing(false); setMode('view'); }
  };

  const handleEditApprove = async () => {
    if (mode !== 'edit') {
      setMode('edit');
      setEditText(approval.preview);
      return;
    }
    if (!editText.trim()) return;
    setActing(true);
    try {
      await api.post(`/approvals/${approval.id}/edit-approve`, { edits: editText });
      onAction(approval.id, 'edit_approved');
    } catch (e) { console.error(e); } finally { setActing(false); setMode('view'); }
  };

  return (
    <div className="rounded-[0.75rem] border border-black/[0.08] bg-black/[0.03] p-[4px] transition-all duration-200 hover:border-black/[0.14]"
      style={{ transitionTimingFunction: 'cubic-bezier(0.32, 0.72, 0, 1)' }}>
      <div className="rounded-[calc(0.75rem-4px)] bg-[var(--mc-surface)] p-4 shadow-sm">
        {/* Header */}
        <div className="flex items-start gap-3">
          {/* Checkbox */}
          {isPending && (
            <button onClick={() => onSelect(approval.id)} className="mt-1 text-[var(--mc-ink-muted)] hover:text-[var(--mc-accent)]">
              {selected ? <CheckSquare size={16} className="text-[var(--mc-accent)]" /> : <Square size={16} />}
            </button>
          )}

          {/* Risk dot */}
          <span className="mt-1.5 h-2.5 w-2.5 flex-shrink-0 rounded-full" style={{
            backgroundColor: approval.risk_tier === 'red' ? 'var(--mc-red)'
              : approval.risk_tier === 'yellow' ? 'var(--mc-yellow)'
              : 'var(--mc-green)',
          }} />

          <div className="flex-1 min-w-0">
            <div className="text-[13px] font-medium text-[var(--mc-ink)]">{approval.title}</div>
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

        {/* Preview payload */}
        {approval.preview && (
          <div className="mt-3">
            <ApprovalPreview approval={approval} />
          </div>
        )}

        {/* Agent reasoning */}
        {approval.agent_reasoning && (
          <div className="mt-2">
            <div className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)] mb-1">Kit's reasoning</div>
            <div className="text-[12px] text-[var(--mc-ink-muted)] leading-relaxed">{approval.agent_reasoning}</div>
          </div>
        )}

        {/* Feedback (if rejected) */}
        {approval.feedback && (
          <div className="mt-2 rounded-lg bg-[var(--mc-red)]/5 p-2.5 text-[12px] text-[var(--mc-red)]">
            <span className="font-medium">Feedback:</span> {approval.feedback}
          </div>
        )}

        {/* Actions */}
        {isPending && (
          <div className="mt-4">
            {mode === 'reject' ? (
              <div className="flex flex-col gap-2">
                <textarea value={feedback} onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Why are you rejecting this?"
                  className="w-full rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] p-2.5 text-[13px] text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:border-[var(--mc-accent)] focus:outline-none resize-none"
                  rows={2} autoFocus />
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="destructive" disabled={acting || !feedback.trim()} onClick={handleReject}>
                    <X size={12} /> Confirm Reject
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => { setMode('view'); setFeedback(''); }}>Cancel</Button>
                </div>
              </div>
            ) : mode === 'edit' ? (
              <div className="flex flex-col gap-2">
                <textarea value={editText} onChange={(e) => setEditText(e.target.value)}
                  placeholder="Edit the content before approving..."
                  className="w-full rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] p-2.5 text-[13px] text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:border-[var(--mc-accent)] focus:outline-none resize-none font-mono"
                  rows={4} autoFocus />
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="default" disabled={acting || !editText.trim()} onClick={handleEditApprove}>
                    <Check size={12} /> Save & Approve
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => { setMode('view'); setEditText(''); }}>Cancel</Button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Button size="sm" variant="default" disabled={acting} onClick={handleApprove} className="flex items-center gap-1">
                  <Check size={12} /> Approve
                </Button>
                <Button size="sm" variant="ghost" disabled={acting} onClick={handleEditApprove} className="flex items-center gap-1">
                  <Edit3 size={12} /> Edit & Approve
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

// ── Bulk Actions Bar ──

function BulkActionsBar({
  count,
  onApproveAll,
  onDiscardAll,
  onClear,
}: {
  count: number;
  onApproveAll: () => void;
  onDiscardAll: () => void;
  onClear: () => void;
}) {
  if (count === 0) return null;

  return (
    <div className="sticky top-0 z-10 flex items-center gap-3 rounded-lg border border-[var(--mc-accent)]/20 bg-[var(--mc-accent)]/5 px-4 py-2.5">
      <span className="text-[13px] font-medium text-[var(--mc-accent)]">{count} selected</span>
      <div className="flex items-center gap-2 ml-auto">
        <Button size="sm" variant="default" onClick={onApproveAll} className="flex items-center gap-1">
          <Check size={12} /> Approve All
        </Button>
        <Button size="sm" variant="destructive" onClick={onDiscardAll} className="flex items-center gap-1">
          <Trash2 size={12} /> Discard All
        </Button>
        <Button size="sm" variant="ghost" onClick={onClear}>Clear</Button>
      </div>
    </div>
  );
}

// ── Main Approvals Page ──

export default function ApprovalsPage() {
  const { approvals, approvalsTotal, loading, fetchApprovals } = useDataStore();
  const activeBrand = useDashboardStore((s) => s.activeBrand);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchApprovals({
      status: statusFilter === 'all' ? undefined : (statusFilter as any),
      brand: activeBrand ?? undefined,
    });
    setSelectedIds(new Set()); // clear selection on filter change
  }, [activeBrand, statusFilter, fetchApprovals]);

  const handleAction = useCallback(
    (id: string) => {
      setSelectedIds((prev) => { const next = new Set(prev); next.delete(id); return next; });
      fetchApprovals({
        status: statusFilter === 'all' ? undefined : (statusFilter as any),
        brand: activeBrand ?? undefined,
      });
    },
    [fetchApprovals, activeBrand, statusFilter],
  );

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const handleBulkApprove = async () => {
    const ids = Array.from(selectedIds);
    try {
      await api.post('/approvals/bulk', { ids, action: 'approve' });
    } catch (e) { console.error(e); }
    setSelectedIds(new Set());
    fetchApprovals({ status: statusFilter === 'all' ? undefined : (statusFilter as any), brand: activeBrand ?? undefined });
  };

  const handleBulkDiscard = async () => {
    const ids = Array.from(selectedIds);
    try {
      await api.post('/approvals/bulk', { ids, action: 'dismiss' });
    } catch (e) { console.error(e); }
    setSelectedIds(new Set());
    fetchApprovals({ status: statusFilter === 'all' ? undefined : (statusFilter as any), brand: activeBrand ?? undefined });
  };

  const pendingApprovals = useMemo(() =>
    approvals.filter((a) => a.status === 'pending'),
    [approvals]
  );

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
          <button key={status} onClick={() => setStatusFilter(status)}
            className={`rounded-lg px-3 py-1.5 text-[12px] font-medium transition-colors duration-150 ${
              statusFilter === status
                ? 'bg-[var(--mc-accent)]/10 text-[var(--mc-accent)]'
                : 'text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]'
            }`}>
            {status === 'all' ? 'All' : STATUS_CONFIG[status]?.label ?? status}
          </button>
        ))}

        {/* Select all (pending only) */}
        {statusFilter === 'pending' && pendingApprovals.length > 0 && (
          <button
            onClick={() => {
              if (selectedIds.size === pendingApprovals.length) {
                setSelectedIds(new Set());
              } else {
                setSelectedIds(new Set(pendingApprovals.map((a) => a.id)));
              }
            }}
            className="ml-auto text-[12px] text-[var(--mc-ink-muted)] hover:text-[var(--mc-accent)]">
            {selectedIds.size === pendingApprovals.length ? 'Deselect All' : 'Select All'}
          </button>
        )}
      </div>

      {/* Bulk actions */}
      <BulkActionsBar
        count={selectedIds.size}
        onApproveAll={handleBulkApprove}
        onDiscardAll={handleBulkDiscard}
        onClear={() => setSelectedIds(new Set())}
      />

      {/* List */}
      <div className="mt-4 flex flex-col gap-3">
        {isLoading && approvals.length === 0 ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-xl bg-black/5" />
          ))
        ) : approvals.length === 0 ? (
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
          approvals.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              selected={selectedIds.has(approval.id)}
              onSelect={toggleSelect}
              onAction={handleAction}
            />
          ))
        )}
      </div>
    </div>
  );
}
