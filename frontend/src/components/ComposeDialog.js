import { useState, useEffect } from "react";
import { composeEmail, fetchAgentMailInboxes, fetchTemplates, createTemplate, deleteTemplate } from "@/lib/api";
import { Send, BookOpen, Save, Trash2, ChevronDown, ChevronUp } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

export default function ComposeDialog({ open, onOpenChange, defaultInbox, onSent }) {
  const [inboxes, setInboxes] = useState([]);
  const [inboxId, setInboxId] = useState(defaultInbox || "");
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const [savingTemplate, setSavingTemplate] = useState(false);
  const [templateName, setTemplateName] = useState("");
  const [showSaveForm, setShowSaveForm] = useState(false);

  useEffect(() => {
    if (open) {
      fetchAgentMailInboxes().then(setInboxes).catch(console.error);
      fetchTemplates().then(setTemplates).catch(console.error);
      setInboxId(defaultInbox || "");
      setTo("");
      setSubject("");
      setBody("");
      setSent(false);
      setShowTemplates(false);
      setShowSaveForm(false);
      setTemplateName("");
    }
  }, [open, defaultInbox]);

  const handleSend = async () => {
    if (!inboxId || !to.trim() || !subject.trim()) return;
    setSending(true);
    try {
      const toList = to.split(",").map(s => s.trim()).filter(Boolean);
      await composeEmail({
        inbox_id: inboxId,
        to: toList,
        subject: subject.trim(),
        text: body,
      });
      setSent(true);
      setTimeout(() => {
        onOpenChange(false);
        if (onSent) onSent();
      }, 1200);
    } catch (e) {
      console.error(e);
    } finally {
      setSending(false);
    }
  };

  const handleLoadTemplate = (tpl) => {
    setSubject(tpl.subject || "");
    setBody(tpl.body || "");
    setShowTemplates(false);
  };

  const handleSaveTemplate = async () => {
    if (!templateName.trim()) return;
    setSavingTemplate(true);
    try {
      const newTpl = await createTemplate({
        name: templateName.trim(),
        subject,
        body,
      });
      setTemplates(prev => [newTpl, ...prev]);
      setShowSaveForm(false);
      setTemplateName("");
    } catch (e) {
      console.error(e);
    } finally {
      setSavingTemplate(false);
    }
  };

  const handleDeleteTemplate = async (id) => {
    try {
      await deleteTemplate(id);
      setTemplates(prev => prev.filter(t => t.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-[600px]"
        style={{ fontFamily: "'Libre Franklin', sans-serif", maxHeight: "85vh", overflow: "auto" }}
      >
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "18px", fontWeight: 500 }}>
            {sent ? "Email Sent" : "Compose Email"}
          </DialogTitle>
          {!sent && (
            <DialogDescription style={{ fontSize: "12px", color: "var(--mc-ink-3)" }}>
              Send a new email from one of your AgentMail inboxes.
            </DialogDescription>
          )}
        </DialogHeader>

        {sent ? (
          <div style={{ padding: "20px 0", textAlign: "center" }}>
            <div style={{
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              background: "var(--mc-green-bg)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 12px",
            }}>
              <Send size={16} style={{ color: "var(--mc-green)" }} />
            </div>
            <div style={{ fontSize: "14px", fontWeight: 500, color: "var(--mc-ink)" }}>
              Email sent successfully
            </div>
            <div style={{ fontSize: "12px", color: "var(--mc-ink-3)", marginTop: "4px" }}>
              {subject} &rarr; {to}
            </div>
          </div>
        ) : (
          <>
            {/* Template bar */}
            <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "4px" }}>
              <button
                className="mc-btn mc-btn-outline mc-btn-sm"
                onClick={() => { setShowTemplates(!showTemplates); setShowSaveForm(false); }}
                data-testid="templates-toggle-btn"
                style={{ gap: "4px" }}
              >
                <BookOpen size={11} />
                Templates
                {showTemplates ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
              </button>
              {(subject || body) && (
                <button
                  className="mc-btn mc-btn-outline mc-btn-sm"
                  onClick={() => setShowSaveForm(!showSaveForm)}
                  data-testid="save-template-toggle-btn"
                  style={{ gap: "4px" }}
                >
                  <Save size={11} />
                  Save as Template
                </button>
              )}
            </div>

            {/* Template save form */}
            {showSaveForm && (
              <div style={{
                border: "1px solid var(--mc-rule)",
                borderRadius: "var(--mc-radius)",
                padding: "10px 12px",
                marginBottom: "8px",
                background: "var(--mc-off-white)",
              }} data-testid="save-template-form">
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <input
                    className="mc-dialog-input"
                    value={templateName}
                    onChange={e => setTemplateName(e.target.value)}
                    placeholder="Template name..."
                    data-testid="template-name-input"
                    style={{ flex: 1, fontSize: "12px", padding: "6px 10px" }}
                  />
                  <button
                    className="mc-btn mc-btn-approve mc-btn-sm"
                    onClick={handleSaveTemplate}
                    disabled={savingTemplate || !templateName.trim()}
                    data-testid="save-template-btn"
                  >
                    {savingTemplate ? "Saving..." : "Save"}
                  </button>
                </div>
              </div>
            )}

            {/* Template list */}
            {showTemplates && (
              <div style={{
                border: "1px solid var(--mc-rule)",
                borderRadius: "var(--mc-radius)",
                marginBottom: "8px",
                maxHeight: "160px",
                overflowY: "auto",
                background: "var(--mc-off-white)",
              }} data-testid="templates-list">
                {templates.length === 0 ? (
                  <div style={{
                    padding: "16px",
                    textAlign: "center",
                    fontSize: "11px",
                    color: "var(--mc-ink-3)",
                    fontStyle: "italic",
                  }}>
                    No saved templates yet. Compose an email and save it as a template.
                  </div>
                ) : (
                  templates.map(tpl => (
                    <div
                      key={tpl.id}
                      data-testid={`template-item-${tpl.id}`}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        padding: "8px 12px",
                        borderBottom: "1px solid var(--mc-rule)",
                        cursor: "pointer",
                        transition: "background-color 150ms",
                      }}
                      onMouseEnter={e => e.currentTarget.style.backgroundColor = "var(--mc-warm-gray)"}
                      onMouseLeave={e => e.currentTarget.style.backgroundColor = "transparent"}
                    >
                      <div
                        style={{ flex: 1, minWidth: 0 }}
                        onClick={() => handleLoadTemplate(tpl)}
                      >
                        <div style={{ fontSize: "12px", fontWeight: 500, color: "var(--mc-ink)" }}>
                          {tpl.name}
                        </div>
                        <div style={{
                          fontSize: "10.5px",
                          color: "var(--mc-ink-3)",
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}>
                          {tpl.subject || "No subject"}
                        </div>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDeleteTemplate(tpl.id); }}
                        data-testid={`delete-template-${tpl.id}`}
                        style={{
                          background: "none",
                          border: "none",
                          cursor: "pointer",
                          color: "var(--mc-ink-4)",
                          padding: "4px",
                          display: "flex",
                          alignItems: "center",
                          flexShrink: 0,
                        }}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: "14px", padding: "8px 0" }}>
              {/* From inbox */}
              <div>
                <label className="mc-dialog-label">From</label>
                <select
                  className="mc-dialog-input"
                  value={inboxId}
                  onChange={e => setInboxId(e.target.value)}
                  data-testid="compose-from-select"
                >
                  <option value="">Select inbox...</option>
                  {inboxes.map(inbox => (
                    <option key={inbox.inbox_id} value={inbox.inbox_id}>
                      {inbox.display_name || inbox.email} ({inbox.email})
                    </option>
                  ))}
                </select>
              </div>

              {/* To */}
              <div>
                <label className="mc-dialog-label">To</label>
                <input
                  className="mc-dialog-input"
                  value={to}
                  onChange={e => setTo(e.target.value)}
                  placeholder="recipient@example.com (comma-separated for multiple)"
                  data-testid="compose-to-input"
                />
              </div>

              {/* Subject */}
              <div>
                <label className="mc-dialog-label">Subject</label>
                <input
                  className="mc-dialog-input"
                  value={subject}
                  onChange={e => setSubject(e.target.value)}
                  placeholder="Email subject"
                  data-testid="compose-subject-input"
                />
              </div>

              {/* Body */}
              <div>
                <label className="mc-dialog-label">Message</label>
                <textarea
                  className="mc-dialog-input"
                  value={body}
                  onChange={e => setBody(e.target.value)}
                  placeholder="Write your message..."
                  data-testid="compose-body-input"
                  rows={10}
                  style={{
                    resize: "vertical",
                    fontFamily: "'Libre Franklin', sans-serif",
                    lineHeight: 1.6,
                    minHeight: "160px",
                  }}
                />
              </div>
            </div>

            <DialogFooter style={{ marginTop: "8px" }}>
              <button
                className="mc-btn mc-btn-outline"
                onClick={() => onOpenChange(false)}
                data-testid="compose-cancel-btn"
              >
                Cancel
              </button>
              <button
                className="mc-btn mc-btn-approve"
                onClick={handleSend}
                disabled={sending || !inboxId || !to.trim() || !subject.trim()}
                data-testid="compose-send-btn"
                style={{ gap: "6px" }}
              >
                <Send size={12} />
                {sending ? "Sending..." : "Send"}
              </button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
