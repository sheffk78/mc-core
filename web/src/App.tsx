import React, { Suspense, lazy, useEffect, useState } from 'react';
import { Layout } from './components/layout/Layout';
import { useAuthStore } from './stores/auth';
import { useDashboardStore } from './stores/dashboard';
import { useDataStore } from './stores/data';
import { subscribe } from './lib/ws';

// ── Lazy page imports ──

const DashboardOverview = lazy(() => import('./views/DashboardOverview'));
const JeffQueueView = lazy(() => import('./views/JeffQueue'));
const ActivityStreamView = lazy(() => import('./views/ActivityStream'));
const TasksPage = lazy(() => import('./views/TasksPage'));

const ApprovalsPage = lazy(() => import('./views/ApprovalsPage'));
const FilesPage = lazy(() =>
  import('./views/stubs').then((m) => ({ default: m.FilesPage })),
);
const CostsPage = lazy(() =>
  import('./views/stubs').then((m) => ({ default: m.CostsPage })),
);
const RevenuePage = lazy(() =>
  import('./views/stubs').then((m) => ({ default: m.RevenuePage })),
);
const SettingsPage = lazy(() =>
  import('./views/stubs').then((m) => ({ default: m.SettingsPage })),
);

// ── Loading pane ──

function LoadingPane() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center bg-[var(--mc-bg)]">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--mc-border)] border-t-[var(--mc-accent)]" />
    </div>
  );
}

// ── Auth gate ──

function AuthGate({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, login } = useAuthStore();
  const [tokenInput, setTokenInput] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return <>{children}</>;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenInput.trim()) return;

    setLoading(true);
    setError('');

    try {
      const res = await fetch('/health', {
        headers: { Authorization: `Bearer ${tokenInput}` },
      });

      if (res.ok) {
        login(tokenInput);
      } else {
        setError('Invalid token');
      }
    } catch {
      setError('Connection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--mc-bg)] px-4">
      {/* Double-bezel card */}
      <div className="rounded-[1rem] border border-black/[0.08] bg-black/5 p-1.5">
        <div className="rounded-[calc(1rem-6px)] bg-[var(--mc-surface)] p-6">
          <h1 className="font-display text-xl font-bold text-[var(--mc-ink)]">
            Mission Control
          </h1>
          <p className="mt-1 text-sm text-[var(--mc-ink-muted)]">
            Enter your access token to continue
          </p>

          <form onSubmit={handleSubmit} className="mt-6">
            <input
              type="password"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              placeholder="Access token"
              disabled={loading}
              className="w-full rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] px-3 py-2 text-sm text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:border-[var(--mc-accent)] focus:outline-none disabled:opacity-50"
            />

            {error && <p className="mt-1 text-xs text-[var(--mc-red)]">{error}</p>}

            <button
              type="submit"
              disabled={loading || !tokenInput.trim()}
              className="mt-4 w-full rounded-lg bg-[var(--mc-accent)] py-2 text-sm font-medium text-white transition-all duration-200 hover:opacity-90 disabled:opacity-50"
              style={{ transitionTimingFunction: 'cubic-bezier(0.32, 0.72, 0, 1)' }}
            >
              {loading ? (
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/50 border-t-transparent" />
              ) : (
                'Connect'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ── View router ──

function ViewRouter() {
  const activeView = useDashboardStore((s) => s.activeView);

  const viewMap: Record<string, React.LazyExoticComponent<() => React.JSX.Element>> = {
    'command-center': DashboardOverview,
    'jeff-queue': JeffQueueView,
    'activity-stream': ActivityStreamView,
    tasks: TasksPage,
    approvals: ApprovalsPage,
    files: FilesPage,
    costs: CostsPage,
    revenue: RevenuePage,
    settings: SettingsPage,
  };

  const Page = viewMap[activeView] ?? DashboardOverview;

  return (
    <Suspense fallback={<LoadingPane />}>
      <Page />
    </Suspense>
  );
}

// ── App ──

export default function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    if (!isAuthenticated) return;

    // Fetch initial data after auth
    useDataStore.getState().fetchBrands();
    useDataStore.getState().fetchStats();
    useDataStore.getState().fetchJeffQueue();

    // Subscribe to all WS events
    const unsub = subscribe('*', (event) => {
      useDataStore.getState().handleWsEvent(event);
    });

    // Poll WS state (the ws module manages the actual connection)
    const interval = setInterval(() => {
      // Import dynamically to avoid circular deps
      import('./lib/ws').then((mod) => {
        useDashboardStore.getState().setWsConnected(mod.getConnected());
      });
    }, 2000);

    return () => {
      unsub();
      clearInterval(interval);
    };
  }, [isAuthenticated]);

  return (
    <AuthGate>
      <Layout>
        <ViewRouter />
      </Layout>
    </AuthGate>
  );
}
