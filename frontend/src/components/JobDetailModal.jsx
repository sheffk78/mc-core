import React from "react";
import { X, RotateCcw, Copy, Clock, CheckCircle2, XCircle, Loader } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { runScheduleNow } from "@/lib/api";
import { describeCron } from "@/utils/cronParser";

function formatDateTime(isoStr) {
  if (!isoStr) return "—";
  try {
    return new Date(isoStr).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return isoStr;
  }
}

function formatDuration(ms) {
  if (!ms && ms !== 0) return "—";
  if (ms >= 60000) {
    const m = Math.floor(ms / 60000);
    const s = Math.round((ms % 60000) / 1000);
    return s > 0 ? `${m}m ${s}s` : `${m}m`;
  }
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
}

const STATUS_ICONS = {
  success:   <CheckCircle2 size={16} style={{ color: "#059669" }} />,
  failed:    <XCircle      size={16} style={{ color: "#dc2626" }} />,
  running:   <Loader       size={16} style={{ color: "#d97706" }} />,
  scheduled: <Clock        size={16} style={{ color: "#6b7280" }} />,
};

export default function JobDetailModal({ job, onClose, onRetry }) {
  if (!job) return null;

  const statusIcon = STATUS_ICONS[job.status] || STATUS_ICONS.scheduled;

  const handleRetry = async () => {
    try {
      await runScheduleNow(job.jobId);
      if (onRetry) onRetry();
      onClose();
    } catch (e) {
      console.error("Failed to trigger job:", e);
    }
  };

  const handleCopyOutput = () => {
    if (job.output) {
      navigator.clipboard.writeText(job.output).catch(console.error);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent
        className="sm:max-w-[520px]"
        style={{ fontFamily: "'Libre Franklin', sans-serif" }}
      >
        <DialogHeader>
          <DialogTitle
            style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: "18px",
              fontWeight: 500,
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            {statusIcon}
            {job.jobName}
          </DialogTitle>
        </DialogHeader>

        {job.description && (
          <p style={{ fontSize: "12px", color: "var(--mc-ink-3)", margin: "0 0 12px" }}>
            {job.description}
          </p>
        )}

        {/* Info grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "10px",
            padding: "12px",
            background: "var(--mc-off-white)",
            borderRadius: "var(--mc-radius)",
            border: "1px solid var(--mc-rule)",
            marginBottom: "12px",
          }}
        >
          {[
            { label: "Scheduled", value: formatDateTime(job.scheduledTime) },
            { label: "Last Run",  value: formatDateTime(job.lastRun) },
            { label: "Status",    value: job.status
                ? job.status.charAt(0).toUpperCase() + job.status.slice(1)
                : "—" },
            { label: "Duration",  value: formatDuration(job.duration) },
          ].map(({ label, value }) => (
            <div key={label}>
              <div
                style={{
                  fontSize: "10px",
                  fontWeight: 600,
                  color: "var(--mc-ink-4)",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  marginBottom: "2px",
                }}
              >
                {label}
              </div>
              <div style={{ fontSize: "12px", color: "var(--mc-ink-2)" }}>{value}</div>
            </div>
          ))}
        </div>

        {/* Cron description */}
        {job.cron && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "7px 10px",
              background: "var(--mc-off-white)",
              border: "1px solid var(--mc-rule)",
              borderRadius: "var(--mc-radius)",
              fontSize: "11.5px",
              color: "var(--mc-ink-2)",
              marginBottom: "12px",
            }}
          >
            <Clock size={11} />
            {describeCron(job.cron)}
            <span
              style={{
                color: "var(--mc-ink-4)",
                fontFamily: "monospace",
                fontSize: "10px",
                marginLeft: "4px",
              }}
            >
              ({job.cron})
            </span>
          </div>
        )}

        {/* Output */}
        {job.output && (
          <div style={{ marginBottom: "12px" }}>
            <div
              style={{
                fontSize: "10px",
                fontWeight: 600,
                color: "var(--mc-ink-4)",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: "6px",
              }}
            >
              Output
            </div>
            <pre
              style={{
                fontSize: "11px",
                background: "#1a1a1a",
                color: "#e0e0e0",
                padding: "12px",
                borderRadius: "4px",
                overflow: "auto",
                maxHeight: "160px",
                fontFamily: "monospace",
                margin: 0,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {job.output}
            </pre>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
          <button
            className="mc-btn mc-btn-outline mc-btn-sm"
            onClick={handleRetry}
            style={{ gap: "4px" }}
          >
            <RotateCcw size={11} />
            Run Now
          </button>
          {job.output && (
            <button
              className="mc-btn mc-btn-outline mc-btn-sm"
              onClick={handleCopyOutput}
              style={{ gap: "4px" }}
            >
              <Copy size={11} />
              Copy Output
            </button>
          )}
          <button
            className="mc-btn mc-btn-outline mc-btn-sm"
            onClick={onClose}
            style={{ gap: "4px" }}
          >
            <X size={11} />
            Close
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
