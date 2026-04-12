import React, { useState, useEffect, useCallback } from 'react';
import type { TaskStatus, RiskTier, Assignee } from '../../lib/types';

export interface TaskFilterState {
  status: TaskStatus | '';
  risk_tier: RiskTier | '';
  assignee: Assignee | '';
  sort: 'newest' | 'oldest' | 'due_date' | 'priority';
  search: string;
}

interface TaskFiltersProps {
  onChange: (filters: TaskFilterState) => void;
}

const DEFAULT_FILTERS: TaskFilterState = {
  status: '',
  risk_tier: '',
  assignee: '',
  sort: 'newest',
  search: '',
};

export function TaskFilters({ onChange }: TaskFiltersProps) {
  const [filters, setFilters] = useState<TaskFilterState>(DEFAULT_FILTERS);

  const update = useCallback(
    (patch: Partial<TaskFilterState>) => {
      setFilters((prev) => {
        const next = { ...prev, ...patch };
        return next;
      });
    },
    [],
  );

  // Notify parent on change
  useEffect(() => {
    onChange(filters);
  }, [filters, onChange]);

  return (
    <div className="flex flex-wrap items-center gap-2 py-3">
      {/* Status select */}
      <select
        value={filters.status}
        onChange={(e) => update({ status: e.target.value as TaskStatus | '' })}
        className="rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] px-3 py-1.5 text-sm text-[var(--mc-ink)] focus:border-[var(--mc-accent)] focus:outline-none"
      >
        <option value="">All Status</option>
        <option value="open">Open</option>
        <option value="in_progress">In Progress</option>
        <option value="pending_review">Pending Review</option>
        <option value="completed">Completed</option>
        <option value="archived">Archived</option>
      </select>

      {/* Risk tier toggle group */}
      <div className="flex overflow-hidden rounded-lg border border-[var(--mc-border)]">
        {([
          { value: '', label: 'All' },
          { value: 'red', label: '🔴 Red' },
          { value: 'yellow', label: '🟡 Yellow' },
          { value: 'green', label: '🟢 Green' },
        ] as const).map((opt) => (
          <button
            key={opt.value}
            onClick={() => update({ risk_tier: opt.value as RiskTier | '' })}
            className={`px-3 py-1.5 text-xs transition-colors duration-150 ${
              filters.risk_tier === opt.value
                ? 'bg-[var(--mc-accent)]/15 text-[var(--mc-accent)]'
                : 'bg-transparent text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Assignee toggle */}
      <div className="flex overflow-hidden rounded-lg border border-[var(--mc-border)]">
        {([
          { value: '', label: 'All' },
          { value: 'kit', label: 'Kit' },
          { value: 'jeff', label: 'Jeff' },
        ] as const).map((opt) => (
          <button
            key={opt.value}
            onClick={() => update({ assignee: opt.value as Assignee | '' })}
            className={`px-3 py-1.5 text-xs transition-colors duration-150 ${
              filters.assignee === opt.value
                ? 'bg-[var(--mc-accent)]/15 text-[var(--mc-accent)]'
                : 'bg-transparent text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Sort select */}
      <select
        value={filters.sort}
        onChange={(e) => update({ sort: e.target.value as TaskFilterState['sort'] })}
        className="rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] px-3 py-1.5 text-sm text-[var(--mc-ink)] focus:border-[var(--mc-accent)] focus:outline-none"
      >
        <option value="newest">Newest</option>
        <option value="oldest">Oldest</option>
        <option value="due_date">Due Date</option>
        <option value="priority">Priority</option>
      </select>

      {/* Text search */}
      <input
        type="text"
        value={filters.search}
        onChange={(e) => update({ search: e.target.value })}
        placeholder="Filter by keyword..."
        className="ml-auto rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] px-3 py-1.5 text-sm text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:border-[var(--mc-accent)] focus:outline-none"
      />
    </div>
  );
}

export { DEFAULT_FILTERS };
