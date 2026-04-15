import { useEffect, useState } from 'react';
import { useDataStore } from '../../stores/data';
import { useDashboardStore } from '../../stores/dashboard';
import { api } from '../../lib/api';
import type { CostToday } from '../../lib/types';

/**
 * BudgetBar — a persistent, glanceable cost indicator that appears on every view.
 * Sits below the Topbar in the Layout, always visible.
 * Shows today's spend vs. $2/day budget with color-coded status.
 */
export function BudgetBar() {
  const stats = useDataStore((s) => s.stats);
  const activeView = useDashboardStore((s) => s.activeView);
  const setActiveView = useDashboardStore((s) => s.setActiveView);
  const [todayCosts, setTodayCosts] = useState<CostToday | null>(null);

  useEffect(() => {
    api.get<CostToday>('/costs/today')
      .then(setTodayCosts)
      .catch(() => setTodayCosts(null));
  }, []);

  // Prefer detailed costs data, fall back to stats
  const spent = todayCosts?.total_cost ?? stats?.today_cost_usd ?? 0;
  const budget = todayCosts?.budget_limit ?? stats?.today_budget_limit ?? 2.0;
  const pct = todayCosts?.budget_pct_used ?? stats?.today_budget_pct_used ?? 0;
  const pctFraction = pct / 100;

  // Status thresholds: green < $1.50, yellow $1.50–$1.99, red ≥ $2.00
  let statusColor = 'var(--mc-green)';
  let statusLabel = 'OK';
  if (spent >= budget) {
    statusColor = 'var(--mc-red)';
    statusLabel = 'OVER';
  } else if (spent >= 1.50) {
    statusColor = 'var(--mc-yellow)';
    statusLabel = 'WARN';
  }

  // Don't show on the Costs page (it already has a full budget display)
  if (activeView === 'costs') return null;

  return (
    <button
      onClick={() => setActiveView('costs')}
      className="flex items-center gap-3 border-b border-[var(--mc-border)] bg-[var(--mc-surface)] px-4 py-1.5 text-left transition-colors hover:bg-[var(--mc-surface)]/80"
      title="Click to view detailed costs"
    >
      {/* Progress bar (tiny, left side) */}
      <div className="h-1.5 w-24 flex-shrink-0 rounded-full bg-black/10 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${Math.min(pctFraction * 100, 100)}%`,
            backgroundColor: statusColor,
          }}
        />
      </div>

      {/* Text */}
      <span
        className="text-[12px] font-medium tabular-nums"
        style={{ color: statusColor }}
      >
        ${spent.toFixed(2)}
      </span>
      <span className="text-[11px] text-[var(--mc-ink-muted)]">
        / ${budget.toFixed(2)}
      </span>

      {/* Status badge */}
      <span
        className="rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider"
        style={{
          backgroundColor: `color-mix(in oklch, ${statusColor} 15%, transparent)`,
          color: statusColor,
        }}
      >
        {statusLabel}
      </span>
    </button>
  );
}