import { useState, useEffect, useRef, useCallback } from "react";
import { marked, Renderer } from "marked";
import DOMPurify from "dompurify";
import hljs from "highlight.js/lib/core";
import javascript from "highlight.js/lib/languages/javascript";
import python from "highlight.js/lib/languages/python";
import bash from "highlight.js/lib/languages/bash";
import json from "highlight.js/lib/languages/json";
import css from "highlight.js/lib/languages/css";
import xml from "highlight.js/lib/languages/xml";
import typescript from "highlight.js/lib/languages/typescript";
import sql from "highlight.js/lib/languages/sql";
import yaml from "highlight.js/lib/languages/yaml";
import markdown from "highlight.js/lib/languages/markdown";
import { gateway, IS_MOCK_MODE } from "@/lib/gateway";
import {
  Send,
  Plus,
  Loader2,
  Cpu,
  Zap,
  MoreHorizontal,
  Pencil,
  Trash2,
  Menu,
  Search,
  ArrowLeft,
  AlertTriangle,
  Wifi,
  WifiOff,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ArrowDownRight,
  ArrowUpRight,
} from "lucide-react";

// ── Register highlight.js languages ──
hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("js", javascript);
hljs.registerLanguage("python", python);
hljs.registerLanguage("py", python);
hljs.registerLanguage("bash", bash);
hljs.registerLanguage("sh", bash);
hljs.registerLanguage("json", json);
hljs.registerLanguage("css", css);
hljs.registerLanguage("html", xml);
hljs.registerLanguage("xml", xml);
hljs.registerLanguage("typescript", typescript);
hljs.registerLanguage("ts", typescript);
hljs.registerLanguage("sql", sql);
hljs.registerLanguage("yaml", yaml);
hljs.registerLanguage("yml", yaml);
hljs.registerLanguage("markdown", markdown);
hljs.registerLanguage("md", markdown);

// ── Configure marked with custom renderer ──
const renderer = new Renderer();

// Links open in new tab
renderer.link = function ({ href, title, tokens }) {
  const text = this.parser.parseInline(tokens);
  let out = `<a href="${href}" target="_blank" rel="noopener noreferrer"`;
  if (title) out += ` title="${title}"`;
  out += `>${text}</a>`;
  return out;
};

// Code blocks with syntax highlighting + copy button
renderer.code = function ({ text, lang }) {
  const language = (lang || "").split(/\s/)[0];
  let highlighted;
  if (language && hljs.getLanguage(language)) {
    highlighted = hljs.highlight(text, { language }).value;
  } else {
    try {
      highlighted = hljs.highlightAuto(text).value;
    } catch {
      highlighted = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
  }
  const langLabel = language || "code";
  const escaped = text.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  return `<div class="mc-code-block" data-testid="code-block"><div class="mc-code-header"><span class="mc-code-lang">${langLabel}</span><button class="mc-code-copy" data-copy-text="${escaped}" title="Copy code">Copy</button></div><pre><code class="hljs">${highlighted}</code></pre></div>`;
};

marked.setOptions({ breaks: true, gfm: true, renderer });

// Allow target attribute through DOMPurify
DOMPurify.addHook("afterSanitizeAttributes", (node) => {
  if (node.tagName === "A") {
    node.setAttribute("target", "_blank");
    node.setAttribute("rel", "noopener noreferrer");
  }
});

function renderMd(text) {
  try {
    return DOMPurify.sanitize(marked.parse(text), {
      ADD_ATTR: ["target", "rel", "data-copy-text", "data-testid"],
    });
  } catch {
    return text;
  }
}

// ── Relative timestamps ──
function relativeTime(iso) {
  if (!iso) return "";
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 10) return "just now";
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function fullTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("en-US", {
    hour: "numeric", minute: "2-digit", second: "2-digit", hour12: true,
    month: "short", day: "numeric", timeZone: "America/Denver",
  });
}

function daysAgoLabel(iso) {
  const d = new Date(iso);
  const now = new Date();
  const diff = Math.floor((now - d) / 86400000);
  if (diff === 0) return "Today";
  if (diff === 1) return "Yesterday";
  if (diff < 7) return "Last 7 days";
  return "Older";
}

function fmtTokens(n) {
  if (n == null) return "0";
  if (n >= 1000) return (n / 1000).toFixed(1) + "k";
  return String(n);
}

