import React, { useEffect, useMemo, useState, useRef } from 'react';
import {
  Bot,
  User,
  Cpu,
  Clock,
  Zap,
  DollarSign,
  CheckSquare,
  Filter,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { useDataStore } from '../stores/data';
import { useDashboardStore } from '../stores/dashboard';
import type { Activity, Actor } from '../lib/types';

// ── Helpers ──

function relativeTime(dateStr: string): string {
  const now = Date.now();
  const normalized = dateStr.includes("Z") || dateStr.includes("+") ? dateStr : dateStr + "Z";
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

function formatHour(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('en-US', {
    hour: 'numeric',
    hour12: true,
  });
}

function getHourBucket(dateStr: string): string {
  const d = new Date(dateStr);
  d.setMinutes(0, 0, 0);
  return d.toISOString();
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

// ── Actor config ──

const ACTOR_CONFIG: Record<
  Actor,
  { label: string; icon: React.ReactNode; color: string; bgColor: string }
> = {
  kit: {
    label: 'Kit',
    icon: <Bot size={12} />,
    color: 'var(--mc-accent)',
    bgColor: 'var(--mc-accent)',
  },
  jeff: {
    label: 'Jeff',
    icon: <User size={12} />,
    color: 'var(--mc-green)',
    bgColor: 'var(--mc-green)',
  },
  system: {
    label: 'System',
    icon: <Cpu size={12} />,
    color: 'var(--mc-ink-muted)',
    bgColor: 'var(--mc-ink-muted)',
  },
  cron: {
    label: 'Cron',
    icon: <Clock size={12} />,
    color: 'var(--mc-yellow)',
    bgColor: 'var(--mc-yellow)',
  },
};

// ── Action icons ──

function getActionIcon(action: string): React.ReactNode {
  if (action.includes('task') || action.includes('complete')) return <CheckSquare size={12} />;
  if (action.includes('approval') || action.includes('approv')) return <Zap size={12} />;
  return <Zap size={12} />;
}

// ── Daily summary bar ──

function DailySummaryBar({ activities }: { activities: Activity[] }) {
  const todayActivities = activities.filter((a) => isToday(a.created_at));
  const totalActions = todayActivities.length;
  const totalTokens = todayActivities.reduce((s, a) => s + (a.tokens_used ?? 0), 0);
  const totalCost = todayActivities.reduce((s, a) => s + (a.cost_usd ?? 0), 0);
  const tasksCompleted = todayActivities.filter(
    (a) => a.action === 'task.completed' || a.action === 'complete',
  ).length;

  return (
    <div className="rounded-[0.75rem] border border-white/[0.06] bg-white/[0.03] p-[4px]">
      <div className="flex items-center gap-6 rounded-[calc(0.75rem-4px)] bg-[var(--mc-surface)] px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
        <div className="flex items-center gap-1.5 text-[12px]">
          <Zap size={13} className="text-[var(--mc-accent)]" />
          <span className="text-[var(--mc-ink-muted)]">Actions</span>
          <span className="font-medium text-[var(--mc-ink)]">{totalActions}</span>
        </div>

        <div className="flex items-center gap-1.5 text-[12px]">
          <Cpu size={13} className="text-[var(--mc-ink-muted)]" />
          <span className="text-[var(--mc-ink-muted)]">Tokens</span>
          <span className="font-medium text-[var(--mc-ink)]">
            {totalTokens >= 1000 ? `${(totalTokens / 1000).toFixed(1)}k` : totalTokens}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-[12px]">
          <DollarSign size={13} className="text-[var(--mc-green)]" />
          <span className="text-[var(--mc-ink-muted)]">Cost</span>
          <span className="font-medium text-[var(--mc-ink)]">
            ${totalCost.toFixed(3)}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-[12px]">
          <CheckSquare size={13} className="text-[var(--mc-yellow)]" />
          <span className="text-[var(--mc-ink-muted)]">Completed</span>
          <span className="font-medium text-[var(--mc-ink)]">{tasksCompleted}</span>
        </div>
      </div>
    </div>
  );
}

// ── Activity row ──

function ActivityRow({ activity }: { activity: Activity }) {
  const actorCfg = ACTOR_CONFIG[activity.actor] ?? ACTOR_CONFIG.system;

  return (
    <div className="group flex items-start gap-3 rounded-lg px-3 py-2.5 transition-colors duration-150 hover:bg-white/[0.03]">
      {/* Timestamp */}
      <span className="mt-0.5 w-14 flex-shrink-0 text-right text-[11px] text-[var(--mc-ink-muted)]">
        {relativeTime(activity.created_at)}
      </span>

      {/* Actor badge */}
      <span
        className="mt-0.5 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium flex-shrink-0"
        style={{
          backgroundColor: `color-mix(in oklch, ${actorCfg.bgColor} 12%, transparent)`,
          color: actorCfg.color,
        }}
      >
        {actorCfg.icon}
        {actorCfg.label}
      </span>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-[var(--mc-ink-muted)]">{getActionIcon(activity.action)}</span>
          <span className="text-[13px] text-[var(--mc-ink)]">{activity.summary}</span>
        </div>

        {/* Brand tag */}
        {activity.brand_slug && (
          <span className="mt-1 inline-block rounded bg-black/5 px-1.5 py-0.5 text-[10px] text-[var(--mc-ink-muted)]">
            {activity.brand_slug}
          </span>
        )}

        {/* Model + tokens + cost */}
        {(activity.model_used || activity.tokens_used || activity.cost_usd) && (
          <div className="mt-1 flex items-center gap-3 text-[11px] text-[var(--mc-ink-muted)]">
            {activity.model_used && <span>{activity.model_used}</span>}
            {activity.tokens_used != null && activity.tokens_used > 0 && (
              <span>{activity.tokens_used.toLocaleString()} tok</span>
            )}
            {activity.cost_usd != null && activity.cost_usd > 0 && (
              <span>${activity.cost_usd.toFixed(4)}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Hour group ──

function HourGroup({
  hourLabel,
  activities,
  defaultOpen,
}: {
  hourLabel: string;
  activities: Activity[];
  defaultOpen: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-left text-[12px] text-[var(--mc-ink-muted)] transition-colors duration-150 hover:bg-white/[0.03] hover:text-[var(--mc-ink)]"
      >
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <span className="font-medium">{hourLabel}</span>
        <span className="text-[10px] opacity-60">{activities.length} activities</span>
      </button>
      {open && (
        <div>
          {activities.map((a) => (
            <ActivityRow key={a.id} activity={a} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Filter bar ──

function FilterBar({
  filters,
  onChange,
}: {
  filters: { actor: string; brand: string; action: string };
  onChange: (filters: { actor: string; brand: string; action: string }) => void;
}) {
  const brands = useDataStore((s) => s.brands);
  const actors: Actor[] = ['kit', 'jeff', 'system', 'cron'];

  return (
    <div className="flex items-center gap-2">
      <Filter size={13} className="text-[var(--mc-ink-muted)]" />

      <select
        value={filters.actor}
        onChange={(e) => onChange({ ...filters, actor: e.target.value })}
        className="rounded-md border border-[var(--mc-border)] bg-[var(--mc-surface)] px-2 py-1 text-[12px] text-[var(--mc-ink)] focus:border-[var(--mc-accent)] focus:outline-none"
      >
        <option value="">All actors</option>
        {actors.map((a) => (
          <option key={a} value={a}>
            {ACTOR_CONFIG[a].label}
          </option>
        ))}
      </select>

      <select
        value={filters.brand}
        onChange={(e) => onChange({ ...filters, brand: e.target.value })}
        className="rounded-md border border-[var(--mc-border)] bg-[var(--mc-surface)] px-2 py-1 text-[12px] text-[var(--mc-ink)] focus:border-[var(--mc-accent)] focus:outline-none"
      >
        <option value="">All brands</option>
        {brands.map((b) => (
          <option key={b.slug} value={b.slug}>
            {b.name}
          </option>
        ))}
      </select>

      {(filters.actor || filters.brand) && (
        <button
          onClick={() => onChange({ actor: '', brand: '', action: '' })}
          className="text-[11px] text-[var(--mc-accent)] hover:underline"
        >
          Clear
        </button>
      )}
    </div>
  );
}

// ── Main ActivityStream view ──

export default function ActivityStreamView() {
  const { activities, loading, fetchActivities } = useDataStore();
  const activeBrand = useDashboardStore((s) => s.activeBrand);
  const [filters, setFilters] = useState({ actor: '', brand: '', action: '' });
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fetch on mount + brand/filter change
  useEffect(() => {
    fetchActivities({
      brand: activeBrand ?? undefined,
      actor: filters.actor || undefined,
      limit: 100,
    });
  }, [activeBrand, filters.actor, filters.brand, fetchActivities]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      fetchActivities({
        brand: activeBrand ?? undefined,
        actor: filters.actor || undefined,
        limit: 100,
      });
    }, 30000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [activeBrand, filters.actor, filters.brand, fetchActivities]);

  // Group activities by hour
  const hourGroups = useMemo(() => {
    const filtered = activities.filter((a) => {
      if (filters.brand && a.brand_slug !== filters.brand) return false;
      return true;
    });

    const groups = new Map<string, Activity[]>();
    for (const a of filtered) {
      const bucket = getHourBucket(a.created_at);
      if (!groups.has(bucket)) groups.set(bucket, []);
      groups.get(bucket)!.push(a);
    }

    return Array.from(groups.entries()).map(([iso, items]) => ({
      iso,
      label: formatHour(items[0].created_at),
      activities: items,
    }));
  }, [activities, filters]);

  const isLoading = loading.activities;

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      {/* Header */}
      <div className="flex items-baseline justify-between">
        <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">
          Kit's Activity Stream
        </h1>
        <span className="text-[11px] text-[var(--mc-ink-muted)]">
          Auto-refreshes every 30s
        </span>
      </div>

      {/* Daily summary */}
      <div className="mt-6">
        <DailySummaryBar activities={activities} />
      </div>

      {/* Filters */}
      <div className="mt-4">
        <FilterBar filters={filters} onChange={setFilters} />
      </div>

      {/* Feed */}
      <div className="mt-6 flex flex-col">
        {isLoading && activities.length === 0 ? (
          <div className="flex flex-col gap-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-start gap-3 px-3 py-2.5">
                <div className="h-3 w-12 animate-pulse rounded bg-black/5" />
                <div className="h-5 w-14 animate-pulse rounded-full bg-black/5" />
                <div className="flex-1">
                  <div className="h-3.5 w-3/4 animate-pulse rounded bg-black/5" />
                  <div className="mt-1.5 h-3 w-1/3 animate-pulse rounded bg-black/5" />
                </div>
              </div>
            ))}
          </div>
        ) : activities.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <p className="text-sm text-[var(--mc-ink-muted)]">No activity yet.</p>
          </div>
        ) : (
          hourGroups.map((group, i) => (
            <HourGroup
              key={group.iso}
              hourLabel={group.label}
              activities={group.activities}
              defaultOpen={i < 2} // First 2 hour groups open by default
            />
          ))
        )}
      </div>
    </div>
  );
}
