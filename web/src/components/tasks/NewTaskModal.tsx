import React, { useState } from 'react';
import { X, Plus } from 'lucide-react';
import { api } from '../../lib/api';
import { Button } from '../ui';
import type { Priority, RiskTier, Assignee, Task } from '../../lib/types';

// ── Brand options ──

const BRANDS = [
  { slug: 'agentictrust', name: 'AgenticTrust' },
  { slug: 'trustoffice', name: 'TrustOffice' },
  { slug: 'wingpoint', name: 'WingPoint' },
  { slug: 'truejoybirthing', name: 'True Joy Birthing' },
  { slug: 'general', name: 'General' },
];

const PRIORITIES: Priority[] = ['low', 'normal', 'high', 'critical'];
const RISK_TIERS: RiskTier[] = ['green', 'yellow', 'red'];
const ASSIGNEES: Assignee[] = ['jeff', 'kit', 'unassigned'];

const RISK_COLORS = {
  green: 'var(--mc-green)',
  yellow: 'var(--mc-yellow)',
  red: 'var(--mc-red)',
} as const;

// ── Modal ──

interface NewTaskModalProps {
  onClose: () => void;
  onCreated?: (task: Task) => void;
}

export function NewTaskModal({ onClose, onCreated }: NewTaskModalProps) {
  const [title, setTitle] = useState('');
  const [brandSlug, setBrandSlug] = useState('general');
  const [priority, setPriority] = useState<Priority>('normal');
  const [riskTier, setRiskTier] = useState<RiskTier>('yellow');
  const [assignee, setAssignee] = useState<Assignee>('jeff');
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [userNote, setUserNote] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      const created = await api.post<Task>('/tasks', {
        title: title.trim(),
        brand_slug: brandSlug,
        priority,
        risk_tier: riskTier,
        assignee,
        category: category.trim() || undefined,
        description: description.trim() || undefined,
        user_note: userNote.trim() || undefined,
        due_date: dueDate || undefined,
      });

      onCreated?.(created);
      onClose();
    } catch (err) {
      setError((err as Error).message || 'Failed to create task');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="mx-4 flex max-h-[85vh] w-full max-w-lg flex-col rounded-[1.25rem] border border-white/[0.08] bg-white/5 p-[6px] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex-none rounded-t-[calc(1.25rem-6px)] bg-[var(--mc-surface)] px-6 pt-6 pb-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Plus size={18} className="text-[var(--mc-accent)]" />
              <h2 className="text-lg font-semibold text-[var(--mc-ink)]">New Task</h2>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-[var(--mc-ink-muted)] transition-colors hover:bg-white/5 hover:text-[var(--mc-ink)]"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Scrollable form */}
        <form id="new-task-form" onSubmit={handleSubmit} className="min-h-0 flex-1 overflow-y-auto bg-[var(--mc-surface)] px-6 py-4">
          {/* Title */}
          <div className="mb-4">
            <label className="mb-1.5 block text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What needs to be done?"
              className="w-full rounded-lg border border-white/[0.08] bg-black/5 px-3 py-2 text-[14px] text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)]/50 focus:border-[var(--mc-accent)] focus:outline-none focus:ring-1 focus:ring-[var(--mc-accent)]"
              autoFocus
            />
          </div>

          {/* Brand + Priority row */}
          <div className="mb-4 grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
                Brand
              </label>
              <select
                value={brandSlug}
                onChange={(e) => setBrandSlug(e.target.value)}
                className="w-full rounded-lg border border-white/[0.08] bg-black/5 px-3 py-2 text-[13px] text-[var(--mc-ink)] focus:border-[var(--mc-accent)] focus:outline-none"
              >
                {BRANDS.map((b) => (
                  <option key={b.slug} value={b.slug}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as Priority)}
                className="w-full rounded-lg border border-white/[0.08] bg-black/5 px-3 py-2 text-[13px] text-[var(--mc-ink)] focus:border-[var(--mc-accent)] focus:outline-none"
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Risk Tier + Assignee row */}
          <div className="mb-4 grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
                Risk Tier
              </label>
              <div className="flex gap-2">
                {RISK_TIERS.map((tier) => (
                  <button
                    key={tier}
                    type="button"
                    onClick={() => setRiskTier(tier)}
                    className={`flex-1 rounded-lg border px-3 py-2 text-[12px] font-medium capitalize transition-colors ${
                      riskTier === tier
                        ? 'border-transparent shadow-sm'
                        : 'border-white/[0.08] bg-black/5 text-[var(--mc-ink-muted)]'
                    }`}
                    style={
                      riskTier === tier
                        ? { backgroundColor: RISK_COLORS[tier], color: '#fff' }
                        : {}
                    }
                  >
                    {tier}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
                Assignee
              </label>
              <select
                value={assignee}
                onChange={(e) => setAssignee(e.target.value as Assignee)}
                className="w-full rounded-lg border border-white/[0.08] bg-black/5 px-3 py-2 text-[13px] text-[var(--mc-ink)] focus:border-[var(--mc-accent)] focus:outline-none"
              >
                {ASSIGNEES.map((a) => (
                  <option key={a} value={a}>
                    {a.charAt(0).toUpperCase() + a.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Category */}
          <div className="mb-4">
            <label className="mb-1.5 block text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
              Category
            </label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g., outreach, content, bug, feature"
              className="w-full rounded-lg border border-white/[0.08] bg-black/5 px-3 py-2 text-[14px] text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)]/50 focus:border-[var(--mc-accent)] focus:outline-none focus:ring-1 focus:ring-[var(--mc-accent)]"
            />
          </div>

          {/* Description */}
          <div className="mb-4">
            <label className="mb-1.5 block text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's the context?"
              rows={3}
              className="w-full rounded-lg border border-white/[0.08] bg-black/5 px-3 py-2 text-[14px] text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)]/50 focus:border-[var(--mc-accent)] focus:outline-none focus:ring-1 focus:ring-[var(--mc-accent)] resize-none"
            />
          </div>

          {/* Note to Kit */}
          <div className="mb-4">
            <label className="mb-1.5 block text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
              Note to Kit
            </label>
            <textarea
              value={userNote}
              onChange={(e) => setUserNote(e.target.value)}
              placeholder="Any specific instructions for Kit?"
              rows={2}
              className="w-full rounded-lg border border-white/[0.08] bg-black/5 px-3 py-2 text-[14px] text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)]/50 focus:border-[var(--mc-accent)] focus:outline-none focus:ring-1 focus:ring-[var(--mc-accent)] resize-none"
            />
          </div>

          {/* Due date */}
          <div className="mb-4">
            <label className="mb-1.5 block text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
              Due Date (optional)
            </label>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full rounded-lg border border-white/[0.08] bg-black/5 px-3 py-2 text-[14px] text-[var(--mc-ink)] focus:border-[var(--mc-accent)] focus:outline-none"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 rounded-lg border border-[var(--mc-red)]/30 bg-[var(--mc-red)]/10 px-3 py-2 text-[12px] text-[var(--mc-red)]">
              {error}
            </div>
          )}
        </form>

        {/* Footer — inside form so submit works from keyboard too */}
        <div className="flex-none rounded-b-[calc(1.25rem-6px)] border-t border-white/[0.06] bg-[var(--mc-surface)] px-6 py-4">
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={onClose} disabled={submitting} type="button">
              Cancel
            </Button>
            <Button
              type="submit"
              form="new-task-form"
              disabled={!title.trim() || submitting}
            >
              {submitting ? 'Creating…' : 'Create Task'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}