import React, { useEffect, useState } from 'react';
import { DollarSign, TrendingUp, AlertTriangle, Zap, BarChart3 } from 'lucide-react';
import { useDataStore } from '../stores/data';
import { api } from '../lib/api';

interface TodayCosts {
  date: string;
  total_cost: number;
  budget_limit: number;
  budget_remaining: number;
  budget_pct_used: number;
  by_brand: Array<{ brand_id: string; brand_name: string; cost_usd: number; task_count: number }>;
  by_model: Array<{ model: string; cost_usd: number; tokens_in: number; tokens_out: number }>;
}

export default function CostsPage() {
  const [todayCosts, setTodayCosts] = useState<TodayCosts | null>(null);
  const [loading, setLoading] = useState(true);
  const stats = useDataStore((s) => s.stats);

  useEffect(() => {
    setLoading(true);
    api.get<TodayCosts>('/costs/today')
      .then(setTodayCosts)
      .catch(() => setTodayCosts(null))
      .finally(() => setLoading(false));
  }, []);

  const budgetPct = todayCosts?.budget_pct_used ?? stats?.today_budget_pct_used ?? 0;
  const spent = todayCosts?.total_cost ?? stats?.today_cost_usd ?? 0;
  const budget = todayCosts?.budget_limit ?? stats?.today_budget_limit ?? 2.00;

  let budgetColor = 'var(--mc-green)';
  if (budgetPct >= 0.9) budgetColor = 'var(--mc-red)';
  else if (budgetPct >= 0.7) budgetColor = 'var(--mc-yellow)';

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">Costs</h1>
      <p className="mt-0.5 text-sm text-[var(--mc-ink-muted)]">
        Track API spend by brand and model
      </p>

      {/* Budget overview */}
      <div className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px] lg:col-span-2">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <div className="flex items-baseline justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--mc-ink-muted)]">Today's Spend</div>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-3xl font-bold" style={{ color: budgetColor }}>
                    ${spent.toFixed(2)}
                  </span>
                  <span className="text-sm text-[var(--mc-ink-muted)]">/ ${budget.toFixed(2)}</span>
                </div>
              </div>
              {budgetPct >= 0.8 && (
                <div className="flex items-center gap-1 rounded-full px-2 py-1 text-[11px] font-medium"
                  style={{ backgroundColor: `color-mix(in oklch, ${budgetColor} 12%, transparent)`, color: budgetColor }}>
                  <AlertTriangle size={12} />
                  {budgetPct >= 0.9 ? 'Budget critical' : 'Budget warning'}
                </div>
              )}
            </div>

            {/* Progress bar */}
            <div className="mt-4 h-2 rounded-full bg-black/10 overflow-hidden">
              <div className="h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(budgetPct * 100, 100)}%`, backgroundColor: budgetColor }} />
            </div>
            <div className="mt-1 flex justify-between text-[11px] text-[var(--mc-ink-muted)]">
              <span>{(budgetPct * 100).toFixed(1)}% used</span>
              <span>${(budget - spent).toFixed(2)} remaining</span>
            </div>
          </div>
        </div>

        {/* Quick stats */}
        <div className="flex flex-col gap-4">
          <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
            <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-4 shadow-sm">
              <div className="flex items-center gap-2 text-[var(--mc-ink-muted)]">
                <Zap size={14} />
                <span className="text-[10px] uppercase tracking-wider">Tokens Today</span>
              </div>
              <div className="mt-2 text-xl font-bold text-[var(--mc-ink)]">
                {todayCosts?.by_model.reduce((sum, m) => sum + m.tokens_in + m.tokens_out, 0).toLocaleString() ?? '0'}
              </div>
            </div>
          </div>
          <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
            <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-4 shadow-sm">
              <div className="flex items-center gap-2 text-[var(--mc-ink-muted)]">
                <BarChart3 size={14} />
                <span className="text-[10px] uppercase tracking-wider">Models Used</span>
              </div>
              <div className="mt-2 text-xl font-bold text-[var(--mc-ink)]">
                {todayCosts?.by_model.length ?? 0}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* By Brand */}
      <div className="mt-8">
        <h2 className="text-sm font-medium text-[var(--mc-ink)] mb-3">By Brand</h2>
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-4 shadow-sm">
            {loading ? (
              <div className="h-24 animate-pulse rounded-lg bg-black/5" />
            ) : todayCosts?.by_brand.length === 0 || !todayCosts ? (
              <div className="flex items-center gap-3 rounded-lg bg-black/[0.03] px-4 py-6">
                <DollarSign size={18} className="text-[var(--mc-ink-muted)]/40" />
                <span className="text-[12px] text-[var(--mc-ink-muted)]/60">No costs logged today — Kit tracks spend as tasks complete</span>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {todayCosts.by_brand.map((b) => (
                  <div key={b.brand_id} className="flex items-center gap-3 rounded-lg bg-black/[0.03] px-4 py-2.5">
                    <span className="text-[13px] font-medium text-[var(--mc-ink)] flex-1">{b.brand_name}</span>
                    <span className="text-[12px] text-[var(--mc-ink-muted)]">{b.task_count} tasks</span>
                    <span className="text-[13px] font-medium text-[var(--mc-ink)]">${b.cost_usd.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* By Model */}
      <div className="mt-6">
        <h2 className="text-sm font-medium text-[var(--mc-ink)] mb-3">By Model</h2>
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-4 shadow-sm">
            {loading ? (
              <div className="h-24 animate-pulse rounded-lg bg-black/5" />
            ) : todayCosts?.by_model.length === 0 || !todayCosts ? (
              <div className="flex items-center gap-3 rounded-lg bg-black/[0.03] px-4 py-6">
                <TrendingUp size={18} className="text-[var(--mc-ink-muted)]/40" />
                <span className="text-[12px] text-[var(--mc-ink-muted)]/60">No model usage recorded today</span>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {todayCosts.by_model.map((m) => (
                  <div key={m.model} className="flex items-center gap-3 rounded-lg bg-black/[0.03] px-4 py-2.5">
                    <span className="text-[13px] font-mono text-[var(--mc-ink)] flex-1">{m.model}</span>
                    <span className="text-[11px] text-[var(--mc-ink-muted)]">
                      {(m.tokens_in + m.tokens_out).toLocaleString()} tok
                    </span>
                    <span className="text-[13px] font-medium text-[var(--mc-ink)]">${m.cost_usd.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
