import { create } from 'zustand';
import { api } from '../lib/api';
import type {
  Brand,
  Task,
  Approval,
  Activity,
  TaskFilters,
  ApprovalFilters,
  ActivityFilters,
  StatsResponse,
  JeffQueueResponse,
  PaginatedResponse,
} from '../lib/types';
import type { WsEvent } from '../lib/ws';

interface DataState {
  brands: Brand[];
  tasks: Task[];
  tasksTotal: number;
  approvals: Approval[];
  approvalsTotal: number;
  activities: Activity[];
  stats: StatsResponse | null;
  jeffQueue: JeffQueueResponse | null;
  loading: Partial<Record<'brands' | 'tasks' | 'approvals' | 'activities' | 'stats' | 'jeffQueue', boolean>>;
  errors: Partial<Record<string, string>>;

  fetchBrands: () => Promise<void>;
  fetchTasks: (filters?: TaskFilters) => Promise<void>;
  fetchApprovals: (filters?: ApprovalFilters) => Promise<void>;
  fetchActivities: (filters?: ActivityFilters) => Promise<void>;
  fetchStats: () => Promise<void>;
  fetchJeffQueue: () => Promise<void>;
  handleWsEvent: (event: WsEvent) => void;
}

export const useDataStore = create<DataState>()((set, get) => ({
  brands: [],
  tasks: [],
  tasksTotal: 0,
  approvals: [],
  approvalsTotal: 0,
  activities: [],
  stats: null,
  jeffQueue: null,
  loading: {},
  errors: {},

  fetchBrands: async () => {
    set((s) => ({ loading: { ...s.loading, brands: true }, errors: { ...s.errors, brands: undefined } }));
    try {
      const data = await api.get<Brand[]>('/brands');
      set((s) => ({ brands: data, loading: { ...s.loading, brands: false } }));
    } catch (err) {
      set((s) => ({
        loading: { ...s.loading, brands: false },
        errors: { ...s.errors, brands: (err as Error).message },
      }));
    }
  },

  fetchTasks: async (filters) => {
    set((s) => ({ loading: { ...s.loading, tasks: true }, errors: { ...s.errors, tasks: undefined } }));
    try {
      const data = await api.get<PaginatedResponse<Task>>('/tasks', filters as Record<string, string | number | undefined>);
      set((s) => ({
        tasks: data.items,
        tasksTotal: data.total,
        loading: { ...s.loading, tasks: false },
      }));
    } catch (err) {
      set((s) => ({
        loading: { ...s.loading, tasks: false },
        errors: { ...s.errors, tasks: (err as Error).message },
      }));
    }
  },

  fetchApprovals: async (filters) => {
    set((s) => ({ loading: { ...s.loading, approvals: true }, errors: { ...s.errors, approvals: undefined } }));
    try {
      const data = await api.get<PaginatedResponse<Approval>>('/approvals', filters as Record<string, string | number | undefined>);
      set((s) => ({
        approvals: data.items,
        approvalsTotal: data.total,
        loading: { ...s.loading, approvals: false },
      }));
    } catch (err) {
      set((s) => ({
        loading: { ...s.loading, approvals: false },
        errors: { ...s.errors, approvals: (err as Error).message },
      }));
    }
  },

  fetchActivities: async (filters) => {
    set((s) => ({ loading: { ...s.loading, activities: true }, errors: { ...s.errors, activities: undefined } }));
    try {
      const data = await api.get<PaginatedResponse<Activity>>('/activities', filters as Record<string, string | number | undefined>);
      set((s) => ({
        activities: data.items,
        loading: { ...s.loading, activities: false },
      }));
    } catch (err) {
      set((s) => ({
        loading: { ...s.loading, activities: false },
        errors: { ...s.errors, activities: (err as Error).message },
      }));
    }
  },

  fetchStats: async () => {
    set((s) => ({ loading: { ...s.loading, stats: true } }));
    try {
      const data = await api.get<StatsResponse>('/stats');
      set((s) => ({ stats: data, loading: { ...s.loading, stats: false } }));
    } catch (err) {
      set((s) => ({
        loading: { ...s.loading, stats: false },
        errors: { ...s.errors, stats: (err as Error).message },
      }));
    }
  },

  fetchJeffQueue: async () => {
    set((s) => ({ loading: { ...s.loading, jeffQueue: true } }));
    try {
      const data = await api.get<JeffQueueResponse>('/stats/jeff-queue');
      set((s) => ({ jeffQueue: data, loading: { ...s.loading, jeffQueue: false } }));
    } catch (err) {
      set((s) => ({
        loading: { ...s.loading, jeffQueue: false },
        errors: { ...s.errors, jeffQueue: (err as Error).message },
      }));
    }
  },

  handleWsEvent: (event) => {
    const state = get();

    switch (event.type) {
      case 'task.created':
        set({ tasks: [event.data as Task, ...state.tasks] });
        break;

      case 'task.updated': {
        const updated = event.data as Task;
        set({
          tasks: state.tasks.map((t) => (t.id === updated.id ? updated : t)),
        });
        break;
      }

      case 'task.status_changed': {
        const { id, new_status } = event.data as { id: string; old_status: string; new_status: string };
        set({
          tasks: state.tasks.map((t) =>
            t.id === id ? { ...t, status: new_status as Task['status'] } : t,
          ),
        });
        break;
      }

      case 'approval.created':
        set({ approvals: [event.data as Approval, ...state.approvals] });
        break;

      case 'approval.approved': {
        const { id } = event.data as { id: string; title: string };
        set({
          approvals: state.approvals.map((a) =>
            a.id === id ? { ...a, status: 'approved' as const, decided_at: new Date().toISOString() } : a,
          ),
        });
        break;
      }

      case 'approval.rejected': {
        const { id, feedback } = event.data as { id: string; title: string; feedback: string };
        set({
          approvals: state.approvals.map((a) =>
            a.id === id
              ? { ...a, status: 'rejected' as const, feedback, decided_at: new Date().toISOString() }
              : a,
          ),
        });
        break;
      }

      case 'activity.new': {
        const newActivities = [event.data as Activity, ...state.activities];
        set({ activities: newActivities.slice(0, 100) });
        break;
      }

      case 'cost.updated':
        // Refresh stats to get updated cost totals
        state.fetchStats();
        break;
    }
  },
}));
