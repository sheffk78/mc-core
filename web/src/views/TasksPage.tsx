import React, { useEffect, useMemo, useCallback, useState } from 'react';
import { Plus } from 'lucide-react';
import { useDashboardStore } from '../stores/dashboard';
import { useDataStore } from '../stores/data';
import { TaskCard, TaskCardSkeleton } from '../components/tasks/TaskCard';
import { TaskFilters, type TaskFilterState } from '../components/tasks/TaskFilters';
import { TaskDetailModal } from '../components/tasks/TaskDetailModal';
import { NewTaskModal } from '../components/tasks/NewTaskModal';
import type { Task, TaskStatus, RiskTier, Assignee, Priority } from '../lib/types';

// ── Sort + filter helpers ──

const PRIORITY_ORDER: Record<Priority, number> = {
  critical: 0,
  high: 1,
  normal: 2,
  low: 3,
};

function applyClientFilters(tasks: Task[], filters: TaskFilterState): Task[] {
  let result = tasks;

  // Keyword search (client-side)
  if (filters.search.trim()) {
    const q = filters.search.toLowerCase();
    result = result.filter(
      (t) =>
        t.title.toLowerCase().includes(q) ||
        (t.agent_note ?? '').toLowerCase().includes(q) ||
        (t.category ?? '').toLowerCase().includes(q),
    );
  }

  // Sort
  switch (filters.sort) {
    case 'newest':
      result = [...result].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      );
      break;
    case 'oldest':
      result = [...result].sort(
        (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      );
      break;
    case 'due_date':
      result = [...result].sort((a, b) => {
        if (!a.due_date && !b.due_date) return 0;
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
      });
      break;
    case 'priority':
      result = [...result].sort(
        (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority],
      );
      break;
  }

  return result;
}

// ── TasksPage ──

export default function TasksPage() {
  const activeBrand = useDashboardStore((s) => s.activeBrand);
  const { tasks, tasksTotal, loading, fetchTasks } = useDataStore();

  // Track the server-side filters that trigger API re-fetch
  const [apiFilters, setApiFilters] = useState<{
    brand?: string;
    status?: TaskStatus;
    risk_tier?: RiskTier;
    assignee?: Assignee;
  }>({});

  // Client-side filter state (search + sort)
  const [clientFilters, setClientFilters] = useState<TaskFilterState>({
    status: '',
    risk_tier: '',
    assignee: '',
    sort: 'newest',
    search: '',
  });
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showNewTask, setShowNewTask] = useState(false);

  // Fetch tasks when brand or API-level filters change
  useEffect(() => {
    fetchTasks({
      brand: activeBrand ?? undefined,
      ...apiFilters,
    });
  }, [activeBrand, apiFilters, fetchTasks]);

  // Handle filter changes — split into API filters and client filters
  const handleFilterChange = useCallback((filters: TaskFilterState) => {
    setClientFilters(filters);

    // API-level filters: status, risk_tier, assignee, brand
    setApiFilters({
      status: filters.status || undefined,
      risk_tier: filters.risk_tier || undefined,
      assignee: filters.assignee || undefined,
    });
  }, []);

  // Apply client-side search + sort on top of API results
  const visibleTasks = useMemo(
    () => applyClientFilters(tasks, clientFilters),
    [tasks, clientFilters],
  );

  const isLoading = loading.tasks;

  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      {/* Header */}
      <div className="flex items-baseline justify-between">
        <h1 className="font-display text-2xl font-bold text-[var(--mc-ink)]">Tasks</h1>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowNewTask(true)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--mc-accent)] px-3 py-1.5 text-[13px] font-medium text-white transition-colors hover:bg-[var(--mc-accent)]/90"
          >
            <Plus size={14} />
            New Task
          </button>
          <span className="text-sm text-[var(--mc-ink-muted)]">
            {isLoading ? '…' : `${tasksTotal} task${tasksTotal !== 1 ? 's' : ''}`}
          </span>
        </div>
      </div>

      {/* Filters */}
      <TaskFilters onChange={handleFilterChange} />

      {/* Task grid */}
      {isLoading ? (
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <TaskCardSkeleton />
          <TaskCardSkeleton />
          <TaskCardSkeleton />
        </div>
      ) : visibleTasks.length === 0 ? (
        <div className="flex flex-1 items-center justify-center py-20">
          <p className="text-sm text-[var(--mc-ink-muted)]">No tasks yet.</p>
        </div>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          {visibleTasks.map((task) => (
            <TaskCard key={task.id} task={task} onClick={() => setSelectedTask(task)} />
          ))}
        </div>
      )}

      {/* New Task Modal */}
      {showNewTask && (
        <NewTaskModal
          onClose={() => setShowNewTask(false)}
          onCreated={() => {
            setShowNewTask(false);
            fetchTasks({
              brand: activeBrand ?? undefined,
              ...apiFilters,
            });
          }}
        />
      )}

      {/* Task Detail Modal */}
      {selectedTask && (
        <TaskDetailModal
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          onUpdated={(updated) => {
            setSelectedTask(updated);
            fetchTasks({
              brand: activeBrand ?? undefined,
              ...apiFilters,
            });
          }}
        />
      )}
    </div>
  );
}
