import React from 'react';
import { FolderOpen, FileText, Code, BookOpen, Wrench, Clock, Link2 } from 'lucide-react';

export default function FilesPage() {
  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">Files</h1>
      <p className="mt-0.5 text-sm text-[var(--mc-ink-muted)]">
        Skill files, outputs, and workspace documents connected to tasks
      </p>

      <div className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Skills */}
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Code size={16} className="text-[var(--mc-accent)]" />
              <h2 className="text-sm font-medium text-[var(--mc-ink)]">Skills</h2>
              <span className="ml-auto text-[11px] text-[var(--mc-ink-muted)]">coming soon</span>
            </div>
            <div className="flex flex-col gap-2">
              {['skill-creator', 'firecrawl', 'xurl', 'coding-agent'].map((skill) => (
                <div key={skill} className="flex items-center gap-2 rounded-lg bg-black/[0.03] px-3 py-2">
                  <FileText size={14} className="text-[var(--mc-ink-muted)]" />
                  <span className="text-[13px] text-[var(--mc-ink)]">{skill}</span>
                  <Link2 size={12} className="ml-auto text-[var(--mc-ink-muted)]" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Brand Docs */}
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen size={16} className="text-[var(--mc-accent)]" />
              <h2 className="text-sm font-medium text-[var(--mc-ink)]">Brand Docs</h2>
              <span className="ml-auto text-[11px] text-[var(--mc-ink-muted)]">coming soon</span>
            </div>
            <div className="flex flex-col gap-2">
              {['BRAND-VOICE.md', 'OFFERS.md', 'STRATEGY.md', 'BRAND-STATUS.md'].map((doc) => (
                <div key={doc} className="flex items-center gap-2 rounded-lg bg-black/[0.03] px-3 py-2">
                  <FileText size={14} className="text-[var(--mc-ink-muted)]" />
                  <span className="text-[13px] text-[var(--mc-ink)] font-mono">{doc}</span>
                  <Link2 size={12} className="ml-auto text-[var(--mc-ink-muted)]" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Outputs */}
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Wrench size={16} className="text-[var(--mc-accent)]" />
              <h2 className="text-sm font-medium text-[var(--mc-ink)]">Recent Outputs</h2>
              <span className="ml-auto text-[11px] text-[var(--mc-ink-muted)]">coming soon</span>
            </div>
            <div className="flex items-center gap-3 rounded-lg bg-black/[0.03] px-4 py-6">
              <FolderOpen size={18} className="text-[var(--mc-ink-muted)]/40" />
              <span className="text-[12px] text-[var(--mc-ink-muted)]/60">No outputs yet — files from completed tasks will appear here</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
