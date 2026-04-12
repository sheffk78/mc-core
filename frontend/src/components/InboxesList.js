import { useState, useEffect, useCallback } from "react";
import { fetchAgentMailInboxes, fetchAgentMailMessages, updateMessageLabels } from "@/lib/api";
import { getBrandColor, getBrandName, timeAgo } from "@/lib/brands";
import { Mail, ChevronRight, ArrowLeft, Circle, Search, X, Send as SendIcon } from "lucide-react";
import MessageViewer from "@/components/MessageViewer";

const TABS = [
  { key: "all", label: "All" },
  { key: "received", label: "Received" },
  { key: "sent", label: "Sent" },
];

/**
 * Group messages into threads. Each thread shows as one line.
 * A thread is "unread" if any received message in it is unread.
 * A thread shows "Sent" badge if the latest message is sent by us.
 * A thread shows "Draft" badge if it has a draft label.
 */
function groupByThread(messages) {
  const threads = new Map();
  for (const msg of messages) {
    const tid = msg.thread_id || msg.message_id;
    if (!threads.has(tid)) {
      threads.set(tid, {
        thread_id: tid,
        subject: msg.subject || "(no subject)",
        from: msg.from,
        text: msg.text,
        created_at: msg.created_at,
        latest_at: msg.created_at,
        message_count: 0,
        has_unread: false,
        has_sent: false,
        has_draft: false,
        messages: [],
      });
    }
    const t = threads.get(tid);
    t.messages.push(msg);
    t.message_count++;

    // Track latest timestamp
    if (msg.created_at > t.latest_at) {
      t.latest_at = msg.created_at;
      t.text = msg.text; // preview from latest message
      t.from = msg.from;
    }

    const labels = msg.labels || [];
    if (labels.includes("received") && !labels.includes("read")) {
      t.has_unread = true;
    }
    if (labels.includes("sent")) {
      t.has_sent = true;
    }
    if (labels.includes("draft")) {
      t.has_draft = true;
    }
  }

  // Determine display status: check if the absolute latest message is sent
  const result = [];
  for (const t of threads.values()) {
    // Sort messages by time
    t.messages.sort((a, b) => (a.created_at || "").localeCompare(b.created_at || ""));
    const latest = t.messages[t.messages.length - 1];
    const latestLabels = latest?.labels || [];
    t.latest_is_sent = latestLabels.includes("sent");
    t.latest_is_draft = latestLabels.includes("draft");
    // Use the thread's subject from any message that has one
    for (const m of t.messages) {
      if (m.subject && m.subject !== "(no subject)") {
        t.subject = m.subject;
        break;
      }
    }
    result.push(t);
  }

  // Sort threads by latest activity (most recent first)
  result.sort((a, b) => (b.latest_at || "").localeCompare(a.latest_at || ""));
  return result;
}

