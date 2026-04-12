import { useState, useEffect } from "react";
import { fetchCalendarEvents, getCalendarConnectionStatus, fetchMorningBrief } from "@/lib/api";
import { marked } from "marked";
import DOMPurify from "dompurify";
import StatsRow from "@/components/StatsRow";
import TasksList from "@/components/TasksList";
import InboxesList from "@/components/InboxesList";
import ActivityFeed from "@/components/ActivityFeed";
import { CalendarDays } from "lucide-react";

function CalendarMini({ onNavigate }) {
  const [events, setEvents] = useState([]);
  const [hasConnection, setHasConnection] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchCalendarEvents(7, 0), getCalendarConnectionStatus()])
      .then(([evData, status]) => {
        setEvents((evData.events || []).slice(0, 5));
        setHasConnection(status.connected);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="mc-empty">Loading...</div>;

  if (!hasConnection) {
    return (
      <div style={{ padding: "24px 20px", textAlign: "center" }}>
        <CalendarDays size={22} style={{ color: "var(--mc-ink-4)", marginBottom: "8px" }} />
        <div style={{ fontSize: "12px", color: "var(--mc-ink-3)", fontWeight: 300, marginBottom: "12px", lineHeight: 1.5 }}>
          Connect Google Calendar to see upcoming events here.
        </div>
        <button
          className="mc-btn mc-btn-accent mc-btn-sm"
          onClick={() => onNavigate("calendar")}
          data-testid="calendar-connect-btn"
        >
          <CalendarDays size={11} /> Connect Calendar
        </button>
      </div>
    );
  }

  if (events.length === 0) {
    return <div className="mc-empty">No upcoming events this week</div>;
  }

  const today = new Date();
  return (
    <div data-testid="calendar-mini">
      {events.map((ev, i) => {
        const d = new Date(ev.start);
        const isToday = d.toDateString() === today.toDateString();
        const timeStr = ev.all_day
          ? "All day"
          : d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true, timeZone: "America/Denver" });
        const dayLabel = isToday
          ? "Today"
          : d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", timeZone: "America/Denver" });

        return (
          <div
            key={ev.id + i}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              padding: "8px 20px",
              borderBottom: i < events.length - 1 ? "1px solid var(--mc-rule)" : "none",
            }}
          >
            <div style={{
              width: "3px",
              borderRadius: "2px",
              background: ev.color || ev.feed_color || "var(--mc-accent)",
              alignSelf: "stretch",
              flexShrink: 0,
            }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: "12px",
                fontWeight: 500,
                color: "var(--mc-ink)",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                marginBottom: "1px",
              }}>
                {ev.title}
              </div>
              <div style={{ fontSize: "10.5px", color: "var(--mc-ink-3)" }}>
                {dayLabel} · {timeStr}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function renderBriefMd(text) {
  try {
    return DOMPurify.sanitize(marked.parse(text, { breaks: true, gfm: true }));
  } catch {
    return text;
  }
}

function formatBriefDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const diff = Math.floor((now - d) / 86400000);
  const timeStr = d.toLocaleTimeString("en-US", {
    hour: "numeric", minute: "2-digit", hour12: true, timeZone: "America/Denver",
  });
  const dateStr = d.toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric", timeZone: "America/Denver",
  });
  if (diff === 0) return `Today at ${timeStr}`;
  if (diff === 1) return `Yesterday at ${timeStr}`;
  return `${dateStr} at ${timeStr}`;
}

function MorningBrief({ brand }) {
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!brand) return;
    setLoading(true);
    fetchMorningBrief(brand)
      .then(setBrief)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [brand]);

  if (loading) return <div className="mc-empty">Loading brief...</div>;

  if (!brief?.content) {
    return (
      <div style={{ padding: "24px 20px", textAlign: "center" }}>
        <div style={{ fontSize: "12px", color: "var(--mc-ink-4)", fontStyle: "italic", lineHeight: 1.6 }}>
          No morning brief yet for this brand.
        </div>
      </div>
    );
  }

  return (
    <div data-testid="morning-brief-content">
      {brief.updated_at && (
        <div style={{
          fontSize: "10px",
          fontWeight: 500,
          color: "var(--mc-ink-4)",
          textTransform: "uppercase",
          letterSpacing: "0.04em",
          padding: "0 20px 8px",
          borderBottom: "1px solid var(--mc-rule)",
          marginBottom: "4px",
        }}
        data-testid="morning-brief-date"
        >
          Updated {formatBriefDate(brief.updated_at)}
        </div>
      )}
      <div
        className="mc-brief-body"
        dangerouslySetInnerHTML={{ __html: renderBriefMd(brief.content) }}
        data-testid="morning-brief-text"
      />
    </div>
  );
}

export default function Overview({ brand, brands, stats, onAction, onNavigate, refreshKey }) {
  const showBrief = brand && brand !== "all";

  return (
    <div data-testid="overview-page">
      <StatsRow stats={stats} />

      <div className="mc-grid-3-1">
        <div>
          {showBrief ? (
            <div className="mc-card" data-testid="morning-brief-card">
              <div className="mc-card-header">
                <span className="mc-card-title">Morning Brief</span>
              </div>
              <div className="mc-card-body">
                <MorningBrief brand={brand} />
              </div>
            </div>
          ) : (
            <div className="mc-card" data-testid="tasks-overview-card">
              <div className="mc-card-header">
                <span className="mc-card-title">Open Tasks</span>
                <span className="mc-card-action" onClick={() => onNavigate("tasks")} data-testid="view-all-tasks-top">
                  View all
                </span>
              </div>
              <div className="mc-card-body">
                <TasksList brand={brand} brands={brands} onAction={onAction} limit={5} embedded refreshKey={refreshKey} />
              </div>
            </div>
          )}
        </div>
        <div>
          <div className="mc-card" data-testid="calendar-overview-card">
            <div className="mc-card-header">
              <span className="mc-card-title">Upcoming</span>
              <span className="mc-card-action" onClick={() => onNavigate("calendar")} data-testid="view-calendar">
                Calendar
              </span>
            </div>
            <div className="mc-card-body">
              <CalendarMini onNavigate={onNavigate} />
            </div>
          </div>
        </div>
      </div>

      <div className="mc-grid-2">
        <div>
          <div className="mc-card" data-testid="tasks-card">
            <div className="mc-card-header">
              <span className="mc-card-title">Open Tasks</span>
              <span className="mc-card-action" onClick={() => onNavigate("tasks")} data-testid="view-all-tasks">
                View all
              </span>
            </div>
            <div className="mc-card-body">
              <TasksList brand={brand} brands={brands} onAction={onAction} limit={5} embedded />
            </div>
          </div>
        </div>
        <div className="mc-stack">
          <div className="mc-card" data-testid="inboxes-card">
            <div className="mc-card-header">
              <span className="mc-card-title">Agent Inboxes</span>
              <span className="mc-card-action" onClick={() => onNavigate("inboxes")} data-testid="view-all-inboxes">
                View all
              </span>
            </div>
            <div className="mc-card-body">
              <InboxesList brand={brand} brands={brands} limit={4} embedded />
            </div>
          </div>
          <div className="mc-card" data-testid="activity-card">
            <div className="mc-card-header">
              <span className="mc-card-title">Recent Activity</span>
              <span className="mc-card-action" onClick={() => onNavigate("activity")} data-testid="view-all-activity">
                View all
              </span>
            </div>
            <div className="mc-card-body">
              <ActivityFeed brand={brand} brands={brands} limit={5} embedded refreshKey={refreshKey} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
