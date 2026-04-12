import React, { useEffect, useState, useMemo } from 'react';
import { FolderOpen, FileText, Code, BookOpen, Settings, Calendar, Search, Link2, ExternalLink } from 'lucide-react';
import { api } from '../lib/api';
import { useDataStore } from '../stores/data';

interface FileItem {
  id: string;
  path: string;
  name: string;
  label: string;
  category: string;
  brand_id: string | null;
  brand_name: string | null;
  brand_slug: string | null;
  preview: string;
  task_count: number;
  created_at: string;
}

const CATEGORY_CONFIG: Record<string, { icon: React.ReactNode; color: string; title: string }> = {
  skill: { icon: <Code size={16} />, color: 'var(--mc-accent)', title: 'Skills' },
  brand_doc: { icon: <BookOpen size={16} />, color: 'var(--mc-green)', title: 'Brand Docs' },
  daily_note: { icon: <Calendar size={16} />, color: 'var(--mc-yellow)', title: 'Daily Notes' },
  config: { icon: <Settings size={16} />, color: 'var(--mc-ink-muted)', title: 'Config' },
  output: { icon: <FolderOpen size={16} />, color: 'var(--mc-red)', title: 'Outputs' },
  other: { icon: <FileText size={16} />, color: 'var(--mc-ink-muted)', title: 'Other' },
};

function FileCard({ file }: { file: FileItem }) {
  const cfg = CATEGORY_CONFIG[file.category] ?? CATEGORY_CONFIG.other;

  return (
    <div className="group rounded-[0.75rem] border border-black/[0.08] bg-black/[0.03] p-[4px] transition-all duration-200 hover:border-black/[0.14]">
      <div className="rounded-[calc(0.75rem-4px)] bg-[var(--mc-surface)] p-3 shadow-sm">
        <div className="flex items-start gap-2">
          <span style={{ color: cfg.color }} className="mt-0.5">{cfg.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-[13px] font-medium text-[var(--mc-ink)]">{file.name}</span>
              {file.brand_slug && (
                <span className="rounded-full px-1.5 py-0.5 text-[9px] font-medium" style={{
                  backgroundColor: `color-mix(in oklch, var(--mc-accent) 10%, transparent)`,
                  color: 'var(--mc-accent)',
                }}>
                  {file.brand_slug}
                </span>
              )}
            </div>
            <div className="mt-0.5 font-mono text-[11px] text-[var(--mc-ink-muted)] truncate">{file.path}</div>
          </div>
          {file.task_count > 0 && (
            <span className="flex items-center gap-1 rounded-full bg-[var(--mc-accent)]/10 px-1.5 py-0.5 text-[10px] font-medium text-[var(--mc-accent)]">
              <Link2 size={10} /> {file.task_count}
            </span>
          )}
        </div>
        {file.preview && (
          <div className="mt-2 line-clamp-2 text-[11px] text-[var(--mc-ink-muted)] leading-relaxed">
            {file.preview}
          </div>
        )}
      </div>
    </div>
  );
}

export default function FilesPage() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    api.get<{ items: FileItem[] }>('/files')
      .then((res) => setFiles(res.items))
      .catch(() => setFiles([]))
      .finally(() => setLoading(false));
  }, []);

  const grouped = useMemo(() => {
    const filtered = search
      ? files.filter((f) =>
          f.name.toLowerCase().includes(search.toLowerCase()) ||
          f.path.toLowerCase().includes(search.toLowerCase()) ||
          (f.brand_slug?.toLowerCase().includes(search.toLowerCase()))
        )
      : files;

    const groups: Record<string, FileItem[]> = {};
    for (const f of filtered) {
      if (!groups[f.category]) groups[f.category] = [];
      groups[f.category].push(f);
    }
    return groups;
  }, [files, search]);

  const categories = Object.keys(CATEGORY_CONFIG);

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">Files</h1>
          <p className="mt-0.5 text-sm text-[var(--mc-ink-muted)]">
            Skills, docs, and outputs Kit references in tasks
          </p>
        </div>
        <span className="text-sm text-[var(--mc-ink-muted)]">
          {loading ? '…' : `${files.length} files`}
        </span>
      </div>

      {/* Search */}
      <div className="mt-6 flex items-center gap-2">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--mc-ink-muted)]" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search files…"
            className="w-full rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] py-1.5 pl-8 pr-3 text-[13px] text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:border-[var(--mc-accent)] focus:outline-none"
          />
        </div>
      </div>

      {/* Empty state */}
      {!loading && files.length === 0 && (
        <div className="mt-12 flex flex-col items-center gap-3 text-center">
          <FolderOpen size={32} className="text-[var(--mc-ink-muted)]/30" />
          <div>
            <div className="text-sm font-medium text-[var(--mc-ink)]">No files registered yet</div>
            <div className="mt-1 text-[12px] text-[var(--mc-ink-muted)]">
              Kit registers files as it works on tasks. Skills, brand docs, and outputs will appear here automatically.
            </div>
          </div>
        </div>
      )}

      {/* Grouped grid */}
      {categories.map((cat) => {
        const items = grouped[cat];
        if (!items || items.length === 0) return null;
        const cfg = CATEGORY_CONFIG[cat];

        return (
          <div key={cat} className="mt-8">
            <div className="flex items-center gap-2 mb-3">
              <span style={{ color: cfg.color }}>{cfg.icon}</span>
              <h2 className="text-sm font-medium text-[var(--mc-ink)]">{cfg.title}</h2>
              <span className="text-[11px] text-[var(--mc-ink-muted)]">({items.length})</span>
            </div>
            <div className="grid grid-cols-1 gap-2 lg:grid-cols-2 xl:grid-cols-3">
              {items.map((file) => (
                <FileCard key={file.id} file={file} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
