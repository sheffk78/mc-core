import { useState, useEffect, useCallback } from "react";
import {
  getCalendarOAuthUrl,
  getCalendarConnectionStatus,
  disconnectCalendarAccount,
  fetchCalendarEvents,
  createCalendarEvent,
} from "@/lib/api";
import {
  Plus,
  ChevronLeft,
  ChevronRight,
  CalendarDays,
  ExternalLink,
  Video,
  MapPin,
  Users,
  LogOut,
  X,
  Clock,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

function getWeekDates(baseDate) {
  const d = new Date(baseDate);
  const day = d.getDay();
  const start = new Date(d);
  start.setDate(d.getDate() - day);
  const dates = [];
  for (let i = 0; i < 7; i++) {
    const dd = new Date(start);
    dd.setDate(start.getDate() + i);
    dates.push(dd);
  }
  return dates;
}

function isSameDay(d1, d2) {
  return (
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
  );
}

const TZ = "America/Denver";

function formatTime(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true, timeZone: TZ });
}

function getHourInTZ(isoStr) {
  const d = new Date(isoStr);
  const parts = d.toLocaleTimeString("en-US", { hour: "numeric", hour12: false, timeZone: TZ });
  return parseInt(parts, 10);
}

function formatWeekRange(dates) {
  const start = dates[0];
  const end = dates[6];
  const sameMonth = start.getMonth() === end.getMonth();
  if (sameMonth) {
    return `${start.toLocaleDateString("en-US", { month: "long", timeZone: TZ })} ${start.getDate()} – ${end.getDate()}, ${end.getFullYear()}`;
  }
  return `${start.toLocaleDateString("en-US", { month: "short", timeZone: TZ })} ${start.getDate()} – ${end.toLocaleDateString("en-US", { month: "short", timeZone: TZ })} ${end.getDate()}, ${end.getFullYear()}`;
}

const HOURS = Array.from({ length: 16 }, (_, i) => i + 6); // 6am to 9pm

