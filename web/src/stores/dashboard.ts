import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type View =
  | 'command-center'
  | 'jeff-queue'
  | 'activity-stream'
  | 'tasks'
  | 'approvals'
  | 'files'
  | 'costs'
  | 'revenue'
  | 'settings'
  | 'chat';

interface DashboardState {
  activeBrand: string | null;
  activeView: View;
  sidebarOpen: boolean;
  wsConnected: boolean;

  setActiveBrand: (slug: string | null) => void;
  setActiveView: (view: View) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setWsConnected: (connected: boolean) => void;
}

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      activeBrand: null,
      activeView: 'command-center',
      sidebarOpen: false,
      wsConnected: false,

      setActiveBrand: (slug) => set({ activeBrand: slug }),
      setActiveView: (view) => set({ activeView: view }),
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setWsConnected: (connected) => set({ wsConnected: connected }),
    }),
    {
      name: 'mc_dashboard',
      partialize: (state) => ({
        activeBrand: state.activeBrand,
        activeView: state.activeView,
      }),
    },
  ),
);
