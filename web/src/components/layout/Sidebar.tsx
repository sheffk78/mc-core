import React from 'react';
import {
  LayoutDashboard,
  CheckSquare,
  ThumbsUp,
  FolderOpen,
  DollarSign,
  TrendingUp,
  Settings2,
  ListTodo,
  Activity,
  MessageCircle,
  Newspaper,
} from 'lucide-react';
import { useDashboardStore } from '../../stores/dashboard';
import { useDataStore } from '../../stores/data';

const COMMAND_CENTER_ITEMS = [
  { label: 'Overview', icon: LayoutDashboard, view: 'command-center' as const },
  { label: 'Mission Control', icon: ListTodo, view: 'jeff-queue' as const },
  { label: "Kit's Stream", icon: Activity, view: 'activity-stream' as const },
  { label: 'Chat', icon: MessageCircle, view: 'chat' as const },
  { label: 'News', icon: Newspaper, view: 'news' as const },
];

const NAV_ITEMS = [
  { label: 'Tasks', icon: CheckSquare, view: 'tasks' as const },
  { label: 'Briefs', icon: ThumbsUp, view: 'briefs' as const },
  { label: 'Files', icon: FolderOpen, view: 'files' as const },
  { label: 'Costs', icon: DollarSign, view: 'costs' as const },
  { label: 'Revenue', icon: TrendingUp, view: 'revenue' as const },
  { label: 'Settings', icon: Settings2, view: 'settings' as const },
];

export function Sidebar() {
  const { activeBrand, activeView, setActiveBrand, setActiveView, setSidebarOpen } = useDashboardStore();
  const brands = useDataStore((s) => s.brands);

  // Close mobile sidebar on nav click
  const nav = (view: string) => { setActiveView(view as any); setSidebarOpen(false); };
  const filterBrand = (slug: string | null) => { setActiveBrand(slug); setSidebarOpen(false); };

  return (
    <aside
      className="flex fixed left-0 top-0 h-screen w-[220px] flex-col border-r border-[var(--mc-border)] bg-[var(--mc-surface)]"
    >
      {/* Wordmark — fixed */}
      <div className="flex-shrink-0 px-4 py-4">
        <div className="font-display text-[17px] font-bold text-[var(--mc-ink)]">
          Mission{' '}
          <span className="italic" style={{ color: 'var(--mc-accent)' }}>
            Control
          </span>
        </div>
        <div className="mt-0.5 text-[10px] tracking-widest text-[var(--mc-ink-muted)]">
          v2.0 ALPHA
        </div>
      </div>

      {/* Brands — compact, scrolls if many */}
      <div className="overflow-y-auto overscroll-contain">
        <div className="px-4 py-2 text-[10px] uppercase tracking-[0.15em] text-[var(--mc-ink-muted)]">
          Brands
        </div>

        {/* All Brands */}
        <button
          onClick={() => filterBrand(null)}
          className={`mx-2 flex w-[calc(100%-16px)] items-center rounded-md px-3 py-1.5 text-left text-sm transition-colors duration-150 ${
            activeBrand === null
              ? 'bg-[var(--mc-accent)]/10 text-[var(--mc-accent)]'
              : 'text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]'
          }`}
        >
          All Brands
        </button>

        {/* Per-brand rows */}
        {brands.map((brand) => (
          <button
            key={brand.slug}
            onClick={() => filterBrand(brand.slug)}
            className={`mx-2 flex w-[calc(100%-16px)] items-center gap-2 rounded-md px-3 py-1.5 text-left text-sm transition-colors duration-150 ${
              activeBrand === brand.slug
                ? 'bg-[var(--mc-accent)]/10 text-[var(--mc-accent)]'
                : 'text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]'
            }`}
          >
            <span
              className="h-2 w-2 flex-shrink-0 rounded-full"
              style={{ backgroundColor: brand.color }}
            />
            <span className="flex-1 truncate">{brand.name}</span>
            {brand.task_count != null && brand.task_count > 0 && (
              <span className="rounded-full bg-black/5 px-1.5 py-0.5 text-[10px] text-[var(--mc-ink-muted)]">
                {brand.task_count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Nav — fixed at bottom */}
      <nav className="flex-shrink-0 border-t border-[var(--mc-border)] pb-3 pt-2">
        <div className="px-4 pb-1 text-[10px] uppercase tracking-[0.15em] text-[var(--mc-ink-muted)]">
          Command Center
        </div>
        {COMMAND_CENTER_ITEMS.map(({ label, icon: Icon, view }) => (
          <button
            key={view}
            onClick={() => nav(view)}
            className={`mx-2 flex w-[calc(100%-16px)] items-center gap-2 rounded-md px-4 py-1.5 text-sm transition-colors duration-150 ${
              activeView === view
                ? 'bg-[var(--mc-accent)]/10 text-[var(--mc-accent)]'
                : 'text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]'
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}

        <div className="mx-4 my-1.5 border-t border-[var(--mc-border)]" />

        {NAV_ITEMS.map(({ label, icon: Icon, view }) => (
          <button
            key={view}
            onClick={() => nav(view)}
            className={`mx-2 flex w-[calc(100%-16px)] items-center gap-2 rounded-md px-4 py-1.5 text-sm transition-colors duration-150 ${
              activeView === view
                ? 'bg-[var(--mc-accent)]/10 text-[var(--mc-accent)]'
                : 'text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]'
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