export default function InboxesList({ brand, brands, limit, embedded, refreshKey }) {
  const [inboxes, setInboxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedInbox, setSelectedInbox] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [selectedThread, setSelectedThread] = useState(null);
  const [activeTab, setActiveTab] = useState("all");
  const [msgSearch, setMsgSearch] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    fetchAgentMailInboxes(brand)
      .then(data => setInboxes(limit ? data.slice(0, limit) : data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [brand, limit]);

  useEffect(() => { load(); }, [load, refreshKey]);

  const openInbox = async (inbox, tab = "all") => {
    setSelectedInbox(inbox);
    setMessagesLoading(true);
    setSelectedThread(null);
    setActiveTab(tab);
    try {
      const labels = tab === "all" ? null : tab;
      const data = await fetchAgentMailMessages(inbox.inbox_id, 50, labels);
      setMessages(data.messages || []);
    } catch (e) {
      console.error(e);
      setMessages([]);
    } finally {
      setMessagesLoading(false);
    }
  };

  const switchTab = async (tab) => {
    if (!selectedInbox) return;
    setActiveTab(tab);
    setMessagesLoading(true);
    try {
      const labels = tab === "all" ? null : tab;
      const data = await fetchAgentMailMessages(selectedInbox.inbox_id, 50, labels);
      setMessages(data.messages || []);
    } catch (e) {
      console.error(e);
    } finally {
      setMessagesLoading(false);
    }
  };

  // Auto-mark all unread messages in a thread as read when opening
  const openThread = async (thread) => {
    setSelectedThread(thread.thread_id);

    // Mark unread messages as read
    if (selectedInbox && thread.has_unread) {
      for (const msg of thread.messages) {
        const labels = msg.labels || [];
        if (labels.includes("received") && !labels.includes("read")) {
          updateMessageLabels(selectedInbox.inbox_id, msg.message_id, ["read"], ["unread"]).catch(() => {});
        }
      }
      // Update local state
      setMessages(prev => prev.map(m => {
        if ((m.thread_id || m.message_id) === thread.thread_id) {
          const labels = m.labels || [];
          if (labels.includes("received") && !labels.includes("read")) {
            return { ...m, labels: [...labels.filter(l => l !== "unread"), "read"] };
          }
        }
        return m;
      }));
    }
  };

  const handleThreadBack = () => {
    setSelectedThread(null);
    // Refresh messages to pick up any changes (sent replies, etc.)
    if (selectedInbox) {
      const labels = activeTab === "all" ? null : activeTab;
      fetchAgentMailMessages(selectedInbox.inbox_id, 50, labels)
        .then(data => setMessages(data.messages || []))
        .catch(() => {});
    }
  };

  const goBack = () => {
    setSelectedInbox(null);
    setMessages([]);
    setActiveTab("all");
    setMsgSearch("");
  };

  // Thread view
  if (selectedThread) {
    return <MessageViewer threadId={selectedThread} onBack={handleThreadBack} />;
  }

  // Message list for selected inbox (grouped by thread)
  if (selectedInbox && !embedded) {
    const threads = groupByThread(messages);
    const q = msgSearch.toLowerCase();
    const filtered = q
      ? threads.filter(t =>
          t.subject.toLowerCase().includes(q) ||
          (typeof t.from === "string" ? t.from : "").toLowerCase().includes(q) ||
          (t.text || "").toLowerCase().includes(q)
        )
      : threads;

    return (
      <div data-testid="inbox-messages-view">
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
          <button className="mc-btn mc-btn-outline mc-btn-sm" onClick={goBack} data-testid="inbox-back-btn">
            <ArrowLeft size={12} /> Back
          </button>
          <div>
            <div style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "16px", fontWeight: 500 }}>
              {selectedInbox.display_name || selectedInbox.email}
            </div>
            <div style={{ fontSize: "11px", color: "var(--mc-ink-3)" }}>{selectedInbox.email}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mc-card">
          <div className="mc-card-header" style={{ gap: "0", padding: "0 20px" }}>
            {TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => switchTab(tab.key)}
                data-testid={`inbox-tab-${tab.key}`}
                style={{
                  fontFamily: "'Libre Franklin', sans-serif",
                  fontSize: "11.5px",
                  fontWeight: activeTab === tab.key ? 600 : 400,
                  color: activeTab === tab.key ? "var(--mc-accent)" : "var(--mc-ink-3)",
                  background: "none",
                  border: "none",
                  borderBottom: activeTab === tab.key ? "2px solid var(--mc-accent)" : "2px solid transparent",
                  padding: "12px 16px",
                  cursor: "pointer",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  transition: "all 150ms",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="mc-card-body">
            {/* Search */}
            <div style={{ padding: "10px 20px 0" }}>
              <div className="mc-search-bar" data-testid="inbox-search-bar">
                <Search size={13} style={{ color: "var(--mc-ink-4)", flexShrink: 0 }} />
                <input
                  type="text"
                  placeholder="Filter messages..."
                  value={msgSearch}
                  onChange={e => setMsgSearch(e.target.value)}
                  className="mc-search-input"
                  data-testid="inbox-search-input"
                />
                {msgSearch && (
                  <button
                    onClick={() => setMsgSearch("")}
                    style={{ background: "none", border: "none", cursor: "pointer", color: "var(--mc-ink-4)", padding: "2px", display: "flex", alignItems: "center" }}
                    data-testid="inbox-search-clear"
                  >
                    <X size={13} />
                  </button>
                )}
              </div>
            </div>
            {messagesLoading ? (
              <div className="mc-empty">Loading messages...</div>
            ) : filtered.length === 0 ? (
              <div className="mc-empty" data-testid="messages-empty">
                {msgSearch ? "No matching messages" : "No messages"}
              </div>
            ) : (
              filtered.map((thread) => {
                const isUnread = thread.has_unread;
                return (
                  <div
                    key={thread.thread_id}
                    data-testid={`thread-item-${thread.thread_id}`}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "10px",
                      padding: "12px 20px",
                      borderBottom: "1px solid var(--mc-rule)",
                      cursor: "pointer",
                      transition: "background-color 150ms",
                      background: isUnread ? "var(--mc-accent-bg)" : "transparent",
                    }}
                    onClick={() => openThread(thread)}
                    onMouseEnter={e => { if (!isUnread) e.currentTarget.style.backgroundColor = "var(--mc-warm-gray)"; }}
                    onMouseLeave={e => e.currentTarget.style.backgroundColor = isUnread ? "var(--mc-accent-bg)" : "transparent"}
                  >
                    {/* Unread dot */}
                    <div style={{ width: "8px", paddingTop: "6px", flexShrink: 0 }}>
                      {isUnread && (
                        <Circle size={7} fill="var(--mc-accent)" stroke="none" data-testid="unread-indicator" />
                      )}
                    </div>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "2px" }}>
                        <span style={{
                          fontSize: "12.5px",
                          fontWeight: isUnread ? 600 : 400,
                          color: "var(--mc-ink)",
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          flex: 1,
                        }}>
                          {thread.subject}
                        </span>
                        {thread.message_count > 1 && (
                          <span style={{
                            fontSize: "9px", fontWeight: 500, color: "var(--mc-ink-4)",
                            background: "var(--mc-warm-gray)", padding: "1px 5px",
                            borderRadius: "3px", flexShrink: 0,
                          }}>
                            {thread.message_count}
                          </span>
                        )}
                        {thread.latest_is_sent && (
                          <span style={{
                            fontSize: "9px", fontWeight: 600, textTransform: "uppercase",
                            letterSpacing: "0.06em", color: "var(--mc-blue)",
                            background: "var(--mc-blue-bg)", padding: "1px 6px",
                            borderRadius: "3px", flexShrink: 0,
                          }} data-testid="sent-badge">Sent</span>
                        )}
                        {thread.has_draft && !thread.latest_is_sent && (
                          <span style={{
                            fontSize: "9px", fontWeight: 600, textTransform: "uppercase",
                            letterSpacing: "0.06em", color: "var(--mc-amber)",
                            background: "var(--mc-amber-bg)", padding: "1px 6px",
                            borderRadius: "3px", flexShrink: 0,
                          }} data-testid="draft-badge">Draft</span>
                        )}
                      </div>
                      <div style={{ fontSize: "11px", color: "var(--mc-ink-3)", marginBottom: "2px" }}>
                        {typeof thread.from === "string" ? thread.from : (thread.from || "")}
                      </div>
                      <div style={{
                        fontSize: "11.5px", fontWeight: 300, color: "var(--mc-ink-2)",
                        display: "-webkit-box", WebkitLineClamp: 1, WebkitBoxOrient: "vertical", overflow: "hidden",
                      }}>
                        {thread.text ? thread.text.substring(0, 120) : ""}
                      </div>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px", flexShrink: 0 }}>
                      <span style={{ fontSize: "10px", color: "var(--mc-ink-4)", whiteSpace: "nowrap" }}>
                        {timeAgo(thread.latest_at)}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    );
  }

  // Inbox list
  if (loading) return <div className="mc-empty">Loading inboxes...</div>;
  if (inboxes.length === 0) return <div className="mc-empty" data-testid="inboxes-empty">No inboxes found</div>;

  return (
    <div data-testid="inboxes-list">
      {inboxes.map(inbox => (
        <div
          key={inbox.inbox_id}
          className="mc-inbox-item"
          data-testid={`inbox-item-${inbox.inbox_id}`}
          onClick={() => !embedded && openInbox(inbox)}
          style={!embedded ? { cursor: "pointer" } : {}}
        >
          <div className="mc-inbox-icon"><Mail size={14} /></div>
          <div className="mc-inbox-info">
            <div className="mc-inbox-address">{inbox.display_name || inbox.email}</div>
            <div className="mc-inbox-stat">{inbox.email}</div>
          </div>
          <div className="mc-inbox-right">
            <span className={`mc-inbox-count ${inbox.message_count === 0 ? "none" : ""}`}>
              {inbox.message_count}
            </span>
            <span className="mc-inbox-time">{timeAgo(inbox.last_activity)}</span>
          </div>
          {!embedded && <ChevronRight size={14} style={{ color: "var(--mc-ink-4)", flexShrink: 0, marginLeft: "4px" }} />}
        </div>
      ))}
    </div>
  );
}
