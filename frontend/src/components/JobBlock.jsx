import React from "react";

const STATUS_CONFIG = {
  success: { bgColor: "#d4edda", borderColor: "#28a745", textColor: "#155724", className: "status-success", label: "Success" },
  failed:  { bgColor: "#f8d7da", borderColor: "#dc3545", textColor: "#721c24", className: "status-failed",  label: "Failed"  },
  running: { bgColor: "#fff3cd", borderColor: "#ffc107", textColor: "#856404", className: "status-running", label: "Running" },
  scheduled: { bgColor: "#e2e3e5", borderColor: "#6c757d", textColor: "#383d41", className: "status-scheduled", label: "Scheduled" },
};

function formatDurationShort(ms) {
  if (!ms) return "";
  if (ms >= 60000) return `${Math.round(ms / 60000)}m`;
  if (ms >= 1000) return `${Math.round(ms / 1000)}s`;
  return `${ms}ms`;
}

export default function JobBlock({ job, onClick }) {
  const config = STATUS_CONFIG[job.status] || STATUS_CONFIG.scheduled;
  const duration = formatDurationShort(job.duration);

  return (
    <div
      className={`job-block ${config.className}`}
      onClick={onClick}
      title={[job.jobName, config.label, duration].filter(Boolean).join("\n")}
      data-testid={`job-block-${job.jobId}`}
      style={{
        backgroundColor: config.bgColor,
        borderColor: config.borderColor,
        color: config.textColor
      }}
    >
      <div className="job-name">{job.jobName}</div>
      {duration && <div className="job-duration">{duration}</div>}
    </div>
  );
}
