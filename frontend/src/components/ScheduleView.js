import { useState, useEffect, useCallback } from "react";
import {
  fetchSchedule,
  createScheduleItem,
  pauseSchedule,
  resumeSchedule,
  runScheduleNow,
  editSchedule,
  deleteScheduleItem,
} from "@/lib/api";
import { getBrandColor, getBrandName, timeAgo } from "@/lib/brands";
import {
  Play,
  Pause,
  Zap,
  Pencil,
  Trash2,
  Plus,
  Clock,
  CheckCircle2,
  X,
  CalendarDays,
  List,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import WeeklyCalendar from "./WeeklyCalendar";

// Human-readable cron descriptions
function describeCron(cron) {
  if (!cron) return "No schedule set";
  const parts = cron.split(" ");
  if (parts.length !== 5) return cron;
  const [min, hour, dom, , dow] = parts;

  const dowNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const formatTime = (h, m) => {
    const hh = parseInt(h, 10);
    const mm = m === "0" ? "00" : m;
    if (hh === 0) return `12:${mm} AM`;
    if (hh < 12) return `${hh}:${mm} AM`;
    if (hh === 12) return `12:${mm} PM`;
    return `${hh - 12}:${mm} PM`;
  };

  // Monthly pattern: 0 9 1 * *
  if (dom !== "*" && dow === "*" && hour !== "*" && min !== "*") {
    const suffix = dom === "1" ? "st" : dom === "2" ? "nd" : dom === "3" ? "rd" : "th";
    return `Monthly on ${dom}${suffix} at ${formatTime(hour, min)}`;
  }

  // Daily pattern: 0 9 * * *
  if (dom === "*" && dow === "*" && hour !== "*" && min !== "*") {
    return `Daily at ${formatTime(hour, min)}`;
  }

  // Day-of-week patterns: ranges (1-5) or lists (1,3,5)
  if (dow !== "*" && hour !== "*" && min !== "*") {
    let dayLabel;
    if (dow.includes("-")) {
      const [start, end] = dow.split("-").map((d) => parseInt(d, 10));
      if (start === 1 && end === 5) {
        dayLabel = "Mon\u2013Fri";
      } else {
        dayLabel = `${dowNames[start]}\u2013${dowNames[end]}`;
      }
    } else {
      const days = dow.split(",").map((d) => dowNames[parseInt(d, 10)] || d);
      dayLabel = days.join(", ");
    }
    return `${dayLabel} at ${formatTime(hour, min)}`;
  }

  if (hour === "*" && min !== "*") {
    return `Every hour at :${min.padStart(2, "0")}`;
  }
  if (min === "*/5" || min === "*/10" || min === "*/15" || min === "*/30") {
    const interval = min.split("/")[1];
    return `Every ${interval} minutes`;
  }
  return cron;
}

// Preset cron options for the dialog
const CRON_PRESETS = [
  { label: "Every 15 minutes", value: "*/15 * * * *" },
  { label: "Every hour", value: "0 * * * *" },
  { label: "Daily at 9:00 AM", value: "0 9 * * *" },
  { label: "Daily at 6:00 PM", value: "0 18 * * *" },
  { label: "Mon–Fri at 9:00 AM", value: "0 9 * * 1-5" },
  { label: "Weekly (Mon 9 AM)", value: "0 9 * * 1" },
  { label: "Monthly (1st, 9 AM)", value: "0 9 1 * *" },
  { label: "Custom", value: "" },
];

function CreateScheduleDialog({ open, onOpenChange, brands, onCreated }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [brand, setBrand] = useState("agentic-trust");
  const [cronPreset, setCronPreset] = useState("0 9 * * *");
  const [customCron, setCustomCron] = useState("");
  const [saving, setSaving] = useState(false);

  const cron = cronPreset === "" ? customCron : cronPreset;

  const handleSave = async () => {
    if (!name.trim() || !cron.trim()) return;
    setSaving(true);
    try {
      await createScheduleItem({
        name: name.trim(),
        description: description.trim(),
        brand,
        cron,
      });
      setName("");
      setDescription("");
      setCronPreset("0 9 * * *");
      setCustomCron("");
      onOpenChange(false);
      if (onCreated) onCreated();
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-[480px]"
        style={{ fontFamily: "'Libre Franklin', sans-serif" }}
      >
        <DialogHeader>
          <DialogTitle
            style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: "18px",
              fontWeight: 500,
            }}
          >
            New Scheduled Job
          </DialogTitle>
          <DialogDescription style={{ fontSize: "12px", color: "var(--mc-ink-3)" }}>
            Create an automated task that Kit will execute on a recurring schedule.
          </DialogDescription>
        </DialogHeader>

        <div style={{ display: "flex", flexDirection: "column", gap: "14px", padding: "8px 0" }}>
          <div>
            <label className="mc-dialog-label">Job Name</label>
            <input
              className="mc-dialog-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Weekly Newsletter Digest"
              data-testid="schedule-name-input"
            />
          </div>

          <div>
            <label className="mc-dialog-label">Description</label>
            <textarea
              className="mc-dialog-input"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What does this job do?"
              rows={2}
              data-testid="schedule-description-input"
              style={{ resize: "vertical", minHeight: "48px" }}
            />
          </div>

          <div>
            <label className="mc-dialog-label">Brand</label>
            <select
              className="mc-dialog-input"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              data-testid="schedule-brand-select"
            >
              {brands.filter((b) => b.slug !== "all").map((b) => (
                <option key={b.slug} value={b.slug}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mc-dialog-label">Schedule</label>
            <select
              className="mc-dialog-input"
              value={cronPreset}
              onChange={(e) => setCronPreset(e.target.value)}
              data-testid="schedule-preset-select"
            >
              {CRON_PRESETS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          {cronPreset === "" && (
            <div>
              <label className="mc-dialog-label">Cron Expression</label>
              <input
                className="mc-dialog-input"
                value={customCron}
                onChange={(e) => setCustomCron(e.target.value)}
                placeholder="* * * * * (min hour dom mon dow)"
                data-testid="schedule-cron-input"
                style={{ fontFamily: "monospace", fontSize: "12px" }}
              />
              <div style={{ fontSize: "10px", color: "var(--mc-ink-4)", marginTop: "4px" }}>
                Format: minute hour day-of-month month day-of-week
              </div>
            </div>
          )}

          {cron && (
            <div
              style={{
                padding: "8px 12px",
                background: "var(--mc-off-white)",
                border: "1px solid var(--mc-rule)",
                borderRadius: "var(--mc-radius)",
                fontSize: "11.5px",
                color: "var(--mc-ink-2)",
              }}
              data-testid="schedule-preview"
            >
              <Clock size={11} style={{ display: "inline", marginRight: "6px", verticalAlign: "-1px" }} />
              {describeCron(cron)}
              <span style={{ color: "var(--mc-ink-4)", marginLeft: "8px", fontFamily: "monospace", fontSize: "10px" }}>
                ({cron})
              </span>
            </div>
          )}
        </div>

        <DialogFooter style={{ marginTop: "8px" }}>
          <button className="mc-btn mc-btn-outline" onClick={() => onOpenChange(false)} data-testid="schedule-cancel-btn">
            Cancel
          </button>
          <button
            className="mc-btn mc-btn-approve"
            onClick={handleSave}
            disabled={saving || !name.trim() || !cron.trim()}
            data-testid="schedule-create-btn"
            style={{ gap: "6px" }}
          >
            <Plus size={12} />
            {saving ? "Creating..." : "Create Job"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function EditScheduleDialog({ open, onOpenChange, job, onUpdated }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [cron, setCron] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (job && open) {
      setName(job.name || "");
      setDescription(job.description || "");
      setCron(job.cron || "");
    }
  }, [job, open]);

  const handleSave = async () => {
    if (!job) return;
    setSaving(true);
    try {
      const updates = {};
      if (name !== job.name) updates.name = name;
      if (description !== job.description) updates.description = description;
      if (cron !== job.cron) updates.cron = cron;
      if (Object.keys(updates).length > 0) {
        await editSchedule(job.id, updates);
      }
      onOpenChange(false);
      if (onUpdated) onUpdated();
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[440px]" style={{ fontFamily: "'Libre Franklin', sans-serif" }}>
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500 }}>
            Edit Schedule
          </DialogTitle>
        </DialogHeader>
        <div style={{ display: "flex", flexDirection: "column", gap: "14px", padding: "8px 0" }}>
          <div>
            <label className="mc-dialog-label">Job Name</label>
            <input className="mc-dialog-input" value={name} onChange={(e) => setName(e.target.value)} data-testid="edit-schedule-name" />
          </div>
          <div>
            <label className="mc-dialog-label">Description</label>
            <textarea className="mc-dialog-input" value={description} onChange={(e) => setDescription(e.target.value)} rows={2} data-testid="edit-schedule-desc" style={{ resize: "vertical" }} />
          </div>
          <div>
            <label className="mc-dialog-label">Cron Expression</label>
            <input className="mc-dialog-input" value={cron} onChange={(e) => setCron(e.target.value)} data-testid="edit-schedule-cron" style={{ fontFamily: "monospace", fontSize: "12px" }} />
            {cron && (
              <div style={{ fontSize: "10.5px", color: "var(--mc-ink-3)", marginTop: "4px" }}>
                <Clock size={10} style={{ display: "inline", marginRight: "4px", verticalAlign: "-1px" }} />
                {describeCron(cron)}
              </div>
            )}
          </div>
        </div>
        <DialogFooter>
          <button className="mc-btn mc-btn-outline" onClick={() => onOpenChange(false)}>Cancel</button>
          <button className="mc-btn mc-btn-approve" onClick={handleSave} disabled={saving} data-testid="edit-schedule-save-btn">
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function ScheduleView({ brand, brands, onAction, refreshKey }) {
  const [viewMode, setViewMode] = useState("calendar"); // "calendar" | "list"
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    fetchSchedule(brand)
      .then(setJobs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [brand]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const handleAction = async (jobId, action) => {
    setActionInProgress(jobId);
    try {
      if (action === "pause") await pauseSchedule(jobId);
      else if (action === "resume") await resumeSchedule(jobId);
      else if (action === "run-now") await runScheduleNow(jobId);
      load();
      if (onAction) onAction();
    } catch (e) {
      console.error(e);
    } finally {
      setActionInProgress(null);
    }
  };

  const handleDelete = async (jobId) => {
    try {
      await deleteScheduleItem(jobId);
      setConfirmDelete(null);
      load();
      if (onAction) onAction();
    } catch (e) {
      console.error(e);
    }
  };

  const activeJobs = jobs.filter((j) => j.status === "active");
  const pausedJobs = jobs.filter((j) => j.status === "paused");

  return (
    <div data-testid="schedule-view">
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <h2
            style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: "22px",
              fontWeight: 500,
              color: "var(--mc-ink)",
              margin: 0,
            }}
            data-testid="schedule-heading"
          >
            Scheduled Jobs
          </h2>
          <p style={{ fontSize: "12px", color: "var(--mc-ink-3)", marginTop: "4px" }}>
            Automated tasks Kit executes on a recurring basis
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          {/* View toggle */}
          <div
            style={{
              display: "flex",
              border: "1px solid var(--mc-rule)",
              borderRadius: "var(--mc-radius)",
              overflow: "hidden",
            }}
          >
            <button
              className="mc-btn mc-btn-sm"
              onClick={() => setViewMode("calendar")}
              data-testid="view-toggle-calendar"
              style={{
                gap: "4px",
                borderRadius: 0,
                background: viewMode === "calendar" ? "var(--mc-ink)" : "var(--mc-white)",
                color:      viewMode === "calendar" ? "#fff" : "var(--mc-ink-3)",
                border: "none",
                borderRight: "1px solid var(--mc-rule)",
              }}
            >
              <CalendarDays size={12} />
              Calendar
            </button>
            <button
              className="mc-btn mc-btn-sm"
              onClick={() => setViewMode("list")}
              data-testid="view-toggle-list"
              style={{
                gap: "4px",
                borderRadius: 0,
                background: viewMode === "list" ? "var(--mc-ink)" : "var(--mc-white)",
                color:      viewMode === "list" ? "#fff" : "var(--mc-ink-3)",
                border: "none",
              }}
            >
              <List size={12} />
              List
            </button>
          </div>

          <button
            className="mc-btn mc-btn-approve"
            onClick={() => setShowCreate(true)}
            data-testid="create-schedule-btn"
            style={{ gap: "6px" }}
          >
            <Plus size={12} />
            New Job
          </button>
        </div>
      </div>

      {/* Calendar view */}
      {viewMode === "calendar" && (
        <WeeklyCalendar brand={brand} refreshKey={refreshKey} />
      )}

      {/* List view */}
      {viewMode === "list" && (loading ? (
        <div className="mc-empty">Loading schedule...</div>
      ) : jobs.length === 0 ? (
        <div
          style={{
            padding: "60px 40px",
            textAlign: "center",
            border: "1px dashed var(--mc-rule)",
            borderRadius: "var(--mc-radius)",
            background: "var(--mc-white)",
          }}
          data-testid="schedule-empty"
        >
          <Clock
            size={28}
            style={{ color: "var(--mc-ink-4)", margin: "0 auto 12px" }}
          />
          <div
            style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: "16px",
              fontWeight: 500,
              color: "var(--mc-ink-2)",
              marginBottom: "6px",
            }}
          >
            No scheduled jobs yet
          </div>
          <div style={{ fontSize: "12px", color: "var(--mc-ink-3)", maxWidth: "320px", margin: "0 auto" }}>
            Create automated tasks that Kit will execute on a recurring schedule — newsletters, reports, syncs, and more.
          </div>
          <button
            className="mc-btn mc-btn-outline"
            onClick={() => setShowCreate(true)}
            style={{ marginTop: "16px", gap: "6px" }}
            data-testid="schedule-empty-create-btn"
          >
            <Plus size={12} />
            Create your first job
          </button>
        </div>
      ) : (
        <>
          {/* Active Jobs */}
          {activeJobs.length > 0 && (
            <div style={{ marginBottom: "28px" }}>
              <div className="mc-section-header" data-testid="active-jobs-header">
                <span
                  style={{
                    fontSize: "9.5px",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.12em",
                    color: "var(--mc-green)",
                  }}
                >
                  Active ({activeJobs.length})
                </span>
              </div>
              {activeJobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  actionInProgress={actionInProgress}
                  onAction={handleAction}
                  onEdit={() => setEditingJob(job)}
                  onDelete={() => setConfirmDelete(job)}
                />
              ))}
            </div>
          )}

          {/* Paused Jobs */}
          {pausedJobs.length > 0 && (
            <div>
              <div className="mc-section-header" data-testid="paused-jobs-header">
                <span
                  style={{
                    fontSize: "9.5px",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.12em",
                    color: "var(--mc-ink-4)",
                  }}
                >
                  Paused ({pausedJobs.length})
                </span>
              </div>
              {pausedJobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  actionInProgress={actionInProgress}
                  onAction={handleAction}
                  onEdit={() => setEditingJob(job)}
                  onDelete={() => setConfirmDelete(job)}
                />
              ))}
            </div>
          )}
        </>
      ))}

      {/* Create Dialog */}
      <CreateScheduleDialog
        open={showCreate}
        onOpenChange={setShowCreate}
        brands={brands}
        onCreated={load}
      />

      {/* Edit Dialog */}
      <EditScheduleDialog
        open={!!editingJob}
        onOpenChange={(v) => !v && setEditingJob(null)}
        job={editingJob}
        onUpdated={load}
      />

      {/* Delete Confirmation */}
      {confirmDelete && (
        <Dialog open onOpenChange={() => setConfirmDelete(null)}>
          <DialogContent className="sm:max-w-[380px]" style={{ fontFamily: "'Libre Franklin', sans-serif" }}>
            <DialogHeader>
              <DialogTitle style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "16px" }}>
                Delete Schedule
              </DialogTitle>
              <DialogDescription style={{ fontSize: "12px" }}>
                Are you sure you want to delete "<strong>{confirmDelete.name}</strong>"? This cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <button className="mc-btn mc-btn-outline" onClick={() => setConfirmDelete(null)} data-testid="delete-schedule-cancel">
                Cancel
              </button>
              <button
                className="mc-btn"
                onClick={() => handleDelete(confirmDelete.id)}
                data-testid="delete-schedule-confirm"
                style={{
                  background: "var(--mc-red-bg)",
                  color: "var(--mc-red)",
                  border: "1px solid currentColor",
                }}
              >
                <Trash2 size={12} style={{ marginRight: "4px" }} />
                Delete
              </button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

function JobCard({ job, actionInProgress, onAction, onEdit, onDelete }) {
  const isActing = actionInProgress === job.id;
  const isActive = job.status === "active";

  return (
    <div
      className="mc-schedule-card"
      data-testid={`schedule-card-${job.id}`}
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "16px",
        padding: "16px 20px",
        background: "var(--mc-white)",
        border: "1px solid var(--mc-rule)",
        borderRadius: "var(--mc-radius)",
        marginBottom: "8px",
        transition: "border-color 150ms",
        opacity: isActive ? 1 : 0.7,
      }}
    >
      {/* Status icon */}
      <div
        style={{
          width: "32px",
          height: "32px",
          borderRadius: "50%",
          background: isActive ? "var(--mc-green-bg)" : "var(--mc-warm-gray)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          marginTop: "2px",
        }}
      >
        {isActive ? (
          <CheckCircle2 size={14} style={{ color: "var(--mc-green)" }} />
        ) : (
          <Pause size={14} style={{ color: "var(--mc-ink-4)" }} />
        )}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
          <span
            className="mc-brand-pill"
            style={{
              background: getBrandColor(job.brand),
              color: "#fff",
              fontSize: "9px",
              padding: "1px 7px",
              borderRadius: "2px",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            {getBrandName(job.brand)}
          </span>
          <span style={{ fontSize: "10px", color: "var(--mc-ink-4)" }}>
            {job.agent_name || "Kit"}
          </span>
        </div>

        <div
          style={{
            fontWeight: 500,
            fontSize: "13.5px",
            color: "var(--mc-ink)",
            marginBottom: "4px",
          }}
        >
          {job.name}
        </div>

        {job.description && (
          <div style={{ fontSize: "11.5px", color: "var(--mc-ink-3)", marginBottom: "6px", lineHeight: 1.4 }}>
            {job.description}
          </div>
        )}

        <div style={{ display: "flex", gap: "16px", alignItems: "center", flexWrap: "wrap" }}>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              fontSize: "11px",
              color: "var(--mc-ink-2)",
              fontFamily: "monospace",
              background: "var(--mc-off-white)",
              padding: "2px 8px",
              borderRadius: "3px",
              border: "1px solid var(--mc-rule)",
            }}
            data-testid={`schedule-cron-${job.id}`}
          >
            <Clock size={10} />
            {describeCron(job.cron)}
          </span>

          {job.last_run && (
            <span style={{ fontSize: "10.5px", color: "var(--mc-ink-4)" }}>
              Last run: {timeAgo(job.last_run)}
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: "4px", flexShrink: 0, alignItems: "center" }}>
        {isActive ? (
          <button
            className="mc-btn mc-btn-outline mc-btn-sm"
            onClick={() => onAction(job.id, "pause")}
            disabled={isActing}
            data-testid={`schedule-pause-${job.id}`}
            title="Pause"
            style={{ gap: "4px" }}
          >
            <Pause size={11} />
            Pause
          </button>
        ) : (
          <button
            className="mc-btn mc-btn-outline mc-btn-sm"
            onClick={() => onAction(job.id, "resume")}
            disabled={isActing}
            data-testid={`schedule-resume-${job.id}`}
            title="Resume"
            style={{ gap: "4px", color: "var(--mc-green)" }}
          >
            <Play size={11} />
            Resume
          </button>
        )}

        <button
          className="mc-btn mc-btn-outline mc-btn-sm"
          onClick={() => onAction(job.id, "run-now")}
          disabled={isActing}
          data-testid={`schedule-run-now-${job.id}`}
          title="Run Now"
          style={{ gap: "4px", color: "var(--mc-accent)" }}
        >
          <Zap size={11} />
          Run
        </button>

        <button
          className="mc-btn mc-btn-outline mc-btn-sm"
          onClick={onEdit}
          data-testid={`schedule-edit-${job.id}`}
          title="Edit"
        >
          <Pencil size={11} />
        </button>

        <button
          className="mc-btn mc-btn-outline mc-btn-sm"
          onClick={onDelete}
          data-testid={`schedule-delete-${job.id}`}
          title="Delete"
          style={{ color: "var(--mc-red, #c0392b)" }}
        >
          <Trash2 size={11} />
        </button>
      </div>
    </div>
  );
}
