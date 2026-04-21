import { create } from 'zustand';
import { api } from '../lib/api';
import type {
  Brand,
  Task,
  Approval,
  Activity,
  News,
  TaskFilters,
  ApprovalFilters,
  ActivityFilters,
  NewsFilters,
  StatsResponse,
  JeffQueueResponse,
  PaginatedResponse,
} from '../lib/types';
import type { WsEvent } from '../lib/ws';

interface DataState {
  brands: Brand[];
  tasks: Task[];
  tasksTotal: number;
  jeffOpenTasks: Task[];
  approvals: Approval[];
  approvalsTotal: number;
  activities: Activity[];
  news: News[];
  newsTotal: number;
  stats: StatsResponse | null;
  jeffQueue: JeffQueueResponse | null;
  loading: Partial<Record<'brands' | 'tasks' | 'jeffOpenTasks' | 'approvals' | 'activities' | 'news' | 'stats' | 'jeffQueue', boolean>>;
  errors: Partial<Record<string, string>>;

  fetchBrands: () => Promise<void>;
  fetchTasks: (filters?: TaskFilters) => Promise<void>;
  fetchJeffOpenTasks: (brand?: string) => Promise<void>;
  fetchApprovals: (filters?: ApprovalFilters) => Promise<void>;
  fetchActivities: (filters?: ActivityFilters) => Promise<void>;
  fetchStats: () => Promise<void>;
  fetchJeffQueue: () => Promise<void>;
  fetchNews: (filters?: NewsFilters) => Promise<void>;
  handleWsEvent: (event: WsEvent) => void;
}

export const useDataStore = create<DataState>()((set, get) => ({
  brands: [],
  tasks: [],
  tasksTotal: 0,
  jeffOpenTasks: [],
  approvals: [],
  approvalsTotal: 0,
  activities: [],
  news: [],
  newsTotal: 0,
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

  fetchJeffOpenTasks: async (brand?: string) => {
    set((s) => ({ loading: { ...s.loading, jeffOpenTasks: true }, errors: { ...s.errors, jeffOpenTasks: undefined } }));
    try {
      const params: Record<string, string> = { status: 'open', assignee: 'jeff' };
      if (brand) params.brand = brand;
      const data = await api.get<PaginatedResponse<Task>>('/tasks', params);
      set((s) => ({
        jeffOpenTasks: data.items,
        loading: { ...s.loading, jeffOpenTasks: false },
      }));;
    } catch (err) {
      set((s) => ({
        loading: { ...s.loading, jeffOpenTasks: false },
        errors: { ...s.errors, jeffOpenTasks: (err as Error).message },
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

  fetchNews: async (filters) => {
    set((s) => ({ loading: { ...s.loading, news: true }, errors: { ...s.errors, news: undefined } }));
    try {
      const data = await api.get<PaginatedResponse<News>>('/news', filters as Record<string, string | number | undefined>);
      set((s) => ({
        news: data.items,
        newsTotal: data.total,
        loading: { ...s.loading, news: false },
      }));
    } catch (err) {
      set((s) => ({
        loading: { ...s.loading, news: false },
        errors: { ...s.errors, news: (err as Error).message },
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
      case 'task.created': {
        const newTask = event.data as Task;
        set({ tasks: [newTask, ...state.tasks] });
        if (newTask.status === 'open' && newTask.assignee === 'jeff') {
          set({ jeffOpenTasks: [newTask, ...state.jeffOpenTasks] });
        }
        break;
      }

      case 'task.updated': {
        const updated = event.data as Task;
        set({
          tasks: state.tasks.map((t) => (t.id === updated.id ? updated : t)),
        });
        // Sync jeffOpenTasks
        if (updated.status === 'open' && updated.assignee === 'jeff') {
          const exists = state.jeffOpenTasks.some((t) => t.id === updated.id);
          set({
            jeffOpenTasks: exists
              ? state.jeffOpenTasks.map((t) => (t.id === updated.id ? updated : t))
              : [updated, ...state.jeffOpenTasks],
          });
        } else {
          set({ jeffOpenTasks: state.jeffOpenTasks.filter((t) => t.id !== updated.id) });
        }
        break;
      }

      case 'task.status_changed': {
        const { id, new_status } = event.data as { id: string; old_status: string; new_status: string };
        set({
          tasks: state.tasks.map((t) =>
            t.id === id ? { ...t, status: new_status as Task['status'] } : t,
          ),
        });
        // Remove from jeffOpenTasks if no longer open
        if (new_status !== 'open') {
          set({ jeffOpenTasks: state.jeffOpenTasks.filter((t) => t.id !== id) });
        }
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

      case 'news.created': {
        const newNews = event.data as News;
        set({ news: [newNews, ...state.news] });
        break;
      }

      case 'news.updated': {
        const updatedNews = event.data as News;
        set({
          news: state.news.map((n) => (n.id === updatedNews.id ? updatedNews : n)),
        });
        break;
      }

      case 'cost.updated':
        // Refresh stats to get updated cost totals
        state.fetchStats();
        break;
    }
  },
}));
