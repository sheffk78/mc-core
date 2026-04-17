import React from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { BudgetBar } from './BudgetBar';
import { useDashboardStore } from '../../stores/dashboard';

export function Layout({ children }: { children: React.ReactNode }) {
  const sidebarOpen = useDashboardStore((s) => s.sidebarOpen);

  return (
    <div className="flex min-h-screen bg-[var(--mc-bg)]">
      {/* Desktop sidebar — visible on md+ screens only */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          onClick={() => useDashboardStore.getState().setSidebarOpen(false)}
        />
      )}

      {/* Mobile sidebar drawer */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-[220px] transform transition-transform duration-300 md:hidden ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Sidebar />
      </div>

      {/* Main column */}
      <div className="flex flex-1 flex-col overflow-hidden md:ml-[220px]">
        <Topbar />
        <BudgetBar />
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