export default function CalendarView() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [showCreateEvent, setShowCreateEvent] = useState(false);
  const [newEvent, setNewEvent] = useState({ title: "", description: "", location: "", start: "", end: "", all_day: false });
  const [creating, setCreating] = useState(false);

  const checkConnection = useCallback(async () => {
    try {
      const status = await getCalendarConnectionStatus();
      setConnected(status.connected);
      setAccounts(status.accounts || []);
      return status.connected;
    } catch {
      return false;
    }
  }, []);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchCalendarEvents(21, 7);
      setEvents(data.events || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      const isConnected = await checkConnection();
      if (isConnected) {
        await loadEvents();
      } else {
        setLoading(false);
      }
    };
    init();
  }, [checkConnection, loadEvents]);

  // Check for OAuth return
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("connected") === "true") {
      window.history.replaceState({}, "", window.location.pathname);
      checkConnection().then((isConnected) => {
        if (isConnected) loadEvents();
      });
    }
  }, [checkConnection, loadEvents]);

  const handleConnect = async () => {
    try {
      const { authorization_url } = await getCalendarOAuthUrl();
      window.location.href = authorization_url;
    } catch (e) {
      console.error(e);
    }
  };

  const handleDisconnect = async (accountId) => {
    try {
      await disconnectCalendarAccount(accountId);
      setAccounts((prev) => prev.filter((a) => a.id !== accountId));
      setConnected(false);
      setEvents([]);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateEvent = async () => {
    if (!newEvent.title || !newEvent.start || !newEvent.end) return;
    setCreating(true);
    try {
      await createCalendarEvent({
        title: newEvent.title,
        description: newEvent.description,
        location: newEvent.location,
        start: newEvent.all_day ? newEvent.start : new Date(newEvent.start).toISOString(),
        end: newEvent.all_day ? newEvent.end : new Date(newEvent.end).toISOString(),
        all_day: newEvent.all_day,
      });
      setShowCreateEvent(false);
      setNewEvent({ title: "", description: "", location: "", start: "", end: "", all_day: false });
      loadEvents();
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
    }
  };

  const navWeek = (dir) => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() + dir * 7);
    setCurrentDate(d);
  };

  const today = new Date();
  const weekDates = getWeekDates(currentDate);

  // --- Not connected view ---
  if (!loading && !connected) {
    return (
      <div data-testid="calendar-view">
        <div className="mc-card" style={{ maxWidth: "520px" }}>
          <div className="mc-card-header">
            <span className="mc-card-title">Calendar</span>
          </div>
          <div className="mc-card-body" style={{ padding: "48px 32px", textAlign: "center" }}>
            <CalendarDays size={32} style={{ color: "var(--mc-ink-4)", marginBottom: "12px" }} />
            <div style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500, marginBottom: "8px" }}>
              Connect Google Calendar
            </div>
            <div style={{ fontSize: "12.5px", color: "var(--mc-ink-3)", fontWeight: 300, marginBottom: "24px", lineHeight: 1.6, maxWidth: "380px", margin: "0 auto 24px" }}>
              Sign in with your Google account to see your calendar events, meeting details, attendees, and video call links directly inside Mission Control.
            </div>
            <button className="mc-btn mc-btn-accent" onClick={handleConnect} data-testid="connect-google-calendar-btn" style={{ gap: "6px" }}>
              <CalendarDays size={13} />
              Connect Google Calendar
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- Get events for a specific day and hour ---
  const getEventsForHour = (date, hour) => {
    return events.filter((ev) => {
      if (ev.all_day) return false;
      const evDate = new Date(ev.start);
      return isSameDay(evDate, date) && getHourInTZ(ev.start) === hour;
    });
  };

  const getAllDayEvents = (date) => {
    return events.filter((ev) => {
      if (!ev.all_day) return false;
      const evDate = new Date(ev.start);
      return isSameDay(evDate, date);
    });
  };

  const hasAllDayEvents = weekDates.some((d) => getAllDayEvents(d).length > 0);

  return (
    <div data-testid="calendar-view">
      {/* Toolbar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button className="mc-btn mc-btn-outline mc-btn-sm" onClick={() => setCurrentDate(new Date())} data-testid="calendar-today-btn">
            Today
          </button>
          <button className="mc-btn mc-btn-outline mc-btn-sm" onClick={() => navWeek(-1)} data-testid="calendar-prev-btn" style={{ padding: "4px 8px" }}>
            <ChevronLeft size={14} />
          </button>
          <button className="mc-btn mc-btn-outline mc-btn-sm" onClick={() => navWeek(1)} data-testid="calendar-next-btn" style={{ padding: "4px 8px" }}>
            <ChevronRight size={14} />
          </button>
          <span style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "15px", fontWeight: 500, color: "var(--mc-ink)", marginLeft: "8px" }}>
            {formatWeekRange(weekDates)}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {accounts.map((acc) => (
            <div key={acc.id} style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "var(--mc-ink-3)" }}>
              <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#34a853" }} />
              {acc.email}
            </div>
          ))}
          <button className="mc-btn mc-btn-accent mc-btn-sm" onClick={() => setShowCreateEvent(true)} data-testid="create-event-btn" style={{ gap: "4px" }}>
            <Plus size={12} />
            Event
          </button>
        </div>
      </div>

      {loading ? (
        <div className="mc-empty">Loading calendar...</div>
      ) : (
        <div className="mc-card" data-testid="calendar-week-grid" style={{ overflow: "hidden" }}>
          {/* Week header */}
          <div style={{ display: "grid", gridTemplateColumns: "52px repeat(7, 1fr)", borderBottom: "1px solid var(--mc-rule)" }}>
            <div style={{ padding: "8px", borderRight: "1px solid var(--mc-rule)" }} />
            {weekDates.map((d, i) => {
              const isToday_ = isSameDay(d, today);
              return (
                <div key={i} style={{
                  padding: "8px 4px", textAlign: "center",
                  borderRight: i < 6 ? "1px solid var(--mc-rule)" : "none",
                  background: isToday_ ? "var(--mc-accent-bg)" : "transparent",
                }}>
                  <div style={{ fontSize: "9.5px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: isToday_ ? "var(--mc-accent)" : "var(--mc-ink-4)" }}>
                    {d.toLocaleDateString("en-US", { weekday: "short", timeZone: TZ })}
                  </div>
                  <div style={{
                    fontSize: "18px", fontFamily: "'Playfair Display', Georgia, serif", fontWeight: 500,
                    color: isToday_ ? "var(--mc-accent)" : "var(--mc-ink)",
                    ...(isToday_ ? { background: "var(--mc-accent)", color: "#fff", width: "28px", height: "28px", borderRadius: "50%", display: "inline-flex", alignItems: "center", justifyContent: "center" } : {}),
                  }}>
                    {d.getDate()}
                  </div>
                </div>
              );
            })}
          </div>

          {/* All-day events row */}
          {hasAllDayEvents && (
            <div style={{ display: "grid", gridTemplateColumns: "52px repeat(7, 1fr)", borderBottom: "1px solid var(--mc-rule)", minHeight: "28px" }}>
              <div style={{ padding: "4px 4px", fontSize: "9px", color: "var(--mc-ink-4)", textAlign: "right", borderRight: "1px solid var(--mc-rule)" }}>
                all day
              </div>
              {weekDates.map((d, di) => {
                const dayAllDay = getAllDayEvents(d);
                return (
                  <div key={di} style={{ padding: "2px 3px", borderRight: di < 6 ? "1px solid var(--mc-rule)" : "none" }}>
                    {dayAllDay.map((ev) => (
                      <div
                        key={ev.id}
                        onClick={() => setSelectedEvent(ev)}
                        style={{
                          fontSize: "10px", fontWeight: 500, color: "#fff",
                          background: ev.color || "var(--mc-accent)", borderRadius: "3px",
                          padding: "2px 5px", marginBottom: "1px", cursor: "pointer",
                          whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                        }}
                        data-testid={`event-allday-${ev.id}`}
                      >
                        {ev.title}
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          )}

          {/* Time grid */}
          <div style={{ maxHeight: "520px", overflow: "auto" }}>
            {HOURS.map((hour) => (
              <div key={hour} style={{ display: "grid", gridTemplateColumns: "52px repeat(7, 1fr)", minHeight: "48px", borderBottom: "1px solid var(--mc-rule)" }}>
                <div style={{ padding: "2px 6px 0 0", fontSize: "9.5px", color: "var(--mc-ink-4)", textAlign: "right", borderRight: "1px solid var(--mc-rule)" }}>
                  {hour > 12 ? `${hour - 12}pm` : hour === 12 ? "12pm" : `${hour}am`}
                </div>
                {weekDates.map((d, di) => {
                  const dayEvents = getEventsForHour(d, hour);
                  const isToday_ = isSameDay(d, today);
                  return (
                    <div key={di} style={{
                      borderRight: di < 6 ? "1px solid var(--mc-rule)" : "none",
                      padding: "1px 2px",
                      background: isToday_ ? "#fdfcfa" : "transparent",
                    }}>
                      {dayEvents.map((ev) => (
                        <div
                          key={ev.id}
                          onClick={() => setSelectedEvent(ev)}
                          data-testid={`event-${ev.id}`}
                          style={{
                            fontSize: "10px", fontWeight: 500, color: "#fff",
                            background: ev.color || "var(--mc-accent)",
                            borderRadius: "3px", padding: "3px 5px",
                            marginBottom: "1px", cursor: "pointer",
                            lineHeight: 1.3, overflow: "hidden",
                          }}
                          title={`${ev.title} — ${formatTime(ev.start)}`}
                        >
                          <div style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{ev.title}</div>
                          <div style={{ fontSize: "9px", opacity: 0.85 }}>{formatTime(ev.start)}</div>
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Event Detail Dialog */}
      <Dialog open={!!selectedEvent} onOpenChange={() => setSelectedEvent(null)}>
        <DialogContent className="sm:max-w-[480px]" style={{ fontFamily: "'Libre Franklin', sans-serif" }}>
          {selectedEvent && (
            <>
              <DialogHeader>
                <DialogTitle style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500 }}>
                  {selectedEvent.title}
                </DialogTitle>
                <DialogDescription style={{ fontSize: "12px", color: "var(--mc-ink-3)" }}>
                  {selectedEvent.calendar_name} · {selectedEvent.account_email}
                </DialogDescription>
              </DialogHeader>
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", padding: "8px 0" }}>
                {/* Time */}
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Clock size={14} style={{ color: "var(--mc-ink-4)", flexShrink: 0 }} />
                  <div style={{ fontSize: "12.5px", color: "var(--mc-ink)" }}>
                    {selectedEvent.all_day
                      ? new Date(selectedEvent.start).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric", timeZone: TZ })
                      : `${new Date(selectedEvent.start).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", timeZone: TZ })} · ${formatTime(selectedEvent.start)} – ${formatTime(selectedEvent.end)}`}
                  </div>
                </div>

                {/* Location */}
                {selectedEvent.location && (
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <MapPin size={14} style={{ color: "var(--mc-ink-4)", flexShrink: 0 }} />
                    <div style={{ fontSize: "12.5px", color: "var(--mc-ink)" }}>{selectedEvent.location}</div>
                  </div>
                )}

                {/* Video link */}
                {(selectedEvent.hangout_link || selectedEvent.conference_data) && (
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <Video size={14} style={{ color: "var(--mc-ink-4)", flexShrink: 0 }} />
                    <a
                      href={selectedEvent.hangout_link || selectedEvent.conference_data?.uri}
                      target="_blank"
                      rel="noopener noreferrer"
                      data-testid="event-video-link"
                      style={{ fontSize: "12.5px", color: "var(--mc-accent)", textDecoration: "none", display: "flex", alignItems: "center", gap: "4px" }}
                    >
                      Join video call <ExternalLink size={11} />
                    </a>
                  </div>
                )}

                {/* Attendees */}
                {selectedEvent.attendees && selectedEvent.attendees.length > 0 && (
                  <div style={{ display: "flex", alignItems: "flex-start", gap: "8px" }}>
                    <Users size={14} style={{ color: "var(--mc-ink-4)", flexShrink: 0, marginTop: "2px" }} />
                    <div style={{ fontSize: "12px", color: "var(--mc-ink-3)", lineHeight: 1.6 }}>
                      {selectedEvent.attendees.slice(0, 8).join(", ")}
                      {selectedEvent.attendees.length > 8 && ` +${selectedEvent.attendees.length - 8} more`}
                    </div>
                  </div>
                )}

                {/* Description */}
                {selectedEvent.description && (
                  <div style={{ fontSize: "12px", color: "var(--mc-ink-3)", lineHeight: 1.6, borderTop: "1px solid var(--mc-rule)", paddingTop: "10px", whiteSpace: "pre-wrap", maxHeight: "120px", overflow: "auto" }}>
                    {selectedEvent.description}
                  </div>
                )}

                {/* Organizer */}
                {selectedEvent.organizer && (
                  <div style={{ fontSize: "11px", color: "var(--mc-ink-4)" }}>
                    Organized by {selectedEvent.organizer}
                  </div>
                )}
              </div>
              <DialogFooter>
                <button className="mc-btn mc-btn-outline" onClick={() => setSelectedEvent(null)}>Close</button>
                {selectedEvent.html_link && (
                  <a href={selectedEvent.html_link} target="_blank" rel="noopener noreferrer" className="mc-btn mc-btn-accent" style={{ gap: "4px", textDecoration: "none" }} data-testid="event-open-google">
                    Open in Google Calendar <ExternalLink size={11} />
                  </a>
                )}
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Event Dialog */}
      <Dialog open={showCreateEvent} onOpenChange={setShowCreateEvent}>
        <DialogContent className="sm:max-w-[480px]" style={{ fontFamily: "'Libre Franklin', sans-serif" }}>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500 }}>
              Create Event
            </DialogTitle>
            <DialogDescription style={{ fontSize: "12px", color: "var(--mc-ink-3)" }}>
              Add a new event to your Google Calendar.
            </DialogDescription>
          </DialogHeader>
          <div style={{ display: "flex", flexDirection: "column", gap: "14px", padding: "8px 0" }}>
            <div>
              <label className="mc-dialog-label">Title</label>
              <input
                className="mc-dialog-input"
                value={newEvent.title}
                onChange={(e) => setNewEvent((p) => ({ ...p, title: e.target.value }))}
                placeholder="Meeting with team"
                data-testid="create-event-title"
              />
            </div>
            <div style={{ display: "flex", gap: "10px" }}>
              <div style={{ flex: 1 }}>
                <label className="mc-dialog-label">Start</label>
                <input
                  className="mc-dialog-input"
                  type={newEvent.all_day ? "date" : "datetime-local"}
                  value={newEvent.start}
                  onChange={(e) => setNewEvent((p) => ({ ...p, start: e.target.value }))}
                  data-testid="create-event-start"
                />
              </div>
              <div style={{ flex: 1 }}>
                <label className="mc-dialog-label">End</label>
                <input
                  className="mc-dialog-input"
                  type={newEvent.all_day ? "date" : "datetime-local"}
                  value={newEvent.end}
                  onChange={(e) => setNewEvent((p) => ({ ...p, end: e.target.value }))}
                  data-testid="create-event-end"
                />
              </div>
            </div>
            <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "var(--mc-ink-3)", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={newEvent.all_day}
                onChange={(e) => setNewEvent((p) => ({ ...p, all_day: e.target.checked }))}
              />
              All day event
            </label>
            <div>
              <label className="mc-dialog-label">Location</label>
              <input
                className="mc-dialog-input"
                value={newEvent.location}
                onChange={(e) => setNewEvent((p) => ({ ...p, location: e.target.value }))}
                placeholder="Office / Zoom link"
                data-testid="create-event-location"
              />
            </div>
            <div>
              <label className="mc-dialog-label">Description</label>
              <textarea
                className="mc-dialog-input"
                value={newEvent.description}
                onChange={(e) => setNewEvent((p) => ({ ...p, description: e.target.value }))}
                placeholder="Notes..."
                rows={3}
                style={{ resize: "vertical" }}
                data-testid="create-event-description"
              />
            </div>
          </div>
          <DialogFooter>
            <button className="mc-btn mc-btn-outline" onClick={() => setShowCreateEvent(false)}>Cancel</button>
            <button
              className="mc-btn mc-btn-approve"
              onClick={handleCreateEvent}
              disabled={creating || !newEvent.title || !newEvent.start || !newEvent.end}
              data-testid="create-event-submit"
              style={{ gap: "4px" }}
            >
              <Plus size={12} />
              {creating ? "Creating..." : "Create Event"}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
