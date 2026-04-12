import React from 'react';
import { Bell, Menu } from 'lucide-react';
import { useDashboardStore } from '../../stores/dashboard';
import { useDataStore } from '../../stores/data';

const VIEW_LABELS: Record<string, string> = {
  'command-center': 'Command Center',
  tasks: 'Tasks',
  approvals: 'Approvals',
  files: 'Files',
  costs: 'Costs',
  revenue: 'Revenue',
  settings: 'Settings',
};

export function Topbar() {
  const { activeView, wsConnected, setActiveView, toggleSidebar } = useDashboardStore();
  const stats = useDataStore((s) => s.stats);

  // Budget color
  let budgetColor = 'var(--mc-green)';
  const pct = stats?.today_budget_pct_used ?? 0;
  if (pct >= 0.9) budgetColor = 'var(--mc-red)';
  else if (pct >= 0.7) budgetColor = 'var(--mc-yellow)';

  return (
    <header className="flex h-12 items-center gap-4 border-b border-[var(--mc-border)] bg-[var(--mc-bg)] px-4">
      {/* Mobile hamburger */}
      <button
        onClick={toggleSidebar}
        className="text-[var(--mc-ink-muted)] hover:text-[var(--mc-ink)] md:hidden"
      >
        <Menu size={20} />
      </button>

      {/* Current view */}
      <span className="font-medium text-[var(--mc-ink)]">
        {VIEW_LABELS[activeView] ?? activeView}
      </span>

      {/* Center: search (non-functional placeholder) */}
      <div className="mx-auto hidden max-w-xs flex-1 sm:block">
        <input
          type="text"
          placeholder="Search tasks..."
          className="w-full rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] px-3 py-1.5 text-sm text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:border-[var(--mc-accent)] focus:outline-none"
        />
      </div>

      {/* Right: status indicators */}
      <div className="ml-auto flex items-center gap-3">
        {/* Cost ticker */}
        {stats && (
          <button
            onClick={() => setActiveView('costs')}
            className="text-xs transition-colors hover:opacity-80"
            style={{ color: budgetColor }}
          >
            ${stats.today_cost_usd.toFixed(2)} today
          </button>
        )}

        {/* WS indicator */}
        <div
          className="h-2 w-2 rounded-full"
          style={{ backgroundColor: wsConnected ? 'var(--mc-green)' : 'var(--mc-red)' }}
          title={wsConnected ? 'WebSocket connected' : 'WebSocket disconnected'}
        />

        {/* Notifications bell */}
        <button
          onClick={() => setActiveView('approvals')}
          className="relative text-[var(--mc-ink-muted)] hover:text-[var(--mc-ink)]"
        >
          <Bell size={18} />
          {stats && stats.pending_approvals > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-[var(--mc-red)] text-[9px] font-medium text-white">
              {stats.pending_approvals > 9 ? '9+' : stats.pending_approvals}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
