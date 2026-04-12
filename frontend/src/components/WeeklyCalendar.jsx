import React, { useState, useEffect, useCallback } from "react";
import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import JobBlock from "./JobBlock";
import JobDetailModal from "./JobDetailModal";
import { fetchWeeklySchedule } from "@/lib/api";
import "@/styles/calendar.css";

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

function formatHour(hour) {
  if (hour === 0)  return "12 AM";
  if (hour < 12)  return `${hour} AM`;
  if (hour === 12) return "12 PM";
  return `${hour - 12} PM`;
}

function formatDateHeader(dateStr, dayName) {
  if (!dateStr) return dayName;
  // Use noon to avoid DST shift issues
  const d = new Date(`${dateStr}T12:00:00`);
  return `${dayName} ${d.getDate()}`;
}

function formatWeekRange(weekStart, weekEnd) {
  if (!weekStart || !weekEnd) return "";
  const start = new Date(`${weekStart}T12:00:00`);
  const end   = new Date(`${weekEnd}T12:00:00`);
  const startStr = start.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  const endStr   = end.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  return `${startStr} – ${endStr}`;
}

export default function WeeklyCalendar({ brand = "all", refreshKey }) {
  const [schedule, setSchedule]     = useState(null);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);
  const [weekOffset, setWeekOffset] = useState(0);
  const [selectedJob, setSelectedJob] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchWeeklySchedule(weekOffset)
      .then(setSchedule)
      .catch((e) => setError(e.message || "Unknown error"))
      .finally(() => setLoading(false));
  }, [weekOffset]);

  useEffect(() => { load(); }, [load, refreshKey]);

  // Filter events by selected brand
  const filteredEvents = brand && brand !== "all" && schedule?.events
    ? schedule.events.filter(e => e.brand === brand)
    : schedule?.events || [];

  if (loading) {
    return <div className="calendar-loading">Loading weekly schedule…</div>;
  }

  if (error) {
    return (
      <div className="calendar-error">
        <p>Failed to load schedule: {error}</p>
        <button className="mc-btn mc-btn-outline mc-btn-sm" onClick={load} style={{ marginTop: "8px", gap: "4px" }}>
          <RefreshCw size={11} /> Retry
        </button>
      </div>
    );
  }

  const events = filteredEvents;

  // Build lookup: "YYYY-MM-DD:HH" → [event, …]
  const eventMap = {};
  for (const ev of events) {
    const key = `${ev.date}:${ev.hour}`;
    if (!eventMap[key]) eventMap[key] = [];
    eventMap[key].push(ev);
  }

  // Derive the 7 ISO date strings for this week (Mon–Sun)
  const weekDates = [];
  if (schedule?.weekStart) {
    const start = new Date(`${schedule.weekStart}T12:00:00`);
    for (let i = 0; i < 7; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      weekDates.push(d.toISOString().split("T")[0]);
    }
  }

  const todayStr    = new Date().toISOString().split("T")[0];
  const currentHour = new Date().getHours();

  return (
    <div className="weekly-calendar" data-testid="weekly-calendar">
      {/* Navigation */}
      <div className="calendar-nav">
        <button
          className="mc-btn mc-btn-outline mc-btn-sm"
          onClick={() => setWeekOffset((w) => w - 1)}
          style={{ gap: "4px" }}
        >
          <ChevronLeft size={14} /> Prev
        </button>

        <span className="calendar-week-label">
          {formatWeekRange(schedule?.weekStart, schedule?.weekEnd)}
        </span>

        <button
          className="mc-btn mc-btn-outline mc-btn-sm"
          onClick={() => setWeekOffset((w) => w + 1)}
          style={{ gap: "4px" }}
        >
          Next <ChevronRight size={14} />
        </button>

        {weekOffset !== 0 && (
          <button
            className="mc-btn mc-btn-outline mc-btn-sm"
            onClick={() => setWeekOffset(0)}
            style={{ marginLeft: "4px" }}
          >
            Today
          </button>
        )}

        <button
          className="mc-btn mc-btn-outline mc-btn-sm"
          onClick={load}
          style={{ marginLeft: "auto", gap: "4px" }}
          title="Refresh"
        >
          <RefreshCw size={11} />
        </button>
      </div>

      {/* Grid */}
      <div className="calendar" data-testid="calendar-grid">
        {/* Header */}
        <div className="calendar-header">
          <div className="time-column-header" />
          {DAY_NAMES.map((day, i) => {
            const dateStr = weekDates[i];
            const isToday = dateStr === todayStr;
            return (
              <div key={day} className={`day-header${isToday ? " today" : ""}`}>
                {formatDateHeader(dateStr, day)}
              </div>
            );
          })}
        </div>

        {/* Hour rows */}
        <div className="calendar-grid">
          {HOURS.map((hour) => (
            <div key={hour} className={`hour-row${hour % 2 === 0 ? " even" : ""}`}>
              <div className="time-label">{formatHour(hour)}</div>

              {DAY_NAMES.map((day, dayIdx) => {
                const dateStr    = weekDates[dayIdx];
                const key        = `${dateStr}:${hour}`;
                const cellEvents = eventMap[key] || [];
                const conflictLevel = Math.min(cellEvents.length, 5);
                const isToday    = dateStr === todayStr;
                const isPast     = isToday && hour < currentHour;

                return (
                  <div
                    key={day}
                    className={[
                      "cell",
                      `conflict-${conflictLevel}`,
                      isToday ? "today-col" : "",
                      isPast  ? "past"      : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    data-testid={`cell-${dateStr}-${hour}`}
                  >
                    {cellEvents.map((ev, idx) => (
                      <JobBlock
                        key={`${ev.jobId}-${idx}`}
                        job={ev}
                        onClick={() => setSelectedJob(ev)}
                      />
                    ))}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="calendar-legend">
        <span className="legend-item"><span className="legend-dot success" />   Success</span>
        <span className="legend-item"><span className="legend-dot failed" />    Failed</span>
        <span className="legend-item"><span className="legend-dot running" />   Running</span>
        <span className="legend-item"><span className="legend-dot scheduled" /> Scheduled</span>
        <span className="legend-item"><span className="legend-dot conflict-2" /> 2 jobs overlap</span>
        <span className="legend-item"><span className="legend-dot conflict-3" /> 3+ jobs overlap</span>
      </div>

      {/* Detail Modal */}
      {selectedJob && (
        <JobDetailModal
          job={selectedJob}
          onClose={() => setSelectedJob(null)}
          onRetry={load}
        />
      )}
    </div>
  );
}