// Word count estimate from text
function wordCount(text) {
  return (text || "").split(/\s+/).filter(Boolean).length;
}

// ── Connection State Banner ──
const CONNECTION_STATES = {
  connecting:      { icon: Loader2, spin: true,  label: "Connecting to gateway...",         level: "info" },
  handshaking:     { icon: Loader2, spin: true,  label: "Authenticating...",                level: "info" },
  reconnecting:    { icon: Loader2, spin: true,  label: "Reconnecting...",                  level: "warn" },
  auth_failed:     { icon: AlertTriangle, spin: false, label: "Authentication failed — check REACT_APP_GATEWAY_TOKEN", level: "error" },
  origin_rejected: { icon: AlertTriangle, spin: false, label: "Origin not allowed — add this domain to gateway.controlUi.allowedOrigins", level: "error" },
  unreachable:     { icon: WifiOff, spin: false, label: "Gateway unreachable",              level: "error" },
  error:           { icon: AlertTriangle, spin: false, label: "Connection error",           level: "error" },
  disconnected:    { icon: WifiOff, spin: false, label: "Disconnected",                     level: "warn" },
};

function ConnectionBanner({ state }) {
  if (state === "connected") return null;
  const config = CONNECTION_STATES[state];
  if (!config) return null;
  const Icon = config.icon;
  return (
    <div className={`mc-chat-conn-banner mc-chat-conn-banner--${config.level}`} data-testid="connection-state-banner">
      <Icon size={13} className={config.spin ? "mc-spin" : ""} />
      <span>{config.label}</span>
      {state === "unreachable" && (
        <button className="mc-chat-conn-retry" onClick={() => gateway.connect().catch(() => {})} data-testid="connection-retry-btn">Retry</button>
      )}
    </div>
  );
}

// ── Code Copy Button handler (event delegation) ──
function useCodeCopyHandler(containerRef) {
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const handler = (e) => {
      const btn = e.target.closest(".mc-code-copy");
      if (!btn) return;
      const codeBlock = btn.closest(".mc-code-block");
      const codeEl = codeBlock?.querySelector("code");
      if (!codeEl) return;
      navigator.clipboard.writeText(codeEl.textContent || "").then(() => {
        btn.textContent = "Copied!";
        btn.classList.add("mc-code-copy--done");
        setTimeout(() => { btn.textContent = "Copy"; btn.classList.remove("mc-code-copy--done"); }, 2000);
      });
    };
    container.addEventListener("click", handler);
    return () => container.removeEventListener("click", handler);
  }, [containerRef]);
}

// ── Collapsible Message Body ──
function MessageBody({ html, isLong }) {
  const [expanded, setExpanded] = useState(false);
  if (!isLong) {
    return <div className="mc-chat-msg__body mc-chat-msg__body--md" dangerouslySetInnerHTML={{ __html: html }} />;
  }
  return (
    <div className="mc-chat-msg__body mc-chat-msg__body--md">
      <div className={expanded ? "" : "mc-chat-msg__body--collapsed"} dangerouslySetInnerHTML={{ __html: html }} />
      <button className="mc-chat-show-more" onClick={() => setExpanded((v) => !v)} data-testid="show-more-btn">
        {expanded ? <><ChevronUp size={12} /> Show less</> : <><ChevronDown size={12} /> Show more</>}
      </button>
    </div>
  );
}

// ── Action Buttons ──
function ActionButtons({ actions, onNavigate }) {
  if (!actions || actions.length === 0) return null;
  const handleAction = (action) => {
    if (action.action === "navigate" && onNavigate) {
      onNavigate(action.target);
    } else if (action.action === "open_url") {
      window.open(action.target, "_blank", "noopener");
    }
  };
  return (
    <div className="mc-chat-actions" data-testid="chat-action-buttons">
      {actions.map((a, i) => (
        <button key={i} className="mc-chat-action-btn" onClick={() => handleAction(a)} data-testid={`action-btn-${i}`}>
          {a.action === "open_url" && <ExternalLink size={11} />}
          {a.label}
        </button>
      ))}
    </div>
  );
}

