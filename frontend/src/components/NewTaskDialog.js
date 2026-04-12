import { useState, useEffect } from "react";
import { createTask, fetchUsers } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

export default function NewTaskDialog({ open, onOpenChange, brands, defaultBrand, onCreated }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [brand, setBrand] = useState(defaultBrand || "");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState("normal");
  const [assignee, setAssignee] = useState("");
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  const filteredBrands = brands.filter(b => b.slug !== "all");

  useEffect(() => {
    if (open) fetchUsers().then(setUsers).catch(console.error);
  }, [open]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !brand) return;
    setLoading(true);
    try {
      const dueDateISO = dueDate ? new Date(dueDate).toISOString() : "";
      await createTask({
        title: title.trim(),
        brand,
        description: description.trim(),
        due_date: dueDateISO,
        priority,
        assignee,
      });
      setTitle("");
      setDescription("");
      setBrand(defaultBrand || "");
      setDueDate("");
      setPriority("normal");
      setAssignee("");
      if (onCreated) onCreated();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]" style={{ fontFamily: "'Libre Franklin', sans-serif" }}>
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500 }}>
            New Task
          </DialogTitle>
          <DialogDescription style={{ fontSize: "12px", color: "var(--mc-ink-3)" }}>
            Create a task for yourself or your team.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} data-testid="new-task-form">
          <div style={{ display: "flex", flexDirection: "column", gap: "14px", padding: "8px 0" }}>
            <div>
              <label className="mc-dialog-label">Task Title</label>
              <input
                className="mc-dialog-input"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="What needs to be done?"
                data-testid="new-task-title-input"
                autoFocus
              />
            </div>
            <div>
              <label className="mc-dialog-label">Description (optional)</label>
              <textarea
                className="mc-dialog-input"
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Add details about this task..."
                data-testid="new-task-description-input"
                rows={3}
                style={{ resize: "vertical", minHeight: "60px", lineHeight: 1.5 }}
              />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label className="mc-dialog-label">Brand</label>
                <select
                  className="mc-dialog-input"
                  value={brand}
                  onChange={e => setBrand(e.target.value)}
                  data-testid="new-task-brand-select"
                >
                  <option value="">Select brand...</option>
                  {filteredBrands.map(b => (
                    <option key={b.slug} value={b.slug}>{b.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mc-dialog-label">Assign To</label>
                <select
                  className="mc-dialog-input"
                  value={assignee}
                  onChange={e => setAssignee(e.target.value)}
                  data-testid="new-task-assignee-select"
                >
                  <option value="">Unassigned</option>
                  {users.map(u => (
                    <option key={u.id} value={u.name}>{u.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label className="mc-dialog-label">Priority</label>
                <select
                  className="mc-dialog-input"
                  value={priority}
                  onChange={e => setPriority(e.target.value)}
                  data-testid="new-task-priority-select"
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <div>
                <label className="mc-dialog-label">Due Date (optional)</label>
                <input
                  type="date"
                  className="mc-dialog-input"
                  value={dueDate}
                  onChange={e => setDueDate(e.target.value)}
                  data-testid="new-task-due-date"
                />
              </div>
            </div>
          </div>
          <DialogFooter style={{ marginTop: "12px" }}>
            <button
              type="button"
              className="mc-btn mc-btn-outline"
              onClick={() => onOpenChange(false)}
              data-testid="new-task-cancel-btn"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="mc-btn mc-btn-approve"
              disabled={loading || !title.trim() || !brand}
              data-testid="new-task-submit-btn"
            >
              {loading ? "Creating..." : "Create Task"}
            </button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
