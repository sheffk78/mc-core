import React, { useEffect, useState, useCallback } from 'react';
import { Newspaper, Star, EyeOff, MessageSquare, ExternalLink } from 'lucide-react';
import { useDashboardStore } from '../stores/dashboard';
import { useDataStore } from '../stores/data';
import { api } from '../lib/api';
import type { News } from '../lib/types';

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

// ── News card ──

function NewsCard({ item, onUpdated }: { item: News; onUpdated: (updated: News) => void }) {
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [noteValue, setNoteValue] = useState(item.jeff_comment ?? '');

  const handleMarkRead = useCallback(async () => {
    try {
      const updated = await api.patch<News>(`/news/${item.id}`, { is_read: 1 });
      onUpdated(updated);
    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  }, [item.id, onUpdated]);

  const handleNoteSubmit = useCallback(async () => {
    if (noteValue === (item.jeff_comment ?? '')) return;
    try {
      const updated = await api.patch<News>(`/news/${item.id}`, { jeff_comment: noteValue });
      onUpdated(updated);
    } catch (err) {
      console.error('Failed to save note:', err);
    }
  }, [item.id, noteValue, item.jeff_comment, onUpdated]);

  const isRead = item.is_read === 1;

  return (
    <div className={`border border-[var(--mc-border)] rounded-lg p-4 ${isRead ? 'opacity-70' : ''}`}>
      {/* Top row: brand dot + name, relative time */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          {item.brand_color && (
            <span
              className="h-2 w-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: item.brand_color }}
            />
          )}
          <span className="text-[11px] uppercase tracking-wider text-[var(--mc-ink-muted)]">
            {item.brand_name ?? item.brand_slug ?? 'unknown'}
          </span>
        </div>
        <span className="text-[11px] text-[var(--mc-ink-muted)]">
          {relativeTime(item.created_at)}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-[16px] font-bold text-[var(--mc-ink)] leading-tight mb-1.5">
        {item.title}
      </h3>

      {/* Summary */}
      <p className="text-[13px] leading-relaxed text-[var(--mc-ink)] mb-2">
        {item.summary}
      </p>

      {/* Source link + category pill row */}
      <div className="flex items-center gap-2 mb-2">
        <a
          href={item.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-[12px] text-[var(--mc-accent)] hover:underline"
        >
          <ExternalLink size={11} />
          {item.source_name || 'Source'}
        </a>
        {item.category && (
          <span className="rounded bg-[var(--mc-bg)] px-1.5 py-0.5 text-[10px] text-[var(--mc-ink-muted)]">
            {item.category}
          </span>
        )}
      </div>

      {/* Jeff Recommends badge */}
      {item.jeff_recommends === 1 && (
        <div className="flex items-center gap-1 mb-2 text-[var(--mc-accent)]">
          <Star size={13} fill="var(--mc-accent)" />
          <span className="text-[11px] font-semibold">Jeff Recommends</span>
        </div>
      )}

      {/* Risk tier indicator */}
      <div className="flex items-center gap-1 mb-2">
        <span
          className={`h-2 w-2 rounded-full ${
            item.risk_tier === 'red'
              ? 'bg-[var(--mc-red)]'
              : item.risk_tier === 'yellow'
              ? 'bg-[var(--mc-yellow)]'
              : 'bg-[var(--mc-green)]'
          }`}
        />
        <span className="text-[10px] text-[var(--mc-ink-muted)] capitalize">{item.risk_tier}</span>
      </div>

      {/* Jeff comment section */}
      {item.jeff_comment && !showNoteInput && (
        <div className="mb-2 rounded bg-[var(--mc-bg)]/50 px-2.5 py-1.5 text-[12px] text-[var(--mc-ink-muted)]">
          {item.jeff_comment}
        </div>
      )}
      <div className="mb-2">
        {!showNoteInput ? (
          <button
            onClick={() => {
              setNoteValue(item.jeff_comment ?? '');
              setShowNoteInput(true);
            }}
            className="inline-flex items-center gap-1 text-[11px] text-[var(--mc-accent)] hover:underline"
          >
            <MessageSquare size={11} />
            {item.jeff_comment ? 'Edit note' : 'Add note'}
          </button>
        ) : (
          <div className="space-y-1.5">
            <textarea
              value={noteValue}
              onChange={(e) => setNoteValue(e.target.value)}
              placeholder="Add a note..."
              className="w-full rounded border border-[var(--mc-border)] bg-[var(--mc-bg)] px-2 py-1.5 text-[12px] text-[var(--mc-ink)] placeholder-[var(--mc-ink-muted)] focus:outline-none focus:border-[var(--mc-accent)]"
              rows={2}
              autoFocus
            />
            <button
              onClick={handleNoteSubmit}
              className="text-[11px] text-[var(--mc-accent)] hover:underline"
            >
              Save note
            </button>
          </div>
        )}
      </div>

      {/* Mark read button */}
      {!isRead && (
        <button
          onClick={handleMarkRead}
          className="inline-flex items-center gap-1 text-[11px] text-[var(--mc-ink-muted)] hover:text-[var(--mc-ink)]"
        >
          <EyeOff size={12} />
          Mark read
        </button>
      )}
    </div>
  );
}

// ── Main page ──

export default function NewsPage() {
  const activeBrand = useDashboardStore((s) => s.activeBrand);
  const { news, newsTotal, loading, fetchNews } = useDataStore();

  // Fetch news on mount and when brand changes
  useEffect(() => {
    fetchNews({
      brand: activeBrand ?? undefined,
    });
  }, [activeBrand, fetchNews]);

  const handleUpdated = useCallback(
    (updated: News) => {
      // Re-fetch to sync store
      fetchNews({
        brand: activeBrand ?? undefined,
      });
    },
    [activeBrand, fetchNews],
  );

  // Loading state
  if (loading.news) {
    return (
      <div className="flex min-h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--mc-border)] border-t-[var(--mc-accent)]" />
      </div>
    );
  }

  // Empty state
  if (news.length === 0) {
    return (
      <div className="flex min-h-full flex-col items-center justify-center text-center px-4">
        <Newspaper size={40} className="mb-3 text-[var(--mc-border)]" />
        <p className="text-[14px] text-[var(--mc-ink-muted)]">No news items.</p>
        <p className="mt-1 text-[12px] text-[var(--mc-ink-muted)]">
          Industry intel findings will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      {/* Header */}
      <div className="flex items-baseline justify-between mb-6">
        <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">News</h1>
        <span className="text-sm text-[var(--mc-ink-muted)]">
          {newsTotal} item{newsTotal !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Card feed */}
      <div className="space-y-3 max-w-2xl">
        {news.map((item) => (
          <NewsCard key={item.id} item={item} onUpdated={handleUpdated} />
        ))}
      </div>
    </div>
  );
}