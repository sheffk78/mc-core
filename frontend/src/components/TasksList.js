import { useState, useEffect, useCallback } from "react";
import { fetchTasks, updateTaskStatus, createTask, fetchUsers } from "@/lib/api";
import { getBrandColor, getBrandName, dueDateStatus } from "@/lib/brands";
import { GripVertical, Plus, Check, User } from "lucide-react";
import NewTaskDialog from "@/components/NewTaskDialog";
import TaskDetailDialog from "@/components/TaskDetailDialog";

const COLUMNS = [
  { key: "open", label: "Open", color: "var(--mc-ink-3)" },
  { key: "in_progress", label: "In Progress", color: "var(--mc-amber)" },
  { key: "approval", label: "Approval", color: "var(--mc-accent)" },
  { key: "completed", label: "Completed", color: "var(--mc-green)" },
];

const COMPLETED_VISIBLE_LIMIT = 10;

export default function TasksList({ brand, brands, onAction, limit, embedded, refreshKey }) {
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [assigneeFilter, setAssigneeFilter] = useState("all");
  const [draggedTask, setDraggedTask] = useState(null);
  const [dragOverCol, setDragOverCol] = useState(null);
  const [showNewTask, setShowNewTask] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [completedLimit, setCompletedLimit] = useState(COMPLETED_VISIBLE_LIMIT);

  const load = useCallback(() => {
    fetchTasks(brand, assigneeFilter).then(setTasks).catch(console.error);
  }, [brand, assigneeFilter]);

  useEffect(() => { load(); }, [load, refreshKey]);

  useEffect(() => {
    fetchUsers().then(setUsers).catch(console.error);
  }, []);

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await updateTaskStatus(taskId, newStatus);
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: newStatus } : t));
      if (onAction) onAction();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDragStart = (e, task) => {
    setDraggedTask(task);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e, colKey) => {
    e.preventDefault();
    setDragOverCol(colKey);
  };

  const handleDragLeave = () => {
    setDragOverCol(null);
  };

  const handleDrop = async (e, colKey) => {
    e.preventDefault();
    setDragOverCol(null);
    if (draggedTask && draggedTask.status !== colKey) {
      await handleStatusChange(draggedTask.id, colKey);
    }
    setDraggedTask(null);
  };

  // Embedded (overview) mode: simple list
  if (embedded) {
    const activeTasks = tasks.filter(t => t.status === "open" || t.status === "in_progress" || t.status === "approval").slice(0, limit || 5);
    if (activeTasks.length === 0) return <div className="mc-empty" data-testid="tasks-empty">No active tasks</div>;

    return (
      <div data-testid="tasks-list">
        {activeTasks.map(task => {
          const brandColor = getBrandColor(task.brand);
          const brandName = getBrandName(task.brand, brands);
          const due = dueDateStatus(task.due_date);
          return (
            <div key={task.id} className="mc-task-item" data-testid={`task-item-${task.id}`}>
              <button
                className="mc-task-checkbox"
                onClick={() => handleStatusChange(task.id, "completed")}
                data-testid={`task-toggle-${task.id}`}
              />
              <div className="mc-task-body">
                <div className="mc-task-title">{task.title}</div>
                <div className="mc-task-meta">
                  <span className="mc-brand-pill" style={{ background: `${brandColor}14`, color: brandColor, fontSize: "9px" }}>
                    {brandName}
                  </span>
                  {due.label && <span className={`mc-task-due ${due.className}`}>{due.label}</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Status buttons config per column
  const getStatusButtons = (colKey, taskId) => {
    const buttons = [];
    if (colKey !== "open") {
      buttons.push({
        label: "Open", status: "open", color: "var(--mc-ink-3)", borderColor: "var(--mc-ink-4)", testId: `task-to-open-${taskId}`
      });
    }
    if (colKey !== "in_progress") {
      buttons.push({
        label: "In Progress", status: "in_progress", color: "var(--mc-amber)", borderColor: "var(--mc-amber)", testId: `task-to-progress-${taskId}`
      });
    }
    if (colKey !== "approval") {
      buttons.push({
        label: "Approval", status: "approval", color: "var(--mc-accent)", borderColor: "var(--mc-accent)", testId: `task-to-approval-${taskId}`
      });
    }
    if (colKey !== "completed") {
      buttons.push({
        label: "Done", status: "completed", color: "var(--mc-green)", borderColor: "var(--mc-green)", testId: `task-to-done-${taskId}`
      });
    }
    return buttons;
  };

  // Full Kanban board
  return (
    <div data-testid="kanban-board">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {COLUMNS.map(col => {
            const count = tasks.filter(t => t.status === col.key).length;
            return (
              <span key={col.key} style={{ fontSize: "11px", color: "var(--mc-ink-3)" }}>
                <span style={{ display: "inline-block", width: "7px", height: "7px", borderRadius: "50%", background: col.color, marginRight: "4px" }} />
                {col.label} ({count})
              </span>
            );
          })}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {/* Assignee filter */}
          <select
            className="mc-dialog-input"
            value={assigneeFilter}
            onChange={e => setAssigneeFilter(e.target.value)}
            data-testid="task-assignee-filter"
            style={{ fontSize: "11px", padding: "4px 8px", width: "auto", minWidth: "100px" }}
          >
            <option value="all">All People</option>
            {users.map(u => (
              <option key={u.id} value={u.name}>{u.name}</option>
            ))}
          </select>
          <button
            className="mc-btn mc-btn-accent mc-btn-sm"
            onClick={() => setShowNewTask(true)}
            data-testid="kanban-new-task-btn"
          >
            <Plus size={12} /> New Task
          </button>
        </div>
      </div>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: "12px",
        alignItems: "flex-start",
      }}>
        {COLUMNS.map(col => {
          const allColTasks = tasks.filter(t => t.status === col.key);
          const isCompleted = col.key === "completed";
          const colTasks = isCompleted ? allColTasks.slice(0, completedLimit) : allColTasks;
          const hasMore = isCompleted && allColTasks.length > completedLimit;
          const isDragOver = dragOverCol === col.key;

          return (
            <div
              key={col.key}
              data-testid={`kanban-column-${col.key}`}
              onDragOver={(e) => handleDragOver(e, col.key)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, col.key)}
              style={{
                background: isDragOver ? "var(--mc-accent-bg)" : "var(--mc-warm-gray)",
                borderRadius: "var(--mc-radius)",
                padding: "12px",
                minHeight: "200px",
                transition: "background-color 200ms",
                border: isDragOver ? "1px dashed var(--mc-accent)" : "1px solid transparent",
              }}
            >
              {/* Column header */}
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                marginBottom: "12px",
                paddingBottom: "8px",
                borderBottom: `2px solid ${col.color}`,
              }}>
                <span style={{
                  fontSize: "10px",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  color: col.color,
                }}>
                  {col.label}
                </span>
                <span style={{
                  fontSize: "10px",
                  fontWeight: 600,
                  color: "var(--mc-ink-4)",
                  background: "var(--mc-white)",
                  padding: "0 6px",
                  borderRadius: "8px",
                }}>
                  {allColTasks.length}
                </span>
              </div>

              {/* Task cards */}
              {colTasks.map(task => {
                const brandColor = getBrandColor(task.brand);
                const brandName = getBrandName(task.brand, brands);
                const due = dueDateStatus(task.due_date);
                const isDone = col.key === "completed";
                const statusButtons = getStatusButtons(col.key, task.id);

                return (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, task)}
                    data-testid={`kanban-card-${task.id}`}
                    style={{
                      background: "var(--mc-white)",
                      border: "1px solid var(--mc-rule)",
                      borderRadius: "var(--mc-radius)",
                      padding: "10px 12px",
                      marginBottom: "8px",
                      cursor: "grab",
                      transition: "box-shadow 150ms, opacity 150ms",
                      opacity: draggedTask?.id === task.id ? 0.4 : 1,
                      boxShadow: "var(--mc-shadow-sm)",
                    }}
                    onMouseEnter={e => e.currentTarget.style.boxShadow = "var(--mc-shadow)"}
                    onMouseLeave={e => e.currentTarget.style.boxShadow = "var(--mc-shadow-sm)"}
                  >
                    <div
                      onClick={() => setSelectedTask(task)}
                      style={{
                        fontSize: "12px",
                        fontWeight: isDone ? 400 : 500,
                        color: isDone ? "var(--mc-ink-3)" : "var(--mc-ink)",
                        textDecoration: isDone ? "line-through" : "none",
                        marginBottom: "6px",
                        lineHeight: 1.35,
                        cursor: "pointer",
                      }}
                      data-testid={`kanban-card-title-${task.id}`}
                    >
                      {task.title}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
                      <span
                        className="mc-brand-pill"
                        style={{ background: `${brandColor}14`, color: brandColor, fontSize: "9px" }}
                      >
                        {brandName}
                      </span>
                      {task.priority && task.priority !== "normal" && (
                        <span style={{
                          fontSize: "9px",
                          fontWeight: 600,
                          textTransform: "uppercase",
                          letterSpacing: "0.04em",
                          color: task.priority === "high" || task.priority === "urgent" ? "var(--mc-red, #c0392b)" : "var(--mc-ink-4)",
                        }}>
                          {task.priority}
                        </span>
                      )}
                      {due.label && (
                        <span className={`mc-task-due ${due.className}`} style={{ fontSize: "9.5px" }}>
                          {due.label}
                        </span>
                      )}
                      {task.assignee && (
                        <span style={{
                          display: "inline-flex", alignItems: "center", gap: "3px",
                          fontSize: "9.5px", color: "var(--mc-ink-3)", fontWeight: 500,
                        }} data-testid={`kanban-card-assignee-${task.id}`}>
                          <User size={9} />
                          {task.assignee}
                        </span>
                      )}
                    </div>
                    {/* Quick status buttons */}
                    <div style={{ display: "flex", gap: "4px", marginTop: "8px", flexWrap: "wrap" }}>
                      {statusButtons.map(btn => (
                        <button
                          key={btn.status}
                          onClick={() => handleStatusChange(task.id, btn.status)}
                          className="mc-btn mc-btn-outline"
                          style={{ fontSize: "9px", padding: "2px 7px", color: btn.color, borderColor: btn.borderColor }}
                          data-testid={btn.testId}
                        >
                          {btn.label}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}

              {colTasks.length === 0 && (
                <div style={{
                  fontSize: "11px",
                  color: "var(--mc-ink-4)",
                  textAlign: "center",
                  padding: "24px 12px",
                  fontStyle: "italic",
                  fontWeight: 300,
                }}>
                  No tasks
                </div>
              )}

              {hasMore && (
                <button
                  className="mc-btn mc-btn-outline"
                  onClick={() => setCompletedLimit(prev => prev + COMPLETED_VISIBLE_LIMIT)}
                  data-testid="completed-load-more-btn"
                  style={{
                    width: "100%",
                    fontSize: "10px",
                    padding: "6px 0",
                    marginTop: "4px",
                    color: "var(--mc-ink-3)",
                    borderColor: "var(--mc-rule)",
                  }}
                >
                  Load more ({allColTasks.length - completedLimit} remaining)
                </button>
              )}
            </div>
          );
        })}
      </div>

      <NewTaskDialog
        open={showNewTask}
        onOpenChange={setShowNewTask}
        brands={brands}
        defaultBrand={brand !== "all" ? brand : ""}
        onCreated={() => { load(); if (onAction) onAction(); setShowNewTask(false); }}
      />

      <TaskDetailDialog
        open={!!selectedTask}
        onOpenChange={(v) => { if (!v) setSelectedTask(null); }}
        task={selectedTask}
        brands={brands}
        onUpdated={() => { load(); if (onAction) onAction(); }}
      />
    </div>
  );
}
