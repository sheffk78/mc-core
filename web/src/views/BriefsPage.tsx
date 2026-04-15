import React, { useEffect, useState, useMemo } from 'react';
import { FileText } from 'lucide-react';
import { useDataStore } from '../stores/data';
import { useDashboardStore } from '../stores/dashboard';
import type { Task } from '../lib/types';

const BRAND_TABS = [
  { slug: 'trustoffice', label: 'TrustOffice', color: '#c85a2a' },
  { slug: 'wingpoint', label: 'WingPoint', color: '#6b7c4a' },
  { slug: 'agentictrust', label: 'AgenticTrust', color: '#3d5a7a' },
  { slug: 'truejoybirthing', label: 'True Joy Birthing', color: '#a0522d' },
] as const;

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

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function renderBrief(text: string): React.ReactNode {
  // Simple markdown-like renderer: ## headings, **bold**, bullet lists, numbered lists, code
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let inList = false;
  let listItems: string[] = [];

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="mt-1 space-y-0.5 text-[13px] text-[var(--mc-ink)]">
          {listItems.map((item, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-[var(--mc-accent)] mt-0.5">•</span>
              <span>{item.replace(/^\d+\.\s*/, '')}</span>
            </li>
          ))}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.match(/^##\s/)) {
      flushList();
      elements.push(
        <h3 key={`h-${i}`} className="mt-4 text-[15px] font-semibold text-[var(--mc-ink)]">
          {line.replace(/^##\s/, '')}
        </h3>
      );
    } else if (line.match(/^#\s/)) {
      flushList();
      elements.push(
        <h2 key={`h2-${i}`} className="mt-5 mb-1 text-[17px] font-bold text-[var(--mc-ink)]">
          {line.replace(/^#\s/, '')}
        </h2>
      );
    } else if (line.match(/^[-*]\s/)) {
      inList = true;
      listItems.push(line.replace(/^[-*]\s/, ''));
    } else if (line.match(/^\d+\.\s/)) {
      inList = true;
      listItems.push(line);
    } else if (line.trim() === '---') {
      flushList();
      elements.push(<hr key={`hr-${i}`} className="my-3 border-white/[0.08]" />);
    } else if (line.trim() === '') {
      flushList();
    } else {
      flushList();
      // Handle **bold** inline
      const parts = line.split(/(\*\*[^*]+\*\*)/);
      elements.push(
        <p key={`p-${i}`} className="mt-1 text-[13px] leading-relaxed text-[var(--mc-ink)]">
          {parts.map((part, j) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={j} className="font-semibold">{part.slice(2, -2)}</strong>;
            }
            return part;
          })}
        </p>
      );
    }
  }
  flushList();
  return <>{elements}</>;
}

export default function BriefsPage() {
  const tasks = useDataStore((s) => s.tasks);
  const activeBrand = useDashboardStore((s) => s.activeBrand);
  const setActiveBrand = useDashboardStore((s) => s.setActiveBrand);

  // Filter to briefing tasks only
  const briefings = useMemo(
    () => tasks.filter((t: Task) => t.category === 'briefing'),
    [tasks],
  );

  // Group by brand_slug
  const byBrand = useMemo(() => {
    const map: Record<string, Task[]> = {};
    for (const t of briefings) {
      const brand = t.brand_slug ?? 'unknown';
      if (!map[brand]) map[brand] = [];
      map[brand].push(t);
    }
    // Sort newest first
    for (const brand in map) {
      map[brand].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }
    return map;
  }, [briefings]);

  // Active brand tab — default to first
  const [tab, setTab] = useState<string>(activeBrand ?? BRAND_TABS[0].slug);
  useEffect(() => { if (!activeBrand) setTab(BRAND_TABS[0].slug); }, [activeBrand]);

  const brandData = BRAND_TABS.find((b) => b.slug === tab);
  const brandBriefs = byBrand[tab] ?? [];

  return (
    <div className="flex h-full">
      {/* ── Left: brief list ─────────────────────────────── */}
      <div className="w-64 flex-shrink-0 border-r border-white/[0.06] overflow-y-auto">
        {/* Brand tabs */}
        <div className="sticky top-0 z-10 border-b border-white/[0.06] bg-[var(--mc-bg)] px-3 py-2">
          <div className="flex gap-1">
            {BRAND_TABS.map((bt) => (
              <button
                key={bt.slug}
                onClick={() => setTab(bt.slug)}
                className={`rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                  tab === bt.slug
                    ? 'text-white'
                    : 'text-[var(--mc-ink-muted)] hover:text-[var(--mc-ink)]'
                }`}
                style={tab === bt.slug ? { backgroundColor: bt.color + '33' } : {}}
              >
                {bt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Brief list for active brand */}
        <div className="p-2 space-y-1">
          {brandBriefs.length === 0 && (
            <p className="p-3 text-[12px] text-[var(--mc-ink-muted)]">No briefs yet</p>
          )}
          {brandBriefs.map((b: Task) => (
            <button
              key={b.id}
              className="w-full rounded-lg border border-transparent px-3 py-2 text-left text-[12px] transition-colors hover:bg-white/[0.04]"
            >
              <div className="font-medium text-[var(--mc-ink)]">{b.title}</div>
              <div className="mt-0.5 text-[10px] text-[var(--mc-ink-muted)]">
                {formatDate(b.created_at)} · {relativeTime(b.created_at)}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* ── Right: brief reader ──────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {brandBriefs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <FileText size={40} className="text-[var(--mc-border)] mb-3" />
            <p className="text-[14px] text-[var(--mc-ink-muted)]">
              No briefs for <strong>{brandData?.label}</strong> yet.
            </p>
            <p className="mt-1 text-[12px] text-[var(--mc-ink-muted)]">
              Briefs are generated automatically each weekday at 7 AM MT.
            </p>
          </div>
        ) : (
          <div className="max-w-2xl mx-auto">
            {/* Latest brief header */}
            <div className="mb-6 pb-4 border-b border-white/[0.06]">
              <h1 className="text-[20px] font-bold text-[var(--mc-ink)]">
                {brandBriefs[0]?.title}
              </h1>
              <p className="mt-1 text-[12px] text-[var(--mc-ink-muted)]">
                {brandData?.label} · {formatDate(brandBriefs[0]?.created_at)}
              </p>
            </div>

            {/* Brief content */}
            <div className="space-y-1">
              {renderBrief(brandBriefs[0]?.description ?? 'No content available.')}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}