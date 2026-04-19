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

interface DailyCost {
  date: string;
  cost_usd: number;
  task_count: number;
}

const DAYS = 30;

// ── Bar chart for 30-day spend ──

function CostChart({ data, budgetLimit }: { data: DailyCost[]; budgetLimit: number }) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center py-10 text-[var(--mc-ink-muted)]">
        <BarChart3 size={18} className="mr-2 opacity-40" />
        <span className="text-[12px]">No cost data for the last {DAYS} days</span>
      </div>
    );
  }

  const maxCost = Math.max(budgetLimit * 1.2, ...data.map((d) => d.cost_usd), 0.01);

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr + 'T12:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const formatDateShort = (dateStr: string) => {
    const d = new Date(dateStr + 'T12:00:00');
    return d.getDate().toString();
  };

  return (
    <div className="w-full">
      <div className="relative flex" style={{ height: 200 }}>
        {/* Y-axis */}
        <div className="flex flex-col justify-between py-1 pr-2 text-[10px] text-[var(--mc-ink-muted)]" style={{ width: 36 }}>
          <span>${maxCost.toFixed(2)}</span>
          <span>${(maxCost * 0.75).toFixed(2)}</span>
          <span>${(maxCost * 0.5).toFixed(2)}</span>
          <span>${(maxCost * 0.25).toFixed(2)}</span>
          <span>$0</span>
        </div>

        {/* Chart area */}
        <div className="relative flex-1 flex items-end" style={{ gap: '1px' }}>
          {/* Budget line */}
          {budgetLimit > 0 && budgetLimit <= maxCost && (
            <div
              className="absolute left-0 right-0 border-t border-dashed border-[var(--mc-yellow)]/60 z-10"
              style={{ bottom: `${(budgetLimit / maxCost) * 100}%` }}
            >
              <span className="absolute -top-3 right-0 text-[9px] text-[var(--mc-yellow)]">
                ${budgetLimit.toFixed(2)}
              </span>
            </div>
          )}

          {/* Grid lines */}
          {[0.25, 0.5, 0.75].map((pct) => (
            <div
              key={pct}
              className="absolute left-0 right-0 border-t border-black/[0.04]"
              style={{ bottom: `${pct * 100}%` }}
            />
          ))}

          {data.map((d, i) => {
            const heightPct = maxCost > 0 ? (d.cost_usd / maxCost) * 100 : 0;
            const isToday = i === data.length - 1;
            const overBudget = budgetLimit > 0 && d.cost_usd > budgetLimit;
            const barColor = overBudget
              ? 'var(--mc-red)'
              : isToday
              ? 'var(--mc-accent)'
              : 'color-mix(in oklch, var(--mc-accent) 55%, transparent)';

            return (
              <div
                key={d.date}
                className="group relative flex-1 flex flex-col items-center justify-end cursor-default"
                style={{ height: '100%' }}
              >
                {/* Tooltip on hover */}
                <div className="absolute bottom-full mb-1 hidden group-hover:block z-20 whitespace-nowrap rounded bg-[var(--mc-ink)] px-2 py-1 text-[10px] text-white shadow-lg">
                  {formatDate(d.date)}: ${d.cost_usd.toFixed(2)}
                </div>
                {/* Today label */}
                {isToday && d.cost_usd > 0 && (
                  <span className="text-[8px] font-medium text-[var(--mc-accent)] mb-0.5">
                    ${d.cost_usd.toFixed(2)}
                  </span>
                )}
                <div
                  className="w-full rounded-t transition-all duration-200 min-h-[1px]"
                  style={{
                    height: `${Math.max(heightPct, 0.4)}%`,
                    backgroundColor: barColor,
                  }}
                />
              </div>
            );
          })}
        </div>
      </div>

      {/* X-axis labels */}
      <div className="flex ml-[36px]" style={{ marginTop: 4 }}>
        {data.map((d, i) => {
          // With 30 days: show date number, and month label on the 1st
          const dayNum = formatDateShort(d.date);
          const isWeekStart = new Date(d.date + 'T12:00:00').getDay() === 1;
          const isToday = i === data.length - 1;
          const showLabel = isWeekStart || isToday || i === 0;
          return (
            <div key={d.date} className="flex-1 text-center">
              {showLabel ? (
                <span className={`text-[8px] ${isToday ? 'text-[var(--mc-accent)] font-bold' : 'text-[var(--mc-ink-muted)]'}`}>
                  {dayNum}
                </span>
              ) : (
                <span className="text-[8px] text-transparent">.</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main page ──

export default function CostsPage() {
  const [todayCosts, setTodayCosts] = useState<TodayCosts | null>(null);
  const [rangeData, setRangeData] = useState<DailyCost[]>([]);
  const [loading, setLoading] = useState(true);
  const [rangeLoading, setRangeLoading] = useState(true);
  const stats = useDataStore((s) => s.stats);

  useEffect(() => {
    setLoading(true);
    api.get<TodayCosts>('/costs/today')
      .then(setTodayCosts)
      .catch(() => setTodayCosts(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setRangeLoading(true);
    const today = new Date();
    const from = new Date(today);
    from.setDate(from.getDate() - (DAYS - 1));
    const fromStr = from.toISOString().slice(0, 10);
    const toStr = today.toISOString().slice(0, 10);

    api.get<DailyCost[]>('/costs/range', { from: fromStr, to: toStr, group_by: 'day' } as Record<string, string | number | undefined>)
      .then((data) => {
        // Fill in missing days with zero
        const dayMap = new Map(data.map((d) => [d.date, d]));
        const filled: DailyCost[] = [];
        for (let i = 0; i < DAYS; i++) {
          const d = new Date(today);
          d.setDate(d.getDate() - (DAYS - 1 - i));
          const dateStr = d.toISOString().slice(0, 10);
          const entry = dayMap.get(dateStr);
          filled.push({
            date: dateStr,
            cost_usd: entry?.cost_usd ?? 0,
            task_count: entry?.task_count ?? 0,
          });
        }
        setRangeData(filled);
      })
      .catch(() => setRangeData([]))
      .finally(() => setRangeLoading(false));
  }, []);

  const budgetPct = (todayCosts?.budget_pct_used ?? stats?.today_budget_pct_used ?? 0) / 100;
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

      {/* 30-Day Cost Chart */}
      <div className="mt-8">
        <h2 className="text-sm font-medium text-[var(--mc-ink)] mb-3">Last {DAYS} Days</h2>
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-4 shadow-sm">
            {rangeLoading ? (
              <div className="h-52 animate-pulse rounded-lg bg-black/5" />
            ) : (
              <CostChart data={rangeData} budgetLimit={budget} />
            )}
          </div>
        </div>
      </div>

      {/* By Brand + By Model side by side */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* By Brand */}
        <div>
          <h2 className="text-sm font-medium text-[var(--mc-ink)] mb-3">By Brand</h2>
          <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
            <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-4 shadow-sm">
              {loading ? (
                <div className="h-24 animate-pulse rounded-lg bg-black/5" />
              ) : todayCosts?.by_brand.length === 0 || !todayCosts ? (
                <div className="flex items-center gap-3 rounded-lg bg-black/[0.03] px-4 py-6">
                  <DollarSign size={18} className="text-[var(--mc-ink-muted)]/40" />
                  <span className="text-[12px] text-[var(--mc-ink-muted)]/60">No costs logged today</span>
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
        <div>
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
    </div>
  );
}