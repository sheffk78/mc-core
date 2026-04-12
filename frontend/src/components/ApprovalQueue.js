import { useState, useEffect, useCallback, useRef } from "react";
import { fetchApprovals, approveItem, rejectItem, discardItem, updateTaskStatus } from "@/lib/api";
import { getBrandColor, getBrandName, timeAgo } from "@/lib/brands";
import { Check, X, Pencil, Send, ArrowRight, Search, ClipboardList, Flag, Keyboard } from "lucide-react";
import EditDraftDialog from "@/components/EditDraftDialog";

export default function ApprovalQueue({ brand, brands, onAction, limit, embedded, refreshKey }) {
  const [items, setItems] = useState([]);
  const [animatingId, setAnimatingId] = useState(null);
  const [sendingId, setSendingId] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [sentFeedback, setSentFeedback] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchTimer = useRef(null);
  const itemRefs = useRef([]);

  const handleSearchChange = (val) => {
    setSearchQuery(val);
    clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => setDebouncedSearch(val), 300);
  };

  const load = useCallback(() => {
    fetchApprovals(brand, "pending", debouncedSearch).then(data => {
      setItems(limit ? data.slice(0, limit) : data);
    }).catch(console.error);
  }, [brand, limit, debouncedSearch]);

  useEffect(() => { load(); }, [load, refreshKey]);

  // Reset selection when items change
  useEffect(() => {
    setSelectedIndex(idx => (items.length === 0 ? -1 : Math.min(idx, items.length - 1)));
  }, [items.length]);

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && itemRefs.current[selectedIndex]) {
      itemRefs.current[selectedIndex].scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }, [selectedIndex]);

  // Keyboard shortcuts
  useEffect(() => {
    if (embedded) return; // no shortcuts in embedded/overview mode

    const handler = (e) => {
      // Skip when typing in inputs/textareas
      const tag = e.target.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || e.target.isContentEditable) return;
      // Skip when a dialog is open
      if (editingItem) return;

      const key = e.key.toLowerCase();

      if (key === "arrowdown" || key === "j") {
        e.preventDefault();
        setSelectedIndex(idx => Math.min(idx + 1, items.length - 1));
      } else if (key === "arrowup" || key === "k") {
        e.preventDefault();
        setSelectedIndex(idx => Math.max(idx - 1, 0));
      } else if (key === "a" && selectedIndex >= 0 && selectedIndex < items.length) {
        e.preventDefault();
        const item = items[selectedIndex];
        if (sendingId || animatingId) return;
        const isTaskApproval = item.source === "task" || item.type === "task_approval";
        if (isTaskApproval) {
          handleTaskApprove(item);
        } else {
          handleApprove(item);
        }
      } else if (key === "d" && selectedIndex >= 0 && selectedIndex < items.length) {
        e.preventDefault();
        const item = items[selectedIndex];
        if (sendingId || animatingId) return;
        const isTaskApproval = item.source === "task" || item.type === "task_approval";
        if (isTaskApproval) {
          // "Send Back" for tasks
          handleTaskSendBack(item);
        } else {
          handleDiscard(item.id);
        }
      } else if (key === "escape") {
        setSelectedIndex(-1);
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [embedded, editingItem, items, selectedIndex, sendingId, animatingId]);

  const handleTaskApprove = async (item) => {
    setSendingId(item.id);
    try {
      await updateTaskStatus(item.id, "completed");
      setSentFeedback({ id: item.id, sent: true });
      setTimeout(() => {
        setAnimatingId(item.id);
        setTimeout(() => {
          setItems(prev => prev.filter(i => i.id !== item.id));
          setAnimatingId(null);
          setSendingId(null);
          setSentFeedback(null);
          if (onAction) onAction();
        }, 400);
      }, 800);
    } catch (e) {
      console.error(e);
      setSendingId(null);
    }
  };

  const handleTaskSendBack = async (item) => {
    try {
      await updateTaskStatus(item.id, "open");
      setItems(prev => prev.filter(i => i.id !== item.id));
      if (onAction) onAction();
    } catch (e) {
      console.error(e);
    }
  };

  const handleApprove = async (item) => {
    if (!item.to_address) {
      // No recipient — open edit to add one
      setEditingItem(item);
      return;
    }
    setSendingId(item.id);
    try {
      const result = await approveItem(item.id);
      // Show brief sent feedback
      setSentFeedback({ id: item.id, sent: result.sent });
      setTimeout(() => {
        setAnimatingId(item.id);
        setTimeout(() => {
          setItems(prev => prev.filter(i => i.id !== item.id));
          setAnimatingId(null);
          setSendingId(null);
          setSentFeedback(null);
          if (onAction) onAction();
        }, 400);
      }, 800);
    } catch (e) {
      console.error(e);
      setSendingId(null);
    }
  };

  const handleDiscard = async (id) => {
    setAnimatingId(id);
    try {
      await discardItem(id);
      setTimeout(() => {
        setItems(prev => prev.filter(item => item.id !== id));
        setAnimatingId(null);
        if (onAction) onAction();
      }, 400);
    } catch (e) {
      console.error(e);
      setAnimatingId(null);
    }
  };

  const handleDraftSaved = (updatedItem) => {
    setItems(prev => prev.map(i => i.id === updatedItem.id ? updatedItem : i));
    setEditingItem(null);
  };

  if (items.length === 0) {
    return <div className="mc-empty" data-testid="approvals-empty">No pending approvals</div>;
  }

  return (
    <div data-testid="approval-queue">
      {!embedded && (
        <>
          <div className="mc-search-bar" data-testid="approval-search-bar">
            <Search size={13} style={{ color: "var(--mc-ink-4)", flexShrink: 0 }} />
            <input
              type="text"
              placeholder="Search approvals by subject, sender, or content..."
              value={searchQuery}
              onChange={e => handleSearchChange(e.target.value)}
              className="mc-search-input"
              data-testid="approval-search-input"
            />
            {searchQuery && (
              <button
                onClick={() => { setSearchQuery(""); setDebouncedSearch(""); }}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--mc-ink-4)",
                  padding: "2px",
                  display: "flex",
                  alignItems: "center",
                }}
                data-testid="approval-search-clear"
              >
                <X size={13} />
              </button>
            )}
          </div>
          <div className="mc-keyboard-hint" data-testid="keyboard-shortcuts-hint">
            <Keyboard size={12} />
            <span><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
            <span className="mc-hint-sep" />
            <span><kbd>A</kbd> approve</span>
            <span className="mc-hint-sep" />
            <span><kbd>D</kbd> discard</span>
            <span className="mc-hint-sep" />
            <span><kbd>Esc</kbd> deselect</span>
          </div>
        </>
      )}
      {items.map((item, idx) => {
        const brandColor = getBrandColor(item.brand);
        const brandName = getBrandName(item.brand, brands);
        const isSending = sendingId === item.id;
        const feedback = sentFeedback && sentFeedback.id === item.id ? sentFeedback : null;
        const isAnimating = animatingId === item.id;
        const isTaskApproval = item.source === "task" || item.type === "task_approval";

        return (
          <div
            key={item.id}
            ref={el => { itemRefs.current[idx] = el; }}
            className={`mc-approval-item ${isAnimating ? "approving" : ""} ${selectedIndex === idx ? "mc-selected" : ""}`}
            data-testid={`approval-item-${item.id}`}
            onClick={() => setSelectedIndex(idx)}
          >
            <div className="mc-approval-meta">
              <span
                className="mc-brand-pill"
                style={{ background: `${brandColor}14`, color: brandColor }}
                data-testid="approval-brand-pill"
              >
                <span className="mc-brand-dot" style={{ background: brandColor }} />
                {brandName}
              </span>
              <span className="mc-approval-dot" />
              {isTaskApproval ? (
                <>
                  <span style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "3px",
                    fontSize: "10px",
                    fontWeight: 600,
                    color: "var(--mc-accent)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}>
                    <ClipboardList size={10} />
                    Task
                  </span>
                  {item.priority && item.priority !== "normal" && (
                    <>
                      <span className="mc-approval-dot" />
                      <span style={{
                        fontSize: "10px",
                        fontWeight: 600,
                        color: item.priority === "urgent" || item.priority === "high"
                          ? "var(--mc-red, #c0392b)"
                          : "var(--mc-ink-4)",
                        textTransform: "uppercase",
                      }}>
                        <Flag size={9} style={{ display: "inline", marginRight: "2px", verticalAlign: "-1px" }} />
                        {item.priority}
                      </span>
                    </>
                  )}
                </>
              ) : (
                <>
                  <span className="mc-approval-from">{item.agent_name || "Kit"}</span>
                  <span className="mc-approval-dot" />
                  <span className="mc-approval-inbox">{item.inbox}</span>
                </>
              )}
              <span className="mc-approval-dot" />
              <span className="mc-approval-time">{timeAgo(item.created_at)}</span>
              {item.due_date && (
                <>
                  <span className="mc-approval-dot" />
                  <span style={{ fontSize: "10.5px", color: "var(--mc-ink-3)" }}>
                    Due: {new Date(item.due_date).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "America/Denver" })}
                  </span>
                </>
              )}
            </div>

            <div className="mc-approval-subject" data-testid="approval-subject">{item.subject}</div>

            {/* Recipient line (email approvals only) */}
            {!isTaskApproval && item.to_address && (
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "4px",
                fontSize: "11px",
                color: "var(--mc-ink-3)",
                marginBottom: "4px",
              }}>
                <ArrowRight size={10} style={{ color: "var(--mc-ink-4)" }} />
                <span style={{ fontWeight: 400 }}>To:</span>
                <span style={{ fontWeight: 500, color: "var(--mc-ink-2)" }}>{item.to_address}</span>
                <span style={{ marginLeft: "4px" }}>via {item.from_address}</span>
              </div>
            )}

            <div className="mc-approval-preview">
              {item.preview || item.description || item.agent_note || ""}
            </div>

            <div className="mc-approval-actions">
              {feedback ? (
                <span style={{
                  fontSize: "11px",
                  fontWeight: 500,
                  color: feedback.sent ? "var(--mc-green)" : "var(--mc-amber)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }} data-testid={`sent-feedback-${item.id}`}>
                  {feedback.sent ? (
                    <><Check size={13} /> {isTaskApproval ? "Marked complete" : "Sent successfully"}</>
                  ) : (
                    <><Check size={13} /> {isTaskApproval ? "Approved" : "Approved (send queued)"}</>
                  )}
                </span>
              ) : isTaskApproval ? (
                <>
                  <button
                    className="mc-btn mc-btn-approve"
                    onClick={() => handleTaskApprove(item)}
                    disabled={isSending}
                    data-testid={`approve-task-btn-${item.id}`}
                  >
                    <Check size={11} />
                    {isSending ? "Completing..." : "Approve & Complete"}
                  </button>
                  <button
                    className="mc-btn mc-btn-edit"
                    onClick={() => handleTaskSendBack(item)}
                    data-testid={`return-task-btn-${item.id}`}
                  >
                    <ArrowRight size={11} style={{ transform: "rotate(180deg)" }} />
                    Send Back
                  </button>
                </>
              ) : (
                <>
                  <button
                    className="mc-btn mc-btn-approve"
                    onClick={() => handleApprove(item)}
                    disabled={isSending}
                    data-testid={`approve-btn-${item.id}`}
                  >
                    {isSending ? (
                      <>
                        <Send size={11} style={{ animation: "none" }} />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Send size={11} />
                        Approve & Send
                      </>
                    )}
                  </button>
                  <button
                    className="mc-btn mc-btn-edit"
                    onClick={() => setEditingItem(item)}
                    data-testid={`edit-btn-${item.id}`}
                  >
                    <Pencil size={11} />
                    Edit Draft
                  </button>
                  <button
                    className="mc-btn mc-btn-reject"
                    onClick={() => handleDiscard(item.id)}
                    data-testid={`discard-btn-${item.id}`}
                  >
                    Discard
                  </button>
                </>
              )}
            </div>
          </div>
        );
      })}

      {editingItem && (
        <EditDraftDialog
          open={!!editingItem}
          onOpenChange={(open) => { if (!open) setEditingItem(null); }}
          item={editingItem}
          onSaved={handleDraftSaved}
        />
      )}
    </div>
  );
}
