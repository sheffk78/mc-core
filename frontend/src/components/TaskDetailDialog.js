import { useState, useEffect } from "react";
import { updateTask, updateTaskStatus, deleteTask, fetchUsers, discardItem } from "@/lib/api";
import { getBrandColor, getBrandName } from "@/lib/brands";
import {
  CalendarDays,
  Flag,
  MessageSquare,
  Pencil,
  Check,
  X,
  Clock,
  ArrowRight,
  User,
  Trash2,
  Link2,
  Mail,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

const STATUS_CONFIG = {
  open: { label: "Open", color: "var(--mc-ink-3)" },
  in_progress: { label: "In Progress", color: "var(--mc-amber)" },
  approval: { label: "Approval", color: "var(--mc-accent)" },
  completed: { label: "Completed", color: "var(--mc-green)" },
};

const PRIORITY_CONFIG = {
  low: { label: "Low", color: "var(--mc-ink-4)" },
  normal: { label: "Normal", color: "var(--mc-ink-3)" },
  high: { label: "High", color: "var(--mc-accent)" },
  urgent: { label: "Urgent", color: "var(--mc-red, #c0392b)" },
};

export default function TaskDetailDialog({ open, onOpenChange, task, brands, onUpdated }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState("normal");
  const [assignee, setAssignee] = useState("");
  const [userNote, setUserNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmTrash, setConfirmTrash] = useState(false);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    if (open) {
      fetchUsers().then(setUsers).catch(console.error);
    }
  }, [open]);

  useEffect(() => {
    if (task && open) {
      setTitle(task.title || "");
      setDescription(task.description || "");
      setDueDate(task.due_date ? task.due_date.split("T")[0] : "");
      setPriority(task.priority || "normal");
      setAssignee(task.assignee || "");
      setUserNote(task.user_note || "");
      setEditing(false);
      setConfirmTrash(false);
    }
  }, [task, open]);

  if (!task) return null;

  const brandColor = getBrandColor(task.brand);
  const brandName = getBrandName(task.brand, brands);
  const statusCfg = STATUS_CONFIG[task.status] || STATUS_CONFIG.open;
  const priorityCfg = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.normal;

  const handleSave = async () => {
    setSaving(true);
    try {
      const updates = {};
      if (title !== task.title) updates.title = title;
      if (description !== (task.description || "")) updates.description = description;
      if (userNote !== (task.user_note || "")) updates.user_note = userNote;
      if (priority !== (task.priority || "normal")) updates.priority = priority;
      if (assignee !== (task.assignee || "")) updates.assignee = assignee;
      const newDueDate = dueDate ? new Date(dueDate).toISOString() : "";
      const oldDueDate = task.due_date ? task.due_date.split("T")[0] : "";
      if (dueDate !== oldDueDate) updates.due_date = newDueDate;

      if (Object.keys(updates).length > 0) {
        await updateTask(task.id, updates);
      }
      setEditing(false);
      if (onUpdated) onUpdated();
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await updateTaskStatus(task.id, newStatus);
      // Auto-dismiss linked approval when task is completed
      if (newStatus === "completed" && task.metadata?.approval_id) {
        try {
          await discardItem(task.metadata.approval_id);
        } catch (e) {
          console.warn("Could not auto-dismiss linked approval:", e);
        }
      }
      if (onUpdated) onUpdated();
      onOpenChange(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleTrash = async () => {
    setDeleting(true);
    try {
      await deleteTask(task.id);
      if (onUpdated) onUpdated();
      onOpenChange(false);
    } catch (e) {
      console.error(e);
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (d) => {
    if (!d) return "Not set";
    try {
      return new Date(d).toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        year: "numeric",
        timeZone: "America/Denver",
      });
    } catch {
      return d;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-[560px]"
        style={{ fontFamily: "'Libre Franklin', sans-serif", maxHeight: "85vh", overflow: "auto", overflowX: "hidden" }}
      >
        <DialogHeader>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
            <span
              style={{
                fontSize: "9px",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                padding: "2px 8px",
                borderRadius: "2px",
                background: `${statusCfg.color}18`,
                color: statusCfg.color,
                border: `1px solid ${statusCfg.color}40`,
              }}
              data-testid="task-detail-status"
            >
              {statusCfg.label}
            </span>
            <span
              className="mc-brand-pill"
              style={{ background: `${brandColor}14`, color: brandColor, fontSize: "9px" }}
            >
              {brandName}
            </span>
            {task.priority && task.priority !== "normal" && (
              <span
                style={{
                  fontSize: "9px",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  color: priorityCfg.color,
                }}
              >
                <Flag size={9} style={{ display: "inline", marginRight: "2px", verticalAlign: "-1px" }} />
                {priorityCfg.label}
              </span>
            )}
          </div>

          {editing ? (
            <input
              className="mc-dialog-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              data-testid="task-detail-title-input"
              style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                fontSize: "18px",
                fontWeight: 500,
              }}
            />
          ) : (
            <DialogTitle
              style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                fontSize: "18px",
                fontWeight: 500,
                cursor: "pointer",
              }}
              data-testid="task-detail-title"
            >
              {task.title}
            </DialogTitle>
          )}
          <DialogDescription className="sr-only">Task details and actions</DialogDescription>
        </DialogHeader>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px", padding: "4px 0 12px" }}>
          {/* Metadata row — always editable */}
          <div
            style={{
              display: "flex",
              gap: "20px",
              padding: "12px 16px",
              background: "var(--mc-off-white)",
              borderRadius: "var(--mc-radius)",
              border: "1px solid var(--mc-rule)",
              flexWrap: "wrap",
            }}
          >
            {/* Due date — always editable */}
            <div style={{ flex: "1 1 140px" }}>
              <div style={{ fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--mc-ink-4)", marginBottom: "4px" }}>
                <CalendarDays size={10} style={{ display: "inline", marginRight: "4px", verticalAlign: "-1px" }} />
                Due Date
              </div>
              <input
                type="date"
                className="mc-dialog-input"
                value={dueDate}
                onChange={(e) => {
                  setDueDate(e.target.value);
                  const newVal = e.target.value ? new Date(e.target.value).toISOString() : "";
                  updateTask(task.id, { due_date: newVal }).then(() => { if (onUpdated) onUpdated(); }).catch(console.error);
                }}
                data-testid="task-detail-due-input"
                style={{ fontSize: "12px", padding: "4px 8px", background: "var(--mc-white)" }}
              />
            </div>

            {/* Priority — always editable */}
            <div style={{ flex: "1 1 100px" }}>
              <div style={{ fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--mc-ink-4)", marginBottom: "4px" }}>
                <Flag size={10} style={{ display: "inline", marginRight: "4px", verticalAlign: "-1px" }} />
                Priority
              </div>
              <select
                className="mc-dialog-input"
                value={priority}
                onChange={(e) => {
                  setPriority(e.target.value);
                  updateTask(task.id, { priority: e.target.value }).then(() => { if (onUpdated) onUpdated(); }).catch(console.error);
                }}
                data-testid="task-detail-priority-select"
                style={{ fontSize: "12px", padding: "4px 8px", color: PRIORITY_CONFIG[priority]?.color || "var(--mc-ink)", fontWeight: 500, background: "var(--mc-white)" }}
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            {/* Assignee — always editable */}
            <div style={{ flex: "1 1 100px" }}>
              <div style={{ fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--mc-ink-4)", marginBottom: "4px" }}>
                <User size={10} style={{ display: "inline", marginRight: "4px", verticalAlign: "-1px" }} />
                Assigned To
              </div>
              <select
                className="mc-dialog-input"
                value={assignee}
                onChange={(e) => {
                  setAssignee(e.target.value);
                  updateTask(task.id, { assignee: e.target.value }).then(() => { if (onUpdated) onUpdated(); }).catch(console.error);
                }}
                data-testid="task-detail-assignee-select"
                style={{ fontSize: "12px", padding: "4px 8px", background: "var(--mc-white)" }}
              >
                <option value="">Unassigned</option>
                {users.map(u => (
                  <option key={u.id} value={u.name}>{u.name}</option>
                ))}
              </select>
            </div>

            {/* Created */}
            <div style={{ flex: "1 1 140px" }}>
              <div style={{ fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--mc-ink-4)", marginBottom: "4px" }}>
                <Clock size={10} style={{ display: "inline", marginRight: "4px", verticalAlign: "-1px" }} />
                Created
              </div>
              <div style={{ fontSize: "12.5px", color: "var(--mc-ink-2)" }}>
                {formatDate(task.created_at)}
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <div style={{ fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--mc-ink-4)", marginBottom: "6px" }}>
              Description
            </div>
            {editing ? (
              <textarea
                className="mc-dialog-input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add a description..."
                data-testid="task-detail-description-input"
                rows={8}
                style={{ resize: "vertical", minHeight: "140px", lineHeight: 1.5 }}
              />
            ) : (
              <div
                style={{
                  fontSize: "13px",
                  lineHeight: 1.6,
                  color: task.description ? "var(--mc-ink-2)" : "var(--mc-ink-4)",
                  fontStyle: task.description ? "normal" : "italic",
                  padding: "10px 14px",
                  background: "var(--mc-white)",
                  border: "1px solid var(--mc-rule)",
                  borderRadius: "var(--mc-radius)",
                  minHeight: "120px",
                  maxHeight: "280px",
                  overflowY: "auto",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  overflowWrap: "anywhere",
                }}
                data-testid="task-detail-description"
              >
                {task.description || "No description"}
              </div>
            )}
          </div>

          {/* Agent Note (read-only — from Kit) */}
          {task.agent_note && (
            <div>
              <div style={{ fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--mc-ink-4)", marginBottom: "6px" }}>
                <MessageSquare size={10} style={{ display: "inline", marginRight: "4px", verticalAlign: "-1px" }} />
                Kit's Note
              </div>
              <div
                style={{
                  fontSize: "12.5px",
                  lineHeight: 1.5,
                  color: "var(--mc-ink-2)",
                  padding: "10px 14px",
                  background: "var(--mc-accent-bg)",
                  borderRadius: "var(--mc-radius)",
                  borderLeft: "3px solid var(--mc-accent)",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  overflowWrap: "anywhere",
                  maxHeight: "240px",
                  overflow: "auto",
                }}
                data-testid="task-detail-agent-note"
              >
                {task.agent_note}
              </div>
            </div>
          )}

          {/* Metadata (read-only — from Kit integration) */}
          {task.metadata && Object.keys(task.metadata).length > 0 && (
            <div>
              <div style={{ fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--mc-ink-4)", marginBottom: "6px" }}>
                <Link2 size={10} style={{ display: "inline", marginRight: "4px", verticalAlign: "-1px" }} />
                Linked Data
              </div>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "6px 16px",
                  padding: "10px 14px",
                  background: "var(--mc-warm-gray)",
                  borderRadius: "var(--mc-radius)",
                  border: "1px solid var(--mc-rule)",
                }}
                data-testid="task-detail-metadata"
              >
                {task.metadata.send_method && (
                  <div style={{ fontSize: "11px", color: "var(--mc-ink-3)" }}>
                    <Mail size={10} style={{ display: "inline", marginRight: "3px", verticalAlign: "-1px" }} />
                    <span style={{ fontWeight: 600 }}>Method:</span> {task.metadata.send_method}
                  </div>
                )}
                {task.metadata.reply_to_address && (
                  <div style={{ fontSize: "11px", color: "var(--mc-ink-3)", wordBreak: "break-all" }}>
                    <span style={{ fontWeight: 600 }}>Reply to:</span> {task.metadata.reply_to_address}
                  </div>
                )}
                {task.metadata.agentmail_thread_id && (
                  <div style={{ fontSize: "11px", color: "var(--mc-ink-4)", fontFamily: "monospace" }}>
                    Thread: {task.metadata.agentmail_thread_id.slice(0, 16)}...
                  </div>
                )}
                {task.metadata.approval_id && (
                  <div style={{ fontSize: "11px", color: "var(--mc-accent)" }}>
                    <Link2 size={10} style={{ display: "inline", marginRight: "3px", verticalAlign: "-1px" }} />
                    <span style={{ fontWeight: 600 }}>Linked approval</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* User Note */}
          <div>
            <div style={{ fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--mc-ink-4)", marginBottom: "6px" }}>
              Your Notes
            </div>
            {editing ? (
              <textarea
                className="mc-dialog-input"
                value={userNote}
                onChange={(e) => setUserNote(e.target.value)}
                placeholder="Add your notes..."
                data-testid="task-detail-note-input"
                rows={2}
                style={{ resize: "vertical", minHeight: "48px", lineHeight: 1.5 }}
              />
            ) : (
              <div
                style={{
                  fontSize: "12.5px",
                  lineHeight: 1.5,
                  color: task.user_note ? "var(--mc-ink-2)" : "var(--mc-ink-4)",
                  fontStyle: task.user_note ? "normal" : "italic",
                  padding: "8px 12px",
                  background: "var(--mc-white)",
                  border: "1px solid var(--mc-rule)",
                  borderRadius: "var(--mc-radius)",
                  maxHeight: "200px",
                  overflowY: "auto",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  overflowWrap: "anywhere",
                }}
                data-testid="task-detail-user-note"
              >
                {task.user_note || "No notes yet"}
              </div>
            )}
          </div>

          {/* Status quick actions */}
          <div>
            <div style={{ fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--mc-ink-4)", marginBottom: "8px" }}>
              <ArrowRight size={10} style={{ display: "inline", marginRight: "4px", verticalAlign: "-1px" }} />
              Move To
            </div>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
              {Object.entries(STATUS_CONFIG)
                .filter(([key]) => key !== task.status)
                .map(([key, cfg]) => (
                  <button
                    key={key}
                    className="mc-btn mc-btn-outline mc-btn-sm"
                    onClick={() => handleStatusChange(key)}
                    data-testid={`task-detail-move-${key}`}
                    style={{ gap: "4px", color: cfg.color, borderColor: `${cfg.color}60` }}
                  >
                    {cfg.label}
                  </button>
                ))}
            </div>
          </div>
        </div>

        <DialogFooter style={{ justifyContent: "space-between" }}>
          <div>
            {confirmTrash ? (
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ fontSize: "11.5px", color: "var(--mc-red, #c0392b)", fontWeight: 500 }}>
                  Delete permanently?
                </span>
                <button
                  className="mc-btn mc-btn-sm"
                  onClick={handleTrash}
                  disabled={deleting}
                  data-testid="task-detail-confirm-trash-btn"
                  style={{
                    background: "var(--mc-red, #c0392b)",
                    color: "#fff",
                    border: "none",
                    gap: "4px",
                    fontSize: "11px",
                  }}
                >
                  <Trash2 size={11} />
                  {deleting ? "Deleting..." : "Yes, delete"}
                </button>
                <button
                  className="mc-btn mc-btn-outline mc-btn-sm"
                  onClick={() => setConfirmTrash(false)}
                  data-testid="task-detail-cancel-trash-btn"
                  style={{ fontSize: "11px" }}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                className="mc-btn mc-btn-outline mc-btn-sm"
                onClick={() => setConfirmTrash(true)}
                data-testid="task-detail-trash-btn"
                style={{ gap: "4px", color: "var(--mc-ink-4)", borderColor: "var(--mc-rule)" }}
              >
                <Trash2 size={11} />
                Trash
              </button>
            )}
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            {editing ? (
              <>
                <button
                  className="mc-btn mc-btn-outline"
                  onClick={() => setEditing(false)}
                  data-testid="task-detail-cancel-edit"
                >
                  Cancel
                </button>
                <button
                  className="mc-btn mc-btn-approve"
                  onClick={handleSave}
                  disabled={saving || !title.trim()}
                  data-testid="task-detail-save-btn"
                  style={{ gap: "4px" }}
                >
                  <Check size={12} />
                  {saving ? "Saving..." : "Save Changes"}
                </button>
              </>
            ) : (
              <>
                <button
                  className="mc-btn mc-btn-outline"
                  onClick={() => onOpenChange(false)}
                  data-testid="task-detail-close-btn"
                >
                  Close
                </button>
                <button
                  className="mc-btn mc-btn-accent"
                  onClick={() => setEditing(true)}
                  data-testid="task-detail-edit-btn"
                  style={{ gap: "4px" }}
                >
                  <Pencil size={12} />
                  Edit
                </button>
              </>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
