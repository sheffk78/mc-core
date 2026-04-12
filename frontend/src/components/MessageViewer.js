import { useState, useEffect, useCallback } from "react";
import { fetchAgentMailThread, replyToMessage } from "@/lib/api";
import { timeAgo } from "@/lib/brands";
import { ArrowLeft, User, Send, Check, FileEdit } from "lucide-react";

export default function MessageViewer({ threadId, onBack }) {
  const [thread, setThread] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedMsg, setExpandedMsg] = useState(null);
  const [draftText, setDraftText] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [editingDraft, setEditingDraft] = useState(false);

  const loadThread = useCallback(() => {
    setLoading(true);
    fetchAgentMailThread(threadId)
      .then(data => {
        setThread(data);
        if (data.messages && data.messages.length > 0) {
          // Auto-expand the latest message
          setExpandedMsg(data.messages[data.messages.length - 1].message_id);

          // Check if the last message is a draft (from Kit)
          const lastMsg = data.messages[data.messages.length - 1];
          const labels = lastMsg.labels || [];
          if (labels.includes("draft")) {
            setDraftText(lastMsg.text || "");
          }
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [threadId]);

  useEffect(() => { loadThread(); }, [loadThread]);

  const handleSend = async () => {
    if (!draftText.trim() || !thread) return;
    setSending(true);
    try {
      // Find the last non-draft received message to reply to
      const receivedMessages = thread.messages.filter(m => {
        const labels = m.labels || [];
        return !labels.includes("draft") && !labels.includes("sent");
      });
      const replyTo = receivedMessages.length > 0
        ? receivedMessages[receivedMessages.length - 1]
        : thread.messages[0];

      await replyToMessage(thread.inbox_id, replyTo.message_id, { text: draftText.trim() });
      setSent(true);
      setTimeout(() => {
        setSent(false);
        setEditingDraft(false);
        setDraftText("");
        loadThread();
      }, 1500);
    } catch (e) {
      console.error(e);
    } finally {
      setSending(false);
    }
  };

  if (loading) return <div className="mc-empty">Loading thread...</div>;
  if (!thread) return <div className="mc-empty">Thread not found</div>;

  // Separate draft messages from regular messages
  const regularMessages = [];
  let draftMessage = null;
  for (const msg of (thread.messages || [])) {
    const labels = msg.labels || [];
    if (labels.includes("draft")) {
      draftMessage = msg;
    } else {
      regularMessages.push(msg);
    }
  }

  return (
    <div data-testid="thread-viewer">
      <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
        <button className="mc-btn mc-btn-outline mc-btn-sm" onClick={onBack} data-testid="thread-back-btn">
          <ArrowLeft size={12} /> Back
        </button>
      </div>

      <div className="mc-card">
        <div className="mc-card-header" style={{ flexDirection: "column", alignItems: "flex-start", gap: "4px" }}>
          <span className="mc-card-title" style={{ fontSize: "16px" }}>
            {thread.subject || "(no subject)"}
          </span>
          <span style={{ fontSize: "11px", color: "var(--mc-ink-3)" }}>
            {thread.message_count} message{thread.message_count !== 1 ? "s" : ""} in this thread
          </span>
        </div>
        <div className="mc-card-body">
          {/* Regular messages */}
          {regularMessages.map((msg, idx) => {
            const isExpanded = expandedMsg === msg.message_id;
            const fromStr = typeof msg.from === "string" ? msg.from : JSON.stringify(msg.from || "");
            const toStr = Array.isArray(msg.to) ? msg.to.join(", ") : (msg.to || "");
            const labels = msg.labels || [];
            const isSent = labels.includes("sent");

            return (
              <div
                key={msg.message_id || idx}
                data-testid={`thread-message-${idx}`}
                style={{ borderBottom: "1px solid var(--mc-rule)" }}
              >
                {/* Message header */}
                <div
                  onClick={() => setExpandedMsg(isExpanded ? null : msg.message_id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "12px 20px",
                    cursor: "pointer",
                    transition: "background-color 150ms",
                    background: isExpanded ? "var(--mc-warm-gray)" : "transparent",
                  }}
                  onMouseEnter={e => { if (!isExpanded) e.currentTarget.style.backgroundColor = "var(--mc-warm-gray)"; }}
                  onMouseLeave={e => { if (!isExpanded) e.currentTarget.style.backgroundColor = "transparent"; }}
                >
                  <div style={{
                    width: "28px", height: "28px", borderRadius: "50%", background: "var(--mc-warm-gray-2)",
                    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                  }}>
                    <User size={13} style={{ color: "var(--mc-ink-3)" }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span style={{ fontSize: "12.5px", fontWeight: 500, color: "var(--mc-ink)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {fromStr}
                      </span>
                      {isSent && (
                        <span style={{
                          fontSize: "8px", fontWeight: 600, textTransform: "uppercase",
                          letterSpacing: "0.06em", color: "var(--mc-blue)",
                          background: "var(--mc-blue-bg)", padding: "1px 5px",
                          borderRadius: "3px",
                        }}>Sent</span>
                      )}
                    </div>
                    {!isExpanded && msg.text && (
                      <div style={{ fontSize: "11px", fontWeight: 300, color: "var(--mc-ink-3)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {msg.text.substring(0, 100)}
                      </div>
                    )}
                  </div>
                  <span style={{ fontSize: "10px", color: "var(--mc-ink-4)", whiteSpace: "nowrap", flexShrink: 0 }}>
                    {timeAgo(msg.created_at)}
                  </span>
                </div>

                {/* Expanded body */}
                {isExpanded && (
                  <div style={{ padding: "0 20px 16px 58px" }}>
                    <div style={{ fontSize: "10.5px", color: "var(--mc-ink-3)", marginBottom: "10px" }}>
                      To: {toStr}
                    </div>
                    {msg.html ? (
                      <div
                        style={{
                          fontSize: "13px", lineHeight: "1.6", color: "var(--mc-ink-2)",
                          background: "var(--mc-off-white)", padding: "16px", borderRadius: "var(--mc-radius)",
                          border: "1px solid var(--mc-rule)", maxHeight: "400px", overflow: "auto",
                          wordBreak: "break-word", overflowWrap: "anywhere",
                        }}
                        dangerouslySetInnerHTML={{ __html: msg.html }}
                        data-testid="message-html-body"
                      />
                    ) : (
                      <div
                        style={{
                          fontSize: "13px", lineHeight: "1.6", color: "var(--mc-ink-2)", whiteSpace: "pre-wrap",
                          background: "var(--mc-off-white)", padding: "16px", borderRadius: "var(--mc-radius)",
                          border: "1px solid var(--mc-rule)", maxHeight: "400px", overflow: "auto",
                          wordBreak: "break-word", overflowWrap: "anywhere",
                        }}
                        data-testid="message-text-body"
                      >
                        {msg.text || "(empty message)"}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Draft section — shown if Kit has written a draft or user wants to compose */}
      {sent ? (
        <div className="mc-card" style={{ marginTop: "12px" }}>
          <div style={{ padding: "20px", textAlign: "center" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "6px", color: "var(--mc-green)", fontSize: "13px", fontWeight: 500 }}>
              <Check size={15} /> Reply sent successfully
            </div>
          </div>
        </div>
      ) : draftMessage || draftText || editingDraft ? (
        <div className="mc-card" style={{ marginTop: "12px", border: "1px solid var(--mc-amber)" }} data-testid="draft-card">
          <div className="mc-card-header" style={{ background: "var(--mc-amber-bg)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <FileEdit size={13} style={{ color: "var(--mc-amber)" }} />
              <span style={{
                fontSize: "10px", fontWeight: 700, textTransform: "uppercase",
                letterSpacing: "0.1em", color: "var(--mc-amber)",
              }}>
                Draft
              </span>
              {draftMessage && (
                <span style={{ fontSize: "10px", color: "var(--mc-ink-4)", fontWeight: 400, textTransform: "none", letterSpacing: "normal" }}>
                  by Kit · {timeAgo(draftMessage.created_at)}
                </span>
              )}
            </div>
          </div>
          <div style={{ padding: "16px 20px" }}>
            {editingDraft ? (
              <textarea
                className="mc-dialog-input"
                value={draftText}
                onChange={e => setDraftText(e.target.value)}
                data-testid="draft-edit-input"
                rows={8}
                autoFocus
                style={{
                  resize: "vertical",
                  fontFamily: "'Libre Franklin', sans-serif",
                  lineHeight: 1.6,
                  minHeight: "120px",
                  marginBottom: "12px",
                  fontSize: "13px",
                }}
              />
            ) : (
              <div
                style={{
                  fontSize: "13px", lineHeight: "1.6", color: "var(--mc-ink-2)", whiteSpace: "pre-wrap",
                  background: "var(--mc-off-white)", padding: "16px", borderRadius: "var(--mc-radius)",
                  border: "1px solid var(--mc-rule)", maxHeight: "320px", overflow: "auto",
                  wordBreak: "break-word", overflowWrap: "anywhere", marginBottom: "12px",
                  cursor: "pointer",
                }}
                onClick={() => { setEditingDraft(true); if (!draftText && draftMessage) setDraftText(draftMessage.text || ""); }}
                data-testid="draft-display"
                title="Click to edit"
              >
                {draftText || draftMessage?.text || "(empty draft)"}
              </div>
            )}

            <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
              {!editingDraft ? (
                <button
                  className="mc-btn mc-btn-outline mc-btn-sm"
                  onClick={() => { setEditingDraft(true); if (!draftText && draftMessage) setDraftText(draftMessage.text || ""); }}
                  data-testid="draft-edit-btn"
                  style={{ gap: "5px" }}
                >
                  <FileEdit size={11} /> Edit
                </button>
              ) : (
                <button
                  className="mc-btn mc-btn-outline mc-btn-sm"
                  onClick={() => setEditingDraft(false)}
                  data-testid="draft-preview-btn"
                >
                  Preview
                </button>
              )}
              <button
                className="mc-btn mc-btn-approve mc-btn-sm"
                onClick={handleSend}
                disabled={sending || !draftText.trim()}
                data-testid="draft-send-btn"
                style={{ gap: "6px" }}
              >
                <Send size={11} />
                {sending ? "Sending..." : "Send"}
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* No draft — show reply button */
        <div className="mc-card" style={{ marginTop: "12px" }}>
          <div style={{ padding: "12px 20px" }}>
            <button
              className="mc-btn mc-btn-outline"
              onClick={() => { setDraftText(""); setEditingDraft(true); }}
              data-testid="reply-open-btn"
              style={{ width: "100%", justifyContent: "center", gap: "6px", color: "var(--mc-ink-2)" }}
            >
              <Send size={12} /> Reply to this thread
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
