import React, { useEffect, useState } from 'react';
import { Shield, Key, Database, Globe, Clock, ExternalLink, Copy, CheckCircle2 } from 'lucide-react';
import { api } from '../lib/api';
import { useDataStore } from '../stores/data';

interface SystemInfo {
  version: string;
  db_size_kb: number;
  uptime_ms: number;
  budget_limit: number;
  brands_count: number;
  tasks_count: number;
  approvals_count: number;
}

export default function SettingsPage() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [copied, setCopied] = useState(false);
  const brands = useDataStore((s) => s.brands);
  const fetchBrands = useDataStore((s) => s.fetchBrands);

  useEffect(() => {
    fetchBrands();
    // Fetch system info from health endpoint
    fetch('https://mc-core-production.up.railway.app/health')
      .then(r => r.json())
      .then(setSystemInfo)
      .catch(() => null);
  }, [fetchBrands]);

  const copyToken = () => {
    navigator.clipboard.writeText('88701a7238d939f349f1d7');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">Settings</h1>
      <p className="mt-0.5 text-sm text-[var(--mc-ink-muted)]">
        System configuration and connection status
      </p>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">

        {/* ── Connection ── */}
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Globe size={16} className="text-[var(--mc-accent)]" />
              <h2 className="text-sm font-medium text-[var(--mc-ink)]">Connection</h2>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[12px] text-[var(--mc-ink-muted)]">API Base</span>
                <div className="flex items-center gap-2">
                  <code className="text-[11px] font-mono text-[var(--mc-ink)] bg-black/[0.03] px-2 py-0.5 rounded">
                    mc-core-production.up.railway.app
                  </code>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[12px] text-[var(--mc-ink-muted)]">Domain</span>
                <a href="https://mc.agentictrust.app" target="_blank" rel="noopener"
                  className="flex items-center gap-1 text-[12px] text-[var(--mc-accent)] hover:underline">
                  mc.agentictrust.app <ExternalLink size={10} />
                </a>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[12px] text-[var(--mc-ink-muted)]">Status</span>
                <span className="flex items-center gap-1 text-[12px] text-[var(--mc-green)]">
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--mc-green)]" /> Online
                </span>
              </div>
              {systemInfo?.uptime_ms && (
                <div className="flex items-center justify-between">
                  <span className="text-[12px] text-[var(--mc-ink-muted)]">Uptime</span>
                  <span className="text-[12px] text-[var(--mc-ink)]">
                    {Math.floor((systemInfo.uptime_ms / 1000 / 3600))}h {Math.floor((systemInfo.uptime_ms / 1000 / 60) % 60)}m
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Auth ── */}
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Key size={16} className="text-[var(--mc-accent)]" />
              <h2 className="text-sm font-medium text-[var(--mc-ink)]">Auth Token</h2>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <code className="flex-1 text-[11px] font-mono text-[var(--mc-ink)] bg-black/[0.03] px-2 py-1.5 rounded border border-[var(--mc-border)]">
                  88701a7238d939f349f1d7
                </code>
                <button onClick={copyToken}
                  className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-[11px] font-medium text-[var(--mc-accent)] hover:bg-[var(--mc-accent)]/10 transition-colors">
                  {copied ? <CheckCircle2 size={12} /> : <Copy size={12} />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
              <p className="text-[11px] text-[var(--mc-ink-muted)]">
                Used by Kit to authenticate API calls. Stored in TOOLS.md and 1Password.
              </p>
            </div>
          </div>
        </div>

        {/* ── Budget ── */}
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Shield size={16} className="text-[var(--mc-accent)]" />
              <h2 className="text-sm font-medium text-[var(--mc-ink)]">Budget</h2>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[12px] text-[var(--mc-ink-muted)]">Daily Limit</span>
                <span className="text-[13px] font-medium text-[var(--mc-ink)]">
                  ${systemInfo?.budget_limit?.toFixed(2) ?? '2.00'}
                </span>
              </div>
              <p className="text-[11px] text-[var(--mc-ink-muted)]">
                Set via <code className="bg-black/[0.03] px-1 rounded">DAILY_BUDGET_USD</code> env var on Railway.
                Kit checks this before spending. Budget alerts fire at 80% and 95%.
              </p>
            </div>
          </div>
        </div>

        {/* ── Database ── */}
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Database size={16} className="text-[var(--mc-accent)]" />
              <h2 className="text-sm font-medium text-[var(--mc-ink)]">Database</h2>
            </div>

            <div className="space-y-3">
              {systemInfo && (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-[12px] text-[var(--mc-ink-muted)]">Size</span>
                    <span className="text-[12px] text-[var(--mc-ink)]">{systemInfo.db_size_kb} KB</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[12px] text-[var(--mc-ink-muted)]">Brands</span>
                    <span className="text-[12px] text-[var(--mc-ink)]">{systemInfo.brands_count}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[12px] text-[var(--mc-ink-muted)]">Tasks</span>
                    <span className="text-[12px] text-[var(--mc-ink)]">{systemInfo.tasks_count}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[12px] text-[var(--mc-ink-muted)]">Approvals</span>
                    <span className="text-[12px] text-[var(--mc-ink)]">{systemInfo.approvals_count}</span>
                  </div>
                </>
              )}
              <p className="text-[11px] text-[var(--mc-ink-muted)]">
                SQLite (better-sqlite3) with WAL mode. Data persists in Railway volume.
              </p>
            </div>
          </div>
        </div>

        {/* ── Brands ── */}
        <div className="lg:col-span-2 rounded-[1rem] border border-black/[0.08] bg-black/[0.03] p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Clock size={16} className="text-[var(--mc-accent)]" />
              <h2 className="text-sm font-medium text-[var(--mc-ink)]">Brands</h2>
            </div>

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-5">
              {brands.map((brand) => (
                <div key={brand.id} className="flex items-center gap-2 rounded-lg bg-black/[0.03] px-3 py-2.5">
                  <span className="h-2.5 w-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: brand.color }} />
                  <div>
                    <div className="text-[13px] font-medium text-[var(--mc-ink)]">{brand.name}</div>
                    <div className="text-[10px] text-[var(--mc-ink-muted)]">{brand.slug}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
