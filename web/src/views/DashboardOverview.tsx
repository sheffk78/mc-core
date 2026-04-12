import React, { useEffect, useMemo } from 'react';
import {
  CheckCircle2,
  ArrowRight,
  Zap,
  DollarSign,
  Cpu,
} from 'lucide-react';
import { useDataStore } from '../stores/data';
import { useDashboardStore } from '../stores/dashboard';
import type { Activity, Actor, QueueItem } from '../lib/types';

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

function isToday(dateStr: string): boolean {
  const d = new Date(dateStr);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

const ACTOR_CONFIG: Record<Actor, { label: string; color: string }> = {
  kit: { label: 'Kit', color: 'var(--mc-accent)' },
  jeff: { label: 'Jeff', color: 'var(--mc-green)' },
  system: { label: 'System', color: 'var(--mc-ink-muted)' },
  cron: { label: 'Cron', color: 'var(--mc-yellow)' },
};

// ── Section header with link ──

function PanelHeader({
  title,
  subtitle,
  viewName,
}: {
  title: string;
  subtitle: string;
  viewName: string;
}) {
  const setActiveView = useDashboardStore((s) => s.setActiveView);

  return (
    <div className="flex items-baseline justify-between">
      <div>
        <h2 className="font-display text-lg font-bold text-[var(--mc-ink)]">{title}</h2>
        <p className="mt-0.5 text-[11px] text-[var(--mc-ink-muted)]">{subtitle}</p>
      </div>
      <button
        onClick={() => setActiveView(viewName)}
        className="flex items-center gap-1 text-[12px] text-[var(--mc-accent)] transition-colors duration-150 hover:opacity-80"
      >
        View all
        <ArrowRight size={12} />
      </button>
    </div>
  );
}

// ── Queue count badges ──

function QueueCountBadges({
  counts,
}: {
  counts: { red: number; yellow: number; green: number };
}) {
  const items = [
    { label: 'Needs Decision', count: counts.red, color: 'var(--mc-red)' },
    { label: 'Ready for Review', count: counts.yellow, color: 'var(--mc-yellow)' },
    { label: 'Recently Done', count: counts.green, color: 'var(--mc-green)' },
  ];

  return (
    <div className="flex items-center gap-3">
      {items.map(({ label, count, color }) => (
        <div key={label} className="flex items-center gap-1.5">
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="text-[12px] text-[var(--mc-ink-muted)]">{label}</span>
          <span
            className="inline-flex items-center justify-center rounded-full min-w-[18px] h-[18px] px-1 text-[10px] font-medium"
            style={{
              backgroundColor: `color-mix(in oklch, ${color} 15%, transparent)`,
              color,
            }}
          >
            {count}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Queue item row (compact) ──

function QueueItemRow({ item }: { item: QueueItem }) {
  return (
    <div className="flex items-center gap-2.5 rounded-md bg-white/[0.02] px-3 py-2 transition-colors duration-150 hover:bg-white/[0.04]">
      <span
        className="h-1.5 w-1.5 flex-shrink-0 rounded-full"
        style={{
          backgroundColor:
            item.risk_tier === 'red'
              ? 'var(--mc-red)'
              : item.risk_tier === 'yellow'
                ? 'var(--mc-yellow)'
                : 'var(--mc-green)',
        }}
      />
      <span className="flex-1 truncate text-[13px] text-[var(--mc-ink)]">
        {item.title}
      </span>
      <span className="flex-shrink-0 text-[11px] text-[var(--mc-ink-muted)]">
        {item.brand_slug}
      </span>
      <span className="flex-shrink-0 text-[11px] text-[var(--mc-ink-muted)]">
        {relativeTime(item.created_at)}
      </span>
    </div>
  );
}

// ── Activity row (compact) ──

function ActivityRowCompact({ activity }: { activity: Activity }) {
  const actorCfg = ACTOR_CONFIG[activity.actor] ?? ACTOR_CONFIG.system;

  return (
    <div className="flex items-start gap-2 rounded-md bg-white/[0.02] px-3 py-2 transition-colors duration-150 hover:bg-white/[0.04]">
      <span className="mt-0.5 w-12 flex-shrink-0 text-right text-[11px] text-[var(--mc-ink-muted)]">
        {relativeTime(activity.created_at)}
      </span>
      <span
        className="mt-0.5 inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium flex-shrink-0"
        style={{
          backgroundColor: `color-mix(in oklch, ${actorCfg.color} 12%, transparent)`,
          color: actorCfg.color,
        }}
      >
        {actorCfg.label}
      </span>
      <span className="flex-1 truncate text-[13px] text-[var(--mc-ink)]">
        {activity.summary}
      </span>
    </div>
  );
}

// ── Daily stats bar (compact) ──

function DailyStatsCompact({ activities }: { activities: Activity[] }) {
  const todayActivities = activities.filter((a) => isToday(a.created_at));
  const totalActions = todayActivities.length;
  const totalTokens = todayActivities.reduce((s, a) => s + (a.tokens_used ?? 0), 0);
  const totalCost = todayActivities.reduce((s, a) => s + (a.cost_usd ?? 0), 0);

  return (
    <div className="flex items-center gap-4 rounded-lg bg-white/[0.02] px-3 py-2 text-[11px]">
      <div className="flex items-center gap-1">
        <Zap size={11} className="text-[var(--mc-accent)]" />
        <span className="text-[var(--mc-ink-muted)]">{totalActions} actions</span>
      </div>
      <div className="flex items-center gap-1">
        <Cpu size={11} className="text-[var(--mc-ink-muted)]" />
        <span className="text-[var(--mc-ink-muted)]">
          {totalTokens >= 1000 ? `${(totalTokens / 1000).toFixed(1)}k` : totalTokens} tok
        </span>
      </div>
      <div className="flex items-center gap-1">
        <DollarSign size={11} className="text-[var(--mc-green)]" />
        <span className="text-[var(--mc-ink-muted)]">${totalCost.toFixed(3)}</span>
      </div>
    </div>
  );
}

// ── Empty state ──

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-white/[0.02] px-4 py-4">
      <CheckCircle2 size={16} className="text-[var(--mc-green)]/40" />
      <span className="text-[12px] text-[var(--mc-ink-muted)]/60">{message}</span>
    </div>
  );
}

// ── Main DashboardOverview ──

export default function DashboardOverview() {
  const {
    jeffQueue,
    activities,
    tasks,
    approvals,
    loading,
    fetchJeffQueue,
    fetchActivities,
    fetchTasks,
    fetchApprovals,
  } = useDataStore();
  const activeBrand = useDashboardStore((s) => s.activeBrand);

  // Fetch data
  useEffect(() => {
    fetchJeffQueue();
    fetchActivities({ limit: 20 });
    fetchApprovals({ status: 'pending' });
    fetchTasks({ status: 'pending_review' });
  }, [activeBrand, fetchJeffQueue, fetchActivities, fetchApprovals, fetchTasks]);

  // Build Jeff's Queue items from fetched data
  const queueItems = useMemo(() => {
    if (jeffQueue) return jeffQueue.items.slice(0, 6);
    return [];
  }, [jeffQueue]);

  const queueCounts = jeffQueue?.counts ?? { red: 0, yellow: 0, green: 0 };
  const recentActivities = activities.slice(0, 10);

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      {/* Page header */}
      <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">
        Dashboard
      </h1>
      <p className="mt-1 text-sm text-[var(--mc-ink-muted)]">
        Mission Control overview — what needs attention right now
      </p>

      {/* Split layout */}
      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* LEFT — Jeff's Queue (60% = 3/5) */}
        <div className="lg:col-span-3 rounded-[1rem] border border-white/[0.08] bg-white/5 p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
            <PanelHeader
              title="Jeff's Queue"
              subtitle="Items needing your input"
              viewName="command-center"
            />

            {/* Count badges */}
            <div className="mt-4">
              <QueueCountBadges counts={queueCounts} />
            </div>

            {/* Queue items */}
            <div className="mt-4 flex flex-col gap-1.5">
              {loading.jeffQueue ? (
                [...Array(4)].map((_, i) => (
                  <div
                    key={i}
                    className="h-9 animate-pulse rounded-md bg-white/5"
                  />
                ))
              ) : queueItems.length === 0 ? (
                <EmptyState message="Nothing needs your attention" />
              ) : (
                queueItems.map((item) => (
                  <QueueItemRow key={item.id} item={item} />
                ))
              )}
            </div>
          </div>
        </div>

        {/* RIGHT — Kit's Stream (40% = 2/5) */}
        <div className="lg:col-span-2 rounded-[1rem] border border-white/[0.08] bg-white/5 p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.07)]">
            <PanelHeader
              title="Kit's Stream"
              subtitle="Recent agent activity"
              viewName="command-center"
            />

            {/* Daily stats */}
            <div className="mt-4">
              <DailyStatsCompact activities={activities} />
            </div>

            {/* Activity items */}
            <div className="mt-4 flex flex-col gap-1.5">
              {loading.activities && activities.length === 0 ? (
                [...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="h-8 animate-pulse rounded-md bg-white/5"
                  />
                ))
              ) : recentActivities.length === 0 ? (
                <EmptyState message="No activity yet" />
              ) : (
                recentActivities.map((a) => (
                  <ActivityRowCompact key={a.id} activity={a} />
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
