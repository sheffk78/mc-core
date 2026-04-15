import React, { useMemo } from 'react';
import { FileText } from 'lucide-react';
import { useDataStore } from '../stores/data';
import { useDashboardStore } from '../stores/dashboard';
import type { Task } from '../lib/types';

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
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="mt-1 space-y-0.5 text-[13px] text-[var(--mc-ink)]">
          {listItems.map((item, i) => (
            <li key={i} className="flex gap-2">
              <span className="mt-0.5 text-[var(--mc-accent)]">•</span>
              <span>{item.replace(/^\d+\.\s*/, '')}</span>
            </li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.match(/^##\s/)) { flushList(); elements.push(<h3 key={`h-${i}`} className="mt-4 text-[15px] font-semibold text-[var(--mc-ink)]">{line.replace(/^##\s/, '')}</h3>); }
    else if (line.match(/^#\s/)) { flushList(); elements.push(<h2 key={`h2-${i}`} className="mt-5 mb-1 text-[17px] font-bold text-[var(--mc-ink)]">{line.replace(/^#\s/, '')}</h2>); }
    else if (line.match(/^[-*]\s/)) { listItems.push(line.replace(/^[-*]\s/, '')); }
    else if (line.match(/^\d+\.\s/)) { listItems.push(line); }
    else if (line.trim() === '---') { flushList(); elements.push(<hr key={`hr-${i}`} className="my-3 border-white/[0.08]" />); }
    else if (line.trim() === '') { flushList(); }
    else {
      flushList();
      const parts = line.split(/(\*\*[^*]+\*\*)/);
      elements.push(
        <p key={`p-${i}`} className="mt-1 text-[13px] leading-relaxed text-[var(--mc-ink)]">
          {parts.map((part, j) => part.startsWith('**') && part.endsWith('**') ? <strong key={j} className="font-semibold">{part.slice(2, -2)}</strong> : part)}
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

  // Use sidebar's active brand — no duplicate brand tabs in the view itself
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
    for (const brand in map) {
      map[brand].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }
    return map;
  }, [briefings]);

  // Show all brands if no active brand filter, otherwise filter to active brand
  const brandGroups = activeBrand
    ? Object.entries(byBrand).filter(([slug]) => slug === activeBrand)
    : Object.entries(byBrand).sort((a, b) => a[0].localeCompare(b[0]));

  return (
    <div className="flex h-full">
      {/* ── Brief list (left) ─────────────────────── */}
      <div className="w-72 flex-shrink-0 border-r border-white/[0.06] overflow-y-auto">
        <div className="sticky top-0 z-10 border-b border-white/[0.06] bg-[var(--mc-bg)] px-4 py-3">
          <h2 className="text-[13px] font-semibold text-[var(--mc-ink)]">Morning Briefs</h2>
          {activeBrand && <p className="mt-0.5 text-[11px] text-[var(--mc-ink-muted)]">Showing: {activeBrand}</p>}
        </div>
        <div className="p-3 space-y-1">
          {brandGroups.length === 0 && (
            <p className="p-4 text-[12px] text-[var(--mc-ink-muted)]">No briefs found.</p>
          )}
          {brandGroups.map(([slug, briefs]) => (
            <div key={slug}>
              <div className="px-1 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--mc-ink-muted)]">{slug}</div>
              {briefs.map((b: Task) => (
                <button
                  key={b.id}
                  onClick={() => {}}
                  className="w-full rounded-lg border border-transparent px-3 py-2 text-left text-[12px] transition-colors hover:bg-white/[0.04]"
                >
                  <div className="font-medium text-[var(--mc-ink)] line-clamp-2">{b.title}</div>
                  <div className="mt-0.5 text-[10px] text-[var(--mc-ink-muted)]">
                    {formatDate(b.created_at)} · {relativeTime(b.created_at)}
                  </div>
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* ── Brief reader (right) ──────────────────── */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {briefings.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <FileText size={40} className="mb-3 text-[var(--mc-border)]" />
            <p className="text-[14px] text-[var(--mc-ink-muted)]">No briefs yet for this brand.</p>
            <p className="mt-1 text-[12px] text-[var(--mc-ink-muted)]">Briefs are generated automatically each weekday at 7 AM MT.</p>
          </div>
        ) : (
          <div className="mx-auto max-w-2xl">
            <div className="mb-6 border-b border-white/[0.06] pb-4">
              <h1 className="text-[20px] font-bold text-[var(--mc-ink)]">{briefings[0].title}</h1>
              <p className="mt-1 text-[12px] text-[var(--mc-ink-muted)]">
                {briefings[0].brand_slug} · {formatDate(briefings[0].created_at)}
              </p>
            </div>
            <div className="space-y-1">
              {renderBrief(briefings[0].description ?? 'No content available.')}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}