import React, { useState } from 'react';
import { useAuthStore } from '../stores/auth';
import { setAuthToken } from '../lib/api';
import { Button } from '../components/ui';

// ── Generic stub ──

function StubPage({ title, phase }: { title: string; phase?: string }) {
  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">{title}</h1>
      <p className="mt-2 text-sm text-[var(--mc-ink-muted)]">
        {phase ?? 'Phase 2'} — coming soon
      </p>
    </div>
  );
}

// ── Command Center (stub) ──

export function CommandCenterPage() {
  return <StubPage title="Command Center" />;
}

// ── Approvals (stub) ──

export function ApprovalsPage() {
  return <StubPage title="Approvals" />;
}

// ── Files (stub) ──

export function FilesPage() {
  return <StubPage title="Files" />;
}

// ── Costs (stub) ──

export function CostsPage() {
  return <StubPage title="Costs" />;
}

// ── Revenue (stub) ──

export function RevenuePage() {
  return <StubPage title="Revenue" />;
}

// ── Settings (functional token section) ──

export function SettingsPage() {
  const { isAuthenticated, login, logout } = useAuthStore();
  const [tokenInput, setTokenInput] = useState('');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    if (!tokenInput.trim()) return;
    setAuthToken(tokenInput.trim());
    login(tokenInput.trim());
    setTokenInput('');
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleSignOut = () => {
    logout();
  };

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">Settings</h1>
      <p className="mt-2 text-sm text-[var(--mc-ink-muted)]">Phase 1 — token management</p>

      {/* API Token section — double-bezel card */}
      <div className="mt-8 max-w-md">
        <div className="rounded-[1rem] border border-black/[0.08] bg-black/5 p-[6px]">
          <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-5 shadow-sm">
            <h2 className="text-sm font-medium text-[var(--mc-ink)]">Access Token</h2>

            {/* Status indicator */}
            <div className="mt-3 flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  isAuthenticated ? 'bg-[var(--mc-green)]' : 'bg-[var(--mc-red)]'
                }`}
              />
              <span className="text-xs text-[var(--mc-ink-muted)]">
                {isAuthenticated ? 'Authenticated' : 'Not authenticated'}
              </span>
            </div>

            {/* Token input */}
            <div className="mt-4 flex gap-2">
              <input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder={isAuthenticated ? '••••••••••••••••' : 'Enter token'}
                className="flex-1 rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] px-3 py-2 text-sm text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:border-[var(--mc-accent)] focus:outline-none"
              />
              <Button onClick={handleSave} disabled={!tokenInput.trim()}>
                Save
              </Button>
            </div>

            {/* Saved confirmation */}
            {saved && (
              <p className="mt-2 text-xs text-[var(--mc-green)]">Token saved.</p>
            )}

            {/* Sign out */}
            {isAuthenticated && (
              <button
                onClick={handleSignOut}
                className="mt-4 text-xs text-[var(--mc-ink-muted)] underline decoration-[var(--mc-border)] underline-offset-2 transition-colors duration-150 hover:text-[var(--mc-red)]"
              >
                Sign out
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
