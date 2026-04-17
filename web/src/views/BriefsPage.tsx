import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { FileText, Calendar, ChevronRight, ArrowLeft } from 'lucide-react';
import { useDashboardStore } from '../stores/dashboard';
import { api } from '../lib/api';
import type { Task, PaginatedResponse } from '../lib/types';

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

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function formatFullDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

// ── Markdown-like renderer ──

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
    if (line.match(/^##\s/)) {
      flushList();
      elements.push(
        <h3 key={`h-${i}`} className="mt-5 mb-1 text-[14px] font-semibold uppercase tracking-wide text-[var(--mc-ink-muted)]">
          {line.replace(/^##\s/, '')}
        </h3>
      );
    } else if (line.match(/^#\s/)) {
      flushList();
      elements.push(
        <h2 key={`h2-${i}`} className="mt-6 mb-2 text-[17px] font-bold text-[var(--mc-ink)]">
          {line.replace(/^#\s/, '')}
        </h2>
      );
    } else if (line.match(/^###\s/)) {
      flushList();
      elements.push(
        <h4 key={`h4-${i}`} className="mt-4 mb-1 text-[13px] font-semibold text-[var(--mc-ink)]">
          {line.replace(/^###\s/, '')}
        </h4>
      );
    } else if (line.match(/^[-*]\s/)) {
      listItems.push(line.replace(/^[-*]\s/, ''));
    } else if (line.match(/^\d+\.\s/)) {
      listItems.push(line);
    } else if (line.trim() === '---') {
      flushList();
      elements.push(<hr key={`hr-${i}`} className="my-4 border-white/[0.08]" />);
    } else if (line.trim() === '') {
      flushList();
    } else {
      flushList();
      // Parse bold and inline code
      const parts = line.split(/(\*\*[^*]+\*\*|`[^`]+`)/);
      elements.push(
        <p key={`p-${i}`} className="mt-1 text-[13px] leading-relaxed text-[var(--mc-ink)]">
          {parts.map((part, j) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={j} className="font-semibold">{part.slice(2, -2)}</strong>;
            }
            if (part.startsWith('`') && part.endsWith('`')) {
              return (
                <code key={j} className="rounded bg-[var(--mc-bg)] px-1 py-0.5 text-[12px] font-mono text-[var(--mc-accent)]">
                  {part.slice(1, -1)}
                </code>
              );
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

// ── Brief list item ──

function BriefListItem({
  brief,
  isSelected,
  onClick,
  brandColor,
}: {
  brief: Task;
  isSelected: boolean;
  onClick: () => void;
  brandColor?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`group w-full rounded-lg px-3 py-2.5 text-left text-[12px] transition-all duration-150 ${
        isSelected
          ? 'border border-[var(--mc-accent)]/20 bg-[var(--mc-accent)]/[0.06]'
          : 'border border-transparent hover:bg-white/[0.04]'
      }`}
    >
      <div className="flex items-start gap-2">
        {brandColor && (
          <span
            className="mt-1 h-2 w-2 flex-shrink-0 rounded-full"
            style={{ backgroundColor: brandColor }}
          />
        )}
        <div className="flex-1 min-w-0">
          <div className={`font-medium line-clamp-2 ${isSelected ? 'text-[var(--mc-accent)]' : 'text-[var(--mc-ink)]'}`}>
            {brief.title}
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-[10px] text-[var(--mc-ink-muted)]">
            <Calendar size={10} />
            <span>{formatDate(brief.created_at)}</span>
            <span>·</span>
            <span>{relativeTime(brief.created_at)}</span>
          </div>
        </div>
        <ChevronRight
          size={14}
          className={`mt-0.5 flex-shrink-0 transition-colors ${
            isSelected ? 'text-[var(--mc-accent)]' : 'text-transparent group-hover:text-[var(--mc-ink-muted)]'
          }`}
        />
      </div>
    </button>
  );
}

// ── Main page ──

export default function BriefsPage() {
  const activeBrand = useDashboardStore((s) => s.activeBrand);
  const [selectedBriefId, setSelectedBriefId] = useState<string | null>(null);
  const [briefings, setBriefings] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch briefing tasks directly — don't clobber the shared tasks store
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.get<PaginatedResponse<Task>>('/tasks', {
      brand: activeBrand ?? undefined,
      category: 'briefing',
      limit: 50,
    } as Record<string, string | number | undefined>)
      .then((data) => {
        if (!cancelled) {
          setBriefings(data.items);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || 'Failed to load briefs');
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [activeBrand]);

  // Group by brand_slug
  const byBrand = useMemo(() => {
    const map: Record<string, Task[]> = {};
    for (const t of briefings) {
      const brand = t.brand_slug ?? 'unknown';
      if (!map[brand]) map[brand] = [];
      map[brand].push(t);
    }
    for (const brand in map) {
      map[brand].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      );
    }
    return map;
  }, [briefings]);

  // Build brand color map from tasks
  const brandColorMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const t of briefings) {
      if (t.brand_slug && t.brand_color) {
        map[t.brand_slug] = t.brand_color;
      }
    }
    return map;
  }, [briefings]);

  // Which brand groups to show
  const brandGroups = activeBrand
    ? Object.entries(byBrand).filter(([slug]) => slug === activeBrand)
    : Object.entries(byBrand).sort((a, b) => a[0].localeCompare(b[0]));

  // Currently selected brief
  const selectedBrief = useMemo(() => {
    if (selectedBriefId) {
      return briefings.find((b) => b.id === selectedBriefId) ?? null;
    }
    // Default to most recent
    return briefings.length > 0 ? briefings[0] : null;
  }, [selectedBriefId, briefings]);

  // Select a brief
  const handleSelect = useCallback((id: string) => {
    setSelectedBriefId(id);
  }, []);

  // Auto-select most recent when list changes and nothing is selected
  useEffect(() => {
    if (!selectedBriefId && briefings.length > 0) {
      setSelectedBriefId(briefings[0].id);
    }
  }, [selectedBriefId, briefings]);

  // ── Brief list sidebar (shared between mobile and desktop) ──

  const briefList = (
    <div className="w-full md:w-72 md:flex-shrink-0 md:border-r md:border-white/[0.06] overflow-y-auto">
      <div className="sticky top-0 z-10 border-b border-white/[0.06] bg-[var(--mc-bg)] px-4 py-3">
        <h2 className="text-[13px] font-semibold text-[var(--mc-ink)]">Morning Briefs</h2>
        {activeBrand && (
          <p className="mt-0.5 text-[11px] text-[var(--mc-ink-muted)]">
            Showing: {activeBrand}
          </p>
        )}
      </div>
      <div className="p-2 space-y-0.5">
        {loading ? (
          <div className="flex items-center justify-center py-10">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--mc-border)] border-t-[var(--mc-accent)]" />
          </div>
        ) : error ? (
          <div className="p-4 text-center">
            <p className="text-[12px] text-[var(--mc-red)]">{error}</p>
          </div>
        ) : brandGroups.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-[12px] text-[var(--mc-ink-muted)]">No briefs found.</p>
            <p className="mt-1 text-[11px] text-[var(--mc-ink-muted)]">
              Briefs are generated each weekday at 7 AM MT.
            </p>
          </div>
        ) : (
          brandGroups.map(([slug, briefs]) => (
            <div key={slug}>
              {/* Brand header — only show when viewing all brands */}
              {!activeBrand && (
                <div className="flex items-center gap-1.5 px-2 py-2">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: brandColorMap[slug] ?? '#888' }}
                  />
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--mc-ink-muted)]">
                    {slug}
                  </span>
                  <span className="ml-auto text-[10px] text-[var(--mc-ink-muted)]">
                    {briefs.length}
                  </span>
                </div>
              )}
              {briefs.map((b: Task) => (
                <BriefListItem
                  key={b.id}
                  brief={b}
                  isSelected={selectedBrief?.id === b.id}
                  onClick={() => handleSelect(b.id)}
                  brandColor={!activeBrand ? undefined : brandColorMap[slug]}
                />
              ))}
            </div>
          ))
        )}
      </div>
    </div>
  );

  // ── Brief reader (shared between mobile and desktop) ──

  const briefReader = selectedBrief ? (
    <div className="flex-1 overflow-y-auto px-4 py-4 md:px-8 md:py-6">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="mb-6 border-b border-white/[0.06] pb-5">
          <div className="flex items-center gap-2 mb-2">
            {selectedBrief.brand_slug && (
              <span
                className="h-2 w-2 rounded-full"
                style={{
                  backgroundColor:
                    brandColorMap[selectedBrief.brand_slug] ?? '#888',
                }}
              />
            )}
            <span className="text-[11px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
              {selectedBrief.brand_slug ?? 'unknown'}
            </span>
          </div>
          <h1 className="text-[18px] md:text-[20px] font-bold text-[var(--mc-ink)] leading-tight">
            {selectedBrief.title}
          </h1>
          <p className="mt-1.5 text-[12px] text-[var(--mc-ink-muted)]">
            {formatFullDate(selectedBrief.created_at)}
          </p>
        </div>

        {/* Brief content */}
        <div className="space-y-1">
          {renderBrief(selectedBrief.description ?? 'No content available.')}
        </div>

        {/* Footer — metadata */}
        {(selectedBrief.agent_note || selectedBrief.risk_tier) && (
          <div className="mt-8 border-t border-white/[0.06] pt-4">
            <div className="flex items-center gap-3 text-[11px] text-[var(--mc-ink-muted)]">
              {selectedBrief.risk_tier && (
                <span className="flex items-center gap-1">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      selectedBrief.risk_tier === 'red'
                        ? 'bg-[var(--mc-red)]'
                        : selectedBrief.risk_tier === 'yellow'
                        ? 'bg-[var(--mc-yellow)]'
                        : 'bg-[var(--mc-green)]'
                    }`}
                  />
                  {selectedBrief.risk_tier}
                </span>
              )}
              {selectedBrief.assignee && (
                <span>assignee: {selectedBrief.assignee}</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  ) : (
    <div className="flex flex-1 flex-col items-center justify-center text-center px-4">
      <FileText size={40} className="mb-3 text-[var(--mc-border)]" />
      <p className="text-[14px] text-[var(--mc-ink-muted)]">No brief selected.</p>
    </div>
  );

  return (
    <div className="flex h-full">
      {/* Mobile: show list OR detail with back button */}
      <div className="md:hidden flex flex-1 flex-col">
        {selectedBrief ? (
          <div className="flex flex-1 flex-col overflow-hidden">
            <button
              onClick={() => setSelectedBriefId(null)}
              className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-2.5 text-[13px] text-[var(--mc-accent)] hover:opacity-80"
            >
              <ArrowLeft size={16} />
              Back to briefs
            </button>
            {briefReader}
          </div>
        ) : (
          briefList
        )}
      </div>

      {/* Desktop: side-by-side layout */}
      <div className="hidden md:flex flex-1">
        {briefList}
        {briefReader}
      </div>

      {/* Empty state — no briefs at all */}
      {briefings.length === 0 && !loading && (
        <div className="flex flex-1 flex-col items-center justify-center text-center">
          <FileText size={40} className="mb-3 text-[var(--mc-border)]" />
          <p className="text-[14px] text-[var(--mc-ink-muted)]">No briefs yet.</p>
          <p className="mt-1 text-[12px] text-[var(--mc-ink-muted)]">
            Briefs are generated automatically each weekday at 7 AM MT.
          </p>
        </div>
      )}
    </div>
  );
}