// ── Embedded Entity Card ──
function EmbedCard({ embed }) {
  if (!embed?.preview) return null;
  const p = embed.preview;
  const statusClass = p.status === "pending" ? "mc-embed-status--pending" : p.status === "approved" ? "mc-embed-status--approved" : "mc-embed-status--default";
  return (
    <div className="mc-embed-card" data-testid={`embed-card-${embed.id}`}>
      <div className="mc-embed-card__header">
        <span className="mc-embed-card__title">{p.title}</span>
      </div>
      <div className="mc-embed-card__meta">
        {p.brand && <span>{p.brand}</span>}
        {p.status && <span className={`mc-embed-status ${statusClass}`}>{p.status}</span>}
      </div>
    </div>
  );
}

// ── Session Item with ⋯ menu ──
function SessionItem({ session, isActive, isCurrent, onSelect, onDelete, onRename }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(session.title);
  const menuRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [menuOpen]);

  useEffect(() => {
    if (renaming && inputRef.current) { inputRef.current.focus(); inputRef.current.select(); }
  }, [renaming]);

  const commitRename = () => {
    const trimmed = renameValue.trim();
    if (trimmed && trimmed !== session.title) onRename(session.id, trimmed);
    else setRenameValue(session.title);
    setRenaming(false);
  };

  return (
    <div
      className={`mc-chat-history__item ${isActive ? "mc-chat-history__item--active" : ""}`}
      onClick={() => { if (!renaming) onSelect(session.id); }}
      data-testid={`session-${session.id}`}
    >
      <span className={`mc-chat-history__dot ${isCurrent ? "mc-chat-history__dot--filled" : ""}`} />
      {renaming ? (
        <input ref={inputRef} className="mc-chat-history__rename-input" value={renameValue}
          onChange={(e) => setRenameValue(e.target.value)} onBlur={commitRename}
          onKeyDown={(e) => { if (e.key === "Enter") commitRename(); if (e.key === "Escape") { setRenameValue(session.title); setRenaming(false); } }}
          onClick={(e) => e.stopPropagation()} data-testid={`rename-input-${session.id}`} />
      ) : (
        <span className="mc-chat-history__title">{session.title}</span>
      )}
      {!renaming && (
        <div className="mc-chat-history__actions" ref={menuRef}>
          <button className="mc-chat-history__menu-btn" onClick={(e) => { e.stopPropagation(); setMenuOpen((o) => !o); }} data-testid={`session-menu-${session.id}`}>
            <MoreHorizontal size={12} />
          </button>
          {menuOpen && (
            <div className="mc-chat-history__dropdown" data-testid={`session-dropdown-${session.id}`}>
              <button className="mc-chat-history__dropdown-item" onClick={(e) => { e.stopPropagation(); setMenuOpen(false); setRenameValue(session.title); setRenaming(true); }} data-testid={`rename-session-${session.id}`}>
                <Pencil size={11} /> Rename
              </button>
              <button className="mc-chat-history__dropdown-item mc-chat-history__dropdown-item--danger" onClick={(e) => { e.stopPropagation(); setMenuOpen(false); onDelete(session.id); }} data-testid={`delete-session-${session.id}`}>
                <Trash2 size={11} /> Delete
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// CHAT VIEW
// ══════════════════════════════════════════════════════════════

export default function ChatView() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [viewingSessionId, setViewingSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState(null);
  const [usageMode, setUsageMode] = useState("off");
  const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [connectionState, setConnectionState] = useState("disconnected");
  const [, setTick] = useState(0); // force re-render for relative timestamps

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const messagesContainerRef = useRef(null);

  const isViewingPast = viewingSessionId && viewingSessionId !== currentSessionId;
  const isConnected = connectionState === "connected";

  // Code copy handler (event delegation on messages container)
  useCodeCopyHandler(messagesContainerRef);

  // Tick every 30s to update relative timestamps
  useEffect(() => {
    const timer = setInterval(() => setTick((t) => t + 1), 30000);
    return () => clearInterval(timer);
  }, []);

  // ── Periodic status refresh (every 60s when idle) ──
  useEffect(() => {
    if (!isConnected) return;
    const timer = setInterval(() => {
      gateway.getStatus().then(setStatus).catch(() => {});
    }, 60000);
    return () => clearInterval(timer);
  }, [isConnected]);

  // ── Connect adapter ──
  useEffect(() => {
    const unsub = gateway.onConnectionStateChange(setConnectionState);
    gateway.connect().catch((err) => console.error("[ChatView] Gateway connection failed:", err.message));
    return () => unsub();
  }, []);

  // ── Load sessions once connected ──
  useEffect(() => {
    if (!isConnected) return;
    gateway.listSessions().then((list) => {
      setSessions(list);
      if (list.length > 0) { setCurrentSessionId(list[0].id); setViewingSessionId(list[0].id); }
    }).catch((err) => console.error("[ChatView] Failed to load sessions:", err));
    gateway.getStatus().then(setStatus).catch(() => {});
  }, [isConnected]);

  // ── Load messages when viewed session changes ──
  useEffect(() => {
    if (!viewingSessionId || !isConnected) return;
    gateway.getHistory(viewingSessionId).then(setMessages).catch(() => setMessages([]));
    gateway.getStatus(viewingSessionId).then(setStatus).catch(() => {});
  }, [viewingSessionId, isConnected]);

  // ── Subscribe to chat events ──
  useEffect(() => {
    const unsub = gateway.onChatEvent((event) => {
      if (event.sessionId && event.sessionId !== currentSessionId) return;

      switch (event.type) {
        case "streaming":
          setMessages((prev) => {
            const idx = prev.findIndex((m) => m._runId === event.runId);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = { ...updated[idx], content: event.text };
              return updated;
            }
            return [...prev, { role: event.role || "assistant", content: event.text, timestamp: new Date().toISOString(), _runId: event.runId, _streaming: true }];
          });
          setSending(false);
          break;

        case "complete": {
          const metadata = {};
          if (event.usage) {
            metadata.tokens_in = event.usage.inputTokens;
            metadata.tokens_out = event.usage.outputTokens;
            metadata.cacheRead = event.usage.cacheReadTokens;
            metadata.cacheWrite = event.usage.cacheWriteTokens;
          }
          if (event.durationMs) metadata.duration = event.durationMs / 1000;
          if (event.metadata) Object.assign(metadata, event.metadata);

          setMessages((prev) => {
            const idx = prev.findIndex((m) => m._runId === event.runId);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = { ...updated[idx], content: event.text, metadata, _streaming: false };
              return updated;
            }
            return [...prev, { role: event.role || "assistant", content: event.text, timestamp: new Date().toISOString(), metadata, _runId: event.runId, _streaming: false }];
          });
          setSending(false);

          if (event.usage) {
            setStatus((s) => ({
              ...s,
              tokens_in: (s?.tokens_in || 0) + (event.usage.inputTokens || 0),
              tokens_out: (s?.tokens_out || 0) + (event.usage.outputTokens || 0),
            }));
          }
          if (event.metadata?.usage_mode) setUsageMode(event.metadata.usage_mode);
          if (event.metadata?.context_pct !== undefined) setStatus((s) => ({ ...s, context_pct: event.metadata.context_pct }));
          if (event.metadata?.model) setStatus((s) => ({ ...s, model: event.metadata.model }));
          if (event.metadata?.cost) setStatus((s) => ({ ...s, cost: event.metadata.cost }));
          break;
        }

        case "typing":
          if (event.isTyping !== undefined) setSending(event.isTyping);
          break;
        case "abort":
          setSending(false);
          break;
        case "tool":
          setMessages((prev) => [...prev, { role: "assistant", content: `*Using tool: ${event.toolName}*`, timestamp: new Date().toISOString(), _runId: event.runId }]);
          break;
        case "error":
          setMessages((prev) => [...prev, { role: "assistant", content: `**Error:** ${event.text}`, timestamp: new Date().toISOString(), metadata: { error: true } }]);
          setSending(false);
          break;
        default:
          break;
      }
    });
    return unsub;
  }, [currentSessionId]);

  // ── Auto-scroll ──
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const handleSelectSession = (sid) => { setViewingSessionId(sid); setMobileHistoryOpen(false); };
  const handleBackToCurrent = () => setViewingSessionId(currentSessionId);

  // ── Send message ──
  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || sending || isViewingPast) return;
    const lower = text.toLowerCase();

    if (lower === "/clear") { setMessages([]); setInput(""); return; }

    if (lower === "/new" || lower.startsWith("/new ")) {
      const model = lower === "/new" ? undefined : text.slice(5).trim();
      setInput("");
      try {
        const session = await gateway.createSession(model || undefined);
        setSessions((prev) => [session, ...prev]);
        setCurrentSessionId(session.id); setViewingSessionId(session.id); setMessages([]);
        setStatus((s) => ({ ...s, model: model || s?.model, context_pct: 0, tokens_in: 0, tokens_out: 0, cost: 0 }));
      } catch (e) { console.error("[ChatView] /new failed:", e); }
      return;
    }

    if (lower === "/reset") {
      setInput("");
      try {
        const session = await gateway.createSession();
        setSessions((prev) => [session, ...prev]);
        setCurrentSessionId(session.id); setViewingSessionId(session.id); setMessages([]);
      } catch (e) { console.error("[ChatView] /reset failed:", e); }
      return;
    }

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text, timestamp: new Date().toISOString() }]);
    setSending(true);
    gateway.sendMessage(currentSessionId, text);
    setSessions((prev) => prev.map((s) =>
      s.id === currentSessionId && (s.title === "New chat" || s.title === "Untitled")
        ? { ...s, title: text.length > 40 ? text.slice(0, 40) + "..." : text } : s
    ));
  }, [input, sending, currentSessionId, isViewingPast]);

  const handleKeyDown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } };

  const handleInputChange = (e) => {
    setInput(e.target.value);
    const ta = textareaRef.current;
    if (ta) { ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, 156) + "px"; }
  };

  const handleDeleteSession = async (sid) => {
    await gateway.deleteSession(sid);
    const remaining = sessions.filter((s) => s.id !== sid);
    setSessions(remaining);
    if (remaining.length === 0) {
      const ns = await gateway.createSession();
      setSessions([ns]); setCurrentSessionId(ns.id); setViewingSessionId(ns.id); setMessages([]);
      return;
    }
    if (currentSessionId === sid) setCurrentSessionId(remaining[0].id);
    if (viewingSessionId === sid) setViewingSessionId(currentSessionId === sid ? remaining[0].id : currentSessionId);
  };

  const handleRenameSession = (sid, newTitle) => {
    setSessions((prev) => prev.map((s) => (s.id === sid ? { ...s, title: newTitle } : s)));
    gateway.renameSession(sid, newTitle).catch(() => {});
  };

  const handleNewChat = async () => {
    try {
      const session = await gateway.createSession();
      setSessions((prev) => [session, ...prev]);
      setCurrentSessionId(session.id); setViewingSessionId(session.id); setMessages([]); setMobileHistoryOpen(false);
    } catch (e) { console.error("[ChatView] New chat failed:", e); }
  };

  const filteredSessions = searchQuery.trim()
    ? sessions.filter((s) => s.title.toLowerCase().includes(searchQuery.toLowerCase()))
    : sessions;
  const groupedSessions = {};
  filteredSessions.forEach((s) => {
    const label = daysAgoLabel(s.created_at);
    if (!groupedSessions[label]) groupedSessions[label] = [];
    groupedSessions[label].push(s);
  });

  const ctxPct = status?.context_pct || 0;
  const ctxMax = status?.context_max || 200000;
  const ctxUsed = Math.round(ctxMax * ctxPct / 100);
  const ctxColor = ctxPct < 60 ? "var(--mc-green)" : ctxPct < 80 ? "var(--mc-amber)" : "var(--mc-red)";
  const ctxCritical = ctxPct >= 95;

  return (
    <div className="mc-chat-layout" data-testid="chat-view">
      {/* ── History Sidebar ── */}
      <div className={`mc-chat-history ${mobileHistoryOpen ? "mc-chat-history--open" : ""}`} data-testid="chat-history-sidebar">
        <div className="mc-chat-history__header">
          <span style={{ fontWeight: 600, fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--mc-ink-3)" }}>Chat History</span>
          <button className="mc-btn mc-btn-sm mc-btn-accent" onClick={handleNewChat} disabled={!isConnected} data-testid="new-chat-btn" style={{ gap: "3px", padding: "3px 8px" }}>
            <Plus size={11} /> New
          </button>
        </div>
        <div className="mc-chat-history__search" data-testid="chat-history-search">
          <Search size={12} className="mc-chat-history__search-icon" />
          <input className="mc-chat-history__search-input" placeholder="Search chats..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} data-testid="chat-search-input" />
        </div>
        <div className="mc-chat-history__list">
          {Object.keys(groupedSessions).length === 0 && searchQuery && (
            <div style={{ padding: "16px 14px", fontSize: "11px", color: "var(--mc-ink-4)" }}>No matching chats</div>
          )}
          {Object.entries(groupedSessions).map(([label, items]) => (
            <div key={label}>
              <div className="mc-chat-history__group-label">{label}</div>
              {items.map((s) => (
                <SessionItem key={s.id} session={s} isActive={viewingSessionId === s.id} isCurrent={currentSessionId === s.id}
                  onSelect={handleSelectSession} onDelete={handleDeleteSession} onRename={handleRenameSession} />
              ))}
            </div>
          ))}
        </div>
        <div className="mc-chat-history__footer" data-testid="gateway-mode-indicator">
          <Wifi size={10} /><span>{IS_MOCK_MODE ? "Mock" : "Live"}</span>
          {isConnected && <span className="mc-chat-history__connected-dot" />}
        </div>
      </div>

      {mobileHistoryOpen && <div className="mc-chat-history__overlay" onClick={() => setMobileHistoryOpen(false)} />}

      {/* ── Main Chat Area ── */}
      <div className="mc-chat-main">
        <div className="mc-chat-mobile-bar">
          <button onClick={() => setMobileHistoryOpen(true)} data-testid="chat-history-toggle" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--mc-ink-3)", padding: "4px" }}>
            <Menu size={16} />
          </button>
          <span style={{ fontSize: "12px", fontWeight: 500, color: "var(--mc-ink-2)" }}>
            {sessions.find((s) => s.id === viewingSessionId)?.title || "Chat"}
          </span>
        </div>

        {!IS_MOCK_MODE && <ConnectionBanner state={connectionState} />}

        {isViewingPast && (
          <div className="mc-chat-back-banner" data-testid="back-to-current-banner">
            <span style={{ fontSize: "12px", color: "var(--mc-ink-2)" }}>Viewing past session</span>
            <button className="mc-chat-back-btn" onClick={handleBackToCurrent} data-testid="back-to-current-btn">
              <ArrowLeft size={12} /> Back to current
            </button>
          </div>
        )}

        {/* Messages */}
        <div className="mc-chat-messages" ref={messagesContainerRef} data-testid="chat-messages">
          {messages.length === 0 && !sending && (
            <div className="mc-chat-empty">
              <div style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: "20px", fontWeight: 500, marginBottom: "6px", color: "var(--mc-ink)" }}>
                {isViewingPast ? "Empty Session" : "Chat with Kit"}
              </div>
              {!isViewingPast && (
                <div style={{ fontSize: "12.5px", color: "var(--mc-ink-3)", fontWeight: 300, lineHeight: 1.6, maxWidth: "400px" }}>
                  Ask Kit anything — draft emails, review code, run research, manage tasks.
                  Use <code>/status</code> to check session info or <code>/new</code> to start fresh.
                </div>
              )}
            </div>
          )}

          {messages.map((msg, i) => {
            const isSystem = msg.role === "system";
            const isUser = msg.role === "user";
            const isAssistant = msg.role === "assistant" || msg.role === "tool";
            const html = !isUser ? renderMd(msg.content) : "";
            const isLongMsg = isAssistant && wordCount(msg.content) > 500;

            return (
              <div key={i} className={`mc-chat-msg mc-chat-msg--${msg.role}`} data-testid={`chat-msg-${i}`}>
                {/* System messages */}
                {isSystem && (
                  <div className="mc-chat-msg__system" dangerouslySetInnerHTML={{ __html: renderMd(msg.content) }} />
                )}

                {/* User / Assistant messages */}
                {!isSystem && (
                  <>
                    <div className="mc-chat-msg__sender">
                      {isUser ? "You" : "Kit"}
                      <span className="mc-chat-msg__time" title={fullTime(msg.timestamp)} data-testid={`msg-time-${i}`}>
                        {relativeTime(msg.timestamp)}
                      </span>
                      {msg._streaming && <span className="mc-chat-msg__streaming-badge">streaming</span>}
                    </div>

                    {isUser ? (
                      <div className="mc-chat-msg__body">{msg.content}</div>
                    ) : isLongMsg ? (
                      <MessageBody html={html} isLong={true} />
                    ) : (
                      <div className="mc-chat-msg__body mc-chat-msg__body--md" dangerouslySetInnerHTML={{ __html: html }} />
                    )}

                    {/* Action buttons */}
                    {isAssistant && msg.metadata?.actions && (
                      <ActionButtons actions={msg.metadata.actions} />
                    )}

                    {/* Embedded entity cards */}
                    {isAssistant && msg.metadata?.embeds && (
                      <div className="mc-chat-embeds">
                        {msg.metadata.embeds.map((embed, j) => <EmbedCard key={j} embed={embed} />)}
                      </div>
                    )}

                    {/* Usage footer */}
                    {isAssistant && msg.metadata && usageMode !== "off" && !msg._streaming && (
                      <div className="mc-chat-msg__usage" data-testid={`chat-usage-${i}`}>
                        {msg.metadata.tokens_in != null && (
                          <span
                            title={msg.metadata.cacheRead ? `${fmtTokens(msg.metadata.cacheRead)} cached` : undefined}
                          >
                            {msg.metadata.tokens_in.toLocaleString()} in / {(msg.metadata.tokens_out || 0).toLocaleString()} out
                          </span>
                        )}
                        {usageMode === "full" && msg.metadata.cost !== undefined && <span>${msg.metadata.cost.toFixed(4)}</span>}
                        {msg.metadata.duration != null && <span>{msg.metadata.duration.toFixed(1)}s</span>}
                        {msg.metadata.toolCalls && <span>Tools: {msg.metadata.toolCalls.join(", ")}</span>}
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}

          {sending && (
            <div className="mc-chat-msg mc-chat-msg--assistant" data-testid="chat-typing-indicator">
              <div className="mc-chat-msg__sender">Kit</div>
              <div className="mc-chat-typing"><span /><span /><span /></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* ── Status Bar ── */}
        <div className={`mc-chat-status ${ctxCritical ? "mc-chat-status--critical" : ""}`} data-testid="chat-status-bar">
          <div className="mc-chat-status__item" data-testid="status-model">
            <Cpu size={11} />
            <span>{(status?.model || "—").replace(/^[^/]+\//, "")}</span>
          </div>
          <div className="mc-chat-status__item" data-testid="status-context">
            <div className={`mc-chat-status__ctx-bar ${ctxCritical ? "mc-chat-status__ctx-bar--pulse" : ""}`}>
              <div className="mc-chat-status__ctx-fill" style={{ width: `${ctxPct}%`, background: ctxColor }} />
            </div>
            <span style={{ color: ctxColor }}>
              {ctxPct}% ctx
              <span className="mc-chat-status__ctx-detail"> ({fmtTokens(ctxUsed)}/{fmtTokens(ctxMax)})</span>
            </span>
            {ctxCritical && <AlertTriangle size={10} style={{ color: "var(--mc-red)" }} />}
          </div>
          <div
            className="mc-chat-status__item"
            data-testid="status-tokens"
            title={[
              status?.cacheRead ? `Cache: ${fmtTokens(status.cacheRead)} read` : null,
              status?.last_duration ? `Last response: ${status.last_duration.toFixed(1)}s` : null,
            ].filter(Boolean).join(" · ") || undefined}
          >
            <ArrowDownRight size={10} />
            <span>{fmtTokens(status?.tokens_in)}</span>
            <ArrowUpRight size={10} />
            <span>{fmtTokens(status?.tokens_out)}</span>
          </div>
          {status?.cost > 0 && (
            <div className="mc-chat-status__item" data-testid="status-cost">
              <span>${status.cost.toFixed(2)} session</span>
            </div>
          )}
          {ctxCritical && (
            <div className="mc-chat-status__item mc-chat-status__compact-hint" data-testid="compact-hint">
              <span>Try /compact</span>
            </div>
          )}
        </div>

        {/* Input */}
        {!isViewingPast && (
          <div className="mc-chat-input-wrap" data-testid="chat-input-wrap">
            <textarea ref={textareaRef} className="mc-chat-input" value={input} onChange={handleInputChange} onKeyDown={handleKeyDown}
              placeholder={isConnected ? "Ask Kit anything..." : "Waiting for gateway connection..."} rows={1} disabled={sending || !isConnected} data-testid="chat-input" />
            <button className="mc-chat-send-btn" onClick={handleSend} disabled={!input.trim() || sending || !isConnected} data-testid="chat-send-btn">
              {sending ? <Loader2 size={15} className="mc-spin" /> : <Send size={15} />}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
