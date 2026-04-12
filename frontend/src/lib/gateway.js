/**
 * Gateway Adapter — abstracts communication with the OpenClaw gateway.
 *
 * Config (all via .env):
 *   REACT_APP_USE_MOCK_GATEWAY  — "true" uses MockGatewayAdapter, "false" uses RealGatewayAdapter
 *   REACT_APP_GATEWAY_URL       — WebSocket URL (default: ws://127.0.0.1:18888)
 *   REACT_APP_GATEWAY_TOKEN     — Bearer token for auth (required in real mode)
 *   REACT_APP_GATEWAY_DEBUG     — "true" enables verbose console logging of WS frames
 */

const USE_MOCK = process.env.REACT_APP_USE_MOCK_GATEWAY !== "false";
const GATEWAY_URL = process.env.REACT_APP_GATEWAY_URL || "ws://127.0.0.1:18888";
const GATEWAY_TOKEN = process.env.REACT_APP_GATEWAY_TOKEN || "";
const DEBUG = process.env.REACT_APP_GATEWAY_DEBUG === "true";

// ── Connection states ──────────────────────────────────────
// 'disconnected' | 'connecting' | 'handshaking' | 'connected'
// | 'reconnecting' | 'auth_failed' | 'origin_rejected' | 'unreachable' | 'error'

// ── Base class with event emitter ──────────────────────────
class AdapterBase {
  constructor() {
    this._chatListeners = new Set();
    this._stateListeners = new Set();
    this._state = "disconnected";
  }

  getConnectionState() {
    return this._state;
  }

  _setState(state) {
    if (this._state === state) return;
    this._state = state;
    this._stateListeners.forEach((cb) => {
      try { cb(state); } catch (e) { console.error("[Gateway] State listener error:", e); }
    });
  }

  onConnectionStateChange(cb) {
    this._stateListeners.add(cb);
    cb(this._state); // fire immediately with current state
    return () => this._stateListeners.delete(cb);
  }

  onChatEvent(cb) {
    this._chatListeners.add(cb);
    return () => this._chatListeners.delete(cb);
  }

  _emitChat(event) {
    this._chatListeners.forEach((cb) => {
      try { cb(event); } catch (e) { console.error("[Gateway] Chat listener error:", e); }
    });
  }

  // Subclasses implement these
  async connect() {}
  disconnect() {}
  sendMessage(_sessionId, _text) {}
  async listSessions() { return []; }
  async getHistory(_sessionId) { return []; }
  async getStatus(_sessionId) { return {}; }
  async createSession(_model) { return {}; }
  async deleteSession(_sessionId) {}
  async renameSession(_sessionId, _title) {}
}

// ══════════════════════════════════════════════════════════════
// MOCK ADAPTER
// ══════════════════════════════════════════════════════════════

let mockSessions = [
  { id: "session_001", title: "Current chat", created_at: new Date().toISOString(), model: "claude-opus-4-6", messages: [] },
];
let mockIdCounter = 2;

const MOCK_RESPONSES = {
  "/status": () => ({
    reply: "**Kit Status**\n\n| Field | Value |\n|---|---|\n| Model | `claude-opus-4-6` |\n| Context | 42% of 200k |\n| Session tokens | 12,400 in / 2,100 out |\n| Session cost | $0.23 |\n| Uptime | 4h 12m |",
    metadata: { model: "claude-opus-4-6", context_pct: 42, tokens_in: 12400, tokens_out: 2100, cost: 0.23 },
  }),
  "/usage tokens": () => ({
    reply: "Token usage footer **enabled** on all responses.",
    metadata: { usage_mode: "tokens" },
  }),
  "/usage full": () => ({
    reply: "Full usage footer (tokens + cost) **enabled**.",
    metadata: { usage_mode: "full" },
  }),
  "/usage off": () => ({
    reply: "Usage footer **disabled**.",
    metadata: { usage_mode: "off" },
  }),
  "/compact": () => ({
    reply: "Session compacted. Summarized 47 messages into context. Context usage dropped from 78% → 31%.",
    metadata: { context_pct: 31 },
  }),
  "/context list": () => ({
    reply: "**System prompt contents:**\n\n1. Base Kit personality & role\n2. Brand context: Agentic Trust\n3. Tool definitions (12 tools)\n4. Session history summary (compacted)\n5. User preferences",
    metadata: {},
  }),
};

function mockDelay(ms = 800) {
  return new Promise((r) => setTimeout(r, ms + Math.random() * 600));
}

function generateMockReply(text) {
  const lower = text.toLowerCase().trim();
  for (const [cmd, fn] of Object.entries(MOCK_RESPONSES)) {
    if (lower === cmd || lower.startsWith(cmd + " ")) return fn();
  }
  if (lower.includes("hello") || lower.includes("hi ") || lower === "hi") {
    return {
      reply: "Hey! I'm **Kit**, your OpenClaw agent. How can I help today?\n\nI can help with:\n- Drafting emails and content\n- Research and analysis\n- Task management\n- Code review\n- Anything else you need",
      metadata: { tokens_in: 45, tokens_out: 62 },
    };
  }
  if (lower.includes("draft") || lower.includes("email")) {
    return {
      reply: "Here's a draft:\n\n---\n\n**Subject:** Re: Follow-up on Q2 Planning\n\nHi team,\n\nThank you for the detailed Q2 plan. A few thoughts:\n\n1. The timeline for Phase 2 looks tight — can we add a buffer week?\n2. Budget allocation for marketing looks good\n3. I'd recommend adding a checkpoint review at the midpoint\n\nLet me know if you'd like me to refine any section.\n\nBest,\nJeff\n\n---\n\nWant me to adjust anything?",
      metadata: { tokens_in: 120, tokens_out: 180, duration: 2.3 },
    };
  }
  if (lower.includes("code") || lower.includes("function") || lower.includes("bug")) {
    return {
      reply: "Here's what I found:\n\n```javascript\nconst handleSubmit = async (data) => {\n  try {\n    const result = await api.post('/tasks', data);\n    refreshTasks();\n    return result;\n  } catch (err) {\n    console.error('Submit failed:', err);\n    throw err;\n  }\n};\n```\n\nThe fix is adding the `refreshTasks()` call after the successful POST. Want me to look at anything else?",
      metadata: { tokens_in: 85, tokens_out: 145, toolCalls: ["code_search", "file_read"] },
    };
  }
  return {
    reply: `Got it. I'll work on that.\n\nHere's my understanding of what you need:\n\n> ${text}\n\nI'm processing this now. In a real session, I'd be querying tools, searching code, and drafting a full response. Let me know if you want to adjust the direction.`,
    metadata: { tokens_in: text.split(" ").length * 2, tokens_out: 65, duration: 1.1 },
  };
}

export class MockGatewayAdapter extends AdapterBase {
  async connect() {
    this._setState("connected");
  }

  disconnect() {
    this._setState("disconnected");
  }

  sendMessage(sessionId, text) {
    const runId = `mock-run-${Date.now()}`;

    // Emit events asynchronously (simulates streaming)
    mockDelay().then(() => {
      const { reply, metadata } = generateMockReply(text);

      // Store in mock session
      const session = mockSessions.find((s) => s.id === sessionId);
      if (session) {
        session.messages.push(
          { role: "user", content: text, timestamp: new Date().toISOString() },
          { role: "assistant", content: reply, timestamp: new Date().toISOString(), metadata }
        );
        if (session.messages.filter((m) => m.role === "user").length === 1) {
          session.title = text.length > 40 ? text.slice(0, 40) + "..." : text;
        }
      }

      this._emitChat({
        type: "complete",
        sessionId,
        role: "assistant",
        text: reply,
        runId,
        metadata,
      });
    });
  }

  async listSessions() {
    return mockSessions.map(({ id, title, created_at, model }) => ({ id, title, created_at, model }));
  }

  async getHistory(sessionId) {
    const session = mockSessions.find((s) => s.id === sessionId);
    return session ? session.messages : [];
  }

  async getStatus(sessionId) {
    return { model: "claude-opus-4-6", context_pct: 42, context_max: 200000, tokens_in: 12400, tokens_out: 2100, cost: 0.23 };
  }

  async createSession(model) {
    const session = {
      id: `session_${String(mockIdCounter++).padStart(3, "0")}`,
      title: "New chat",
      created_at: new Date().toISOString(),
      model: model || "claude-opus-4-6",
      messages: [],
    };
    mockSessions.unshift(session);
    return { id: session.id, title: session.title, created_at: session.created_at, model: session.model };
  }

  async deleteSession(sessionId) {
    mockSessions = mockSessions.filter((s) => s.id !== sessionId);
  }

  async renameSession(sessionId, newTitle) {
    const session = mockSessions.find((s) => s.id === sessionId);
    if (session) session.title = newTitle;
  }
}

// ══════════════════════════════════════════════════════════════
// REAL GATEWAY ADAPTER (WebSocket)
// ══════════════════════════════════════════════════════════════

export class RealGatewayAdapter extends AdapterBase {
  constructor(url, token) {
    super();
    // Normalize URL to ws://
    this.wsUrl = url.replace(/^http:/, "ws:").replace(/^https:/, "wss:");
    this.token = token;
    this.ws = null;
    this.pendingRequests = new Map(); // id → { resolve, reject, timeout }
    this.reqCounter = 0;
    this.reconnectTimer = null;
    this.reconnectAttempt = 0;
    this.maxReconnectAttempts = 10;
    this.deviceToken = null;
    this.sessionKey = "openclaw-control-ui";
    this._wasConnected = false; // track if we ever connected successfully
    // Local session overrides (rename/delete are local-only)
    this._localSessionOverrides = new Map(); // sessionKey → { title?, hidden? }
  }

  // ── Debug logging ──

  _log(...args) {
    if (DEBUG) console.log("%c[Gateway]", "color:#c85a2a;font-weight:bold", ...args);
  }

  _logWarn(...args) {
    if (DEBUG) console.warn("%c[Gateway]", "color:#b06a10;font-weight:bold", ...args);
  }

  _logError(...args) {
    console.error("%c[Gateway]", "color:#c0392b;font-weight:bold", ...args);
  }

  _logFrame(direction, data) {
    if (!DEBUG) return;
    const arrow = direction === "send" ? "→" : "←";
    const color = direction === "send" ? "color:#2d6a4f" : "color:#2a5c8a";
    console.groupCollapsed(`%c${arrow} ${data.type || "frame"} ${data.method || data.event || data.id || ""}`, color);
    console.log(JSON.parse(JSON.stringify(data)));
    console.groupEnd();
  }

  // ── Request ID generator ──

  _nextId() {
    return `mc-${++this.reqCounter}-${Date.now().toString(36)}`;
  }

  // ── Raw WebSocket send ──

  _sendRaw(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this._logFrame("send", data);
      this.ws.send(JSON.stringify(data));
    } else {
      this._logError("Cannot send — WebSocket not open. State:", this.ws?.readyState);
    }
  }

  // ── Request/response with correlation ──

  _request(method, params = {}, timeoutMs = 30000) {
    return new Promise((resolve, reject) => {
      if (this._state !== "connected" && this._state !== "handshaking") {
        reject(new Error(`Cannot send request — state: ${this._state}`));
        return;
      }

      const id = this._nextId();
      const timer = setTimeout(() => {
        this.pendingRequests.delete(id);
        reject(new Error(`Request "${method}" timed out after ${timeoutMs}ms`));
      }, timeoutMs);

      this.pendingRequests.set(id, {
        resolve: (payload) => { clearTimeout(timer); resolve(payload); },
        reject: (err) => { clearTimeout(timer); reject(err); },
      });

      this._sendRaw({ type: "req", id, method, params });
    });
  }

  // ── Connect to gateway ──

  async connect() {
    if (this._state === "connected") return;
    if (this._state === "connecting" || this._state === "handshaking") return;

    this._setState("connecting");
    this._log("Connecting to", this.wsUrl);

    return new Promise((resolve, reject) => {
      let connectTimer;
      try {
        this.ws = new WebSocket(this.wsUrl);
      } catch (err) {
        this._logError("WebSocket constructor failed:", err.message);
        this._setState("unreachable");
        reject(new Error(`Cannot create WebSocket: ${err.message}`));
        return;
      }

      connectTimer = setTimeout(() => {
        this._logError("Connection timed out after 10s");
        this._setState("unreachable");
        if (this.ws) this.ws.close();
        reject(new Error("Connection timed out — gateway unreachable at " + this.wsUrl));
      }, 10000);

      this.ws.onopen = () => {
        this._log("TCP connected, sending handshake");
        this._setState("handshaking");

        const handshakeId = this._nextId();
        this.pendingRequests.set(handshakeId, {
          resolve: (payload) => {
            clearTimeout(connectTimer);
            if (payload.type === "hello-ok") {
              this.deviceToken = payload.auth?.deviceToken;
              this._setState("connected");
              this._wasConnected = true;
              this.reconnectAttempt = 0;
              this._log("Authenticated. Role:", payload.auth?.role, "Scopes:", payload.auth?.scopes);
              resolve();
            } else {
              this._logError("Unexpected handshake response:", payload);
              this._setState("error");
              reject(new Error("Unexpected handshake response: " + JSON.stringify(payload)));
            }
          },
          reject: (err) => {
            clearTimeout(connectTimer);
            reject(err);
          },
        });

        this._sendRaw({
          type: "req",
          id: handshakeId,
          method: "connect",
          params: {
            minProtocol: 3,
            maxProtocol: 3,
            client: {
              id: "openclaw-control-ui",
              version: "1.0.0",
              platform: "web",
              mode: "operator",
            },
            role: "operator",
            scopes: ["operator.read", "operator.write"],
            caps: [],
            commands: [],
            permissions: {},
            auth: { token: this.token },
            locale: "en-US",
            userAgent: "mission-control-ui/1.0.0",
            device: {
              id: "mission-control-device-" + Math.random().toString(36).slice(2, 10),
              publicKey: "",
              signature: "",
              signedAt: Date.now(),
              nonce: Math.random().toString(36).slice(2),
            },
          },
        });
      };

      this.ws.onmessage = (msgEvent) => {
        try {
          const data = JSON.parse(msgEvent.data);
          this._logFrame("recv", data);
          this._handleMessage(data);
        } catch (err) {
          this._logError("Failed to parse WS message:", err, msgEvent.data);
        }
      };

      this.ws.onerror = (err) => {
        this._logError("WebSocket error event");
        if (this._state === "connecting" || this._state === "handshaking") {
          clearTimeout(connectTimer);
          this._setState("unreachable");
          reject(new Error("WebSocket connection failed — is the gateway running at " + this.wsUrl + "?"));
        }
      };

      this.ws.onclose = (event) => {
        this._log("WebSocket closed. Code:", event.code, "Reason:", event.reason || "(none)", "Clean:", event.wasClean);
        clearTimeout(connectTimer);

        // Classify close reason
        if (event.code === 4001 || event.reason?.toLowerCase().includes("auth")) {
          this._setState("auth_failed");
          this._logError("AUTH FAILED — Check REACT_APP_GATEWAY_TOKEN. Token length:", this.token.length);
          // Reject pending handshake if applicable
          this.pendingRequests.forEach((p) => p.reject(new Error("Authentication failed")));
          this.pendingRequests.clear();
          reject(new Error("Authentication failed — invalid or missing gateway token"));
          return;
        }
        if (event.code === 4003 || event.reason?.toLowerCase().includes("origin")) {
          this._setState("origin_rejected");
          this._logError("ORIGIN REJECTED — Add this origin to gateway.controlUi.allowedOrigins in ~/.openclaw/openclaw.json");
          this.pendingRequests.forEach((p) => p.reject(new Error("Origin rejected")));
          this.pendingRequests.clear();
          reject(new Error("Origin not allowed — configure gateway.controlUi.allowedOrigins"));
          return;
        }

        this._handleDisconnect();
      };
    });
  }

  // ── Message handling ──

  _handleMessage(data) {
    if (data.type === "res") {
      const pending = this.pendingRequests.get(data.id);
      if (pending) {
        this.pendingRequests.delete(data.id);
        if (data.ok) {
          pending.resolve(data.payload);
        } else {
          const code = data.error?.details?.code || data.error?.code || "";
          const reason = data.error?.details?.reason || data.error?.message || "Request failed";
          this._logError(`Request ${data.id} failed: [${code}] ${reason}`);

          if (code === "auth_failed" || code === "unauthorized" || code === "invalid_token") {
            this._setState("auth_failed");
          } else if (code === "origin_rejected" || code === "forbidden_origin") {
            this._setState("origin_rejected");
          }

          pending.reject(new Error(`[${code}] ${reason}`));
        }
      } else {
        this._logWarn("Response for unknown request ID:", data.id);
      }
    } else if (data.type === "event") {
      this._handleEvent(data);
    }
  }

  _handleEvent(data) {
    const { event, payload } = data;

    switch (event) {
      case "chat": {
        const chatEvent = {
          type: payload.status === "streaming" ? "streaming" : payload.status === "complete" ? "complete" : "message",
          sessionId: payload.sessionKey,
          role: payload.role,
          text: payload.text || "",
          runId: payload.runId,
        };

        if (payload.role === "tool") {
          chatEvent.type = "tool";
          chatEvent.toolName = payload.toolName;
          chatEvent.toolOutput = payload.toolOutput;
        }

        if (payload.status === "complete" && payload.usage) {
          chatEvent.usage = {
            inputTokens: payload.usage.inputTokens || 0,
            outputTokens: payload.usage.outputTokens || 0,
            cacheReadTokens: payload.usage.cacheReadTokens || 0,
            cacheWriteTokens: payload.usage.cacheWriteTokens || 0,
          };
        }

        if (payload.durationMs) {
          chatEvent.durationMs = payload.durationMs;
        }

        this._emitChat(chatEvent);
        break;
      }

      case "chat.typing":
        this._emitChat({
          type: "typing",
          sessionId: payload.sessionKey,
          isTyping: payload.isTyping,
        });
        break;

      case "chat.abort":
        this._emitChat({
          type: "abort",
          sessionId: payload.sessionKey,
          runId: payload.runId,
        });
        break;

      default:
        this._log("Unhandled event:", event, payload);
    }
  }

  // ── Disconnection & reconnect ──

  _handleDisconnect() {
    // Don't reconnect on terminal states or if we never connected
    if (this._state === "auth_failed" || this._state === "origin_rejected"
      || this._state === "disconnected" || this._state === "unreachable") {
      return;
    }

    // Reject all pending requests
    this.pendingRequests.forEach((p) => p.reject(new Error("Connection lost")));
    this.pendingRequests.clear();

    // Only auto-reconnect if we previously had a successful connection
    if (!this._wasConnected) {
      this._setState("unreachable");
      return;
    }

    this._setState("reconnecting");
    this._scheduleReconnect();
  }

  _scheduleReconnect() {
    if (this.reconnectAttempt >= this.maxReconnectAttempts) {
      this._logError(`Max reconnect attempts (${this.maxReconnectAttempts}) reached`);
      this._setState("unreachable");
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempt), 30000);
    this.reconnectAttempt++;
    this._log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempt}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((err) => {
        this._logError("Reconnect failed:", err.message);
      });
    }, delay);
  }

  disconnect() {
    this._log("Disconnecting");
    clearTimeout(this.reconnectTimer);
    this.pendingRequests.forEach((p) => p.reject(new Error("Disconnected")));
    this.pendingRequests.clear();
    this._setState("disconnected");
    if (this.ws) {
      this.ws.onclose = null; // prevent reconnect trigger
      this.ws.close();
      this.ws = null;
    }
  }

  // ── Chat ──

  sendMessage(sessionId, text) {
    if (this._state !== "connected") {
      this._emitChat({ type: "error", sessionId, text: `Cannot send — gateway ${this._state}` });
      return;
    }

    const idempotencyKey = `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

    this._request("chat.send", {
      sessionKey: sessionId || this.sessionKey,
      message: text,
      idempotencyKey,
    }).then((payload) => {
      this._log("Message ack. runId:", payload.runId, "status:", payload.status);
    }).catch((err) => {
      this._logError("chat.send failed:", err.message);
      this._emitChat({ type: "error", sessionId: sessionId || this.sessionKey, text: err.message });
    });
  }

  // ── Sessions ──

  async listSessions(limit = 50) {
    if (this._state !== "connected") throw new Error("Not connected");

    const payload = await this._request("sessions.list", {
      agentId: "main",
      limit,
      messageLimit: 10,
    });

    return (payload.sessions || [])
      .filter((s) => !this._localSessionOverrides.get(s.sessionKey)?.hidden)
      .map((s) => {
        const overrides = this._localSessionOverrides.get(s.sessionKey) || {};
        return {
          id: s.sessionKey,
          title: overrides.title || s.label || "Untitled",
          created_at: new Date(s.created).toISOString(),
          model: s.model,
          lastActive: s.lastActive ? new Date(s.lastActive).toISOString() : undefined,
        };
      });
  }

  async getHistory(sessionId, limit = 100) {
    if (this._state !== "connected") throw new Error("Not connected");

    const payload = await this._request("chat.history", {
      sessionKey: sessionId,
      limit,
    });

    return (payload.messages || []).map((m) => ({
      role: m.role,
      content: m.text,
      timestamp: new Date(m.timestamp).toISOString(),
    }));
  }

  async getStatus() {
    if (this._state !== "connected") throw new Error("Not connected");

    const payload = await this._request("status", {});
    const agent = payload.agents?.[0];
    return {
      model: agent?.defaultModel || "unknown",
      sessions: agent?.sessions || 0,
      gateway_version: payload.gateway?.version,
      uptime: payload.gateway?.uptime,
    };
  }

  // createSession sends /new to the gateway, then refreshes the session list
  async createSession(model) {
    if (this._state !== "connected") throw new Error("Not connected");

    const text = model ? `/new ${model}` : "/new";
    await this._request("chat.send", {
      sessionKey: this.sessionKey,
      message: text,
      idempotencyKey: `new-${Date.now()}`,
    });

    // Give the gateway a moment to process the session reset
    await new Promise((r) => setTimeout(r, 600));

    // Refresh session list and return the most recent
    const sessions = await this.listSessions();
    return sessions[0] || { id: this.sessionKey, title: "New chat", created_at: new Date().toISOString() };
  }

  // Local-only: hide from session list
  async deleteSession(sessionId) {
    this._localSessionOverrides.set(sessionId, {
      ...this._localSessionOverrides.get(sessionId),
      hidden: true,
    });
  }

  // Local-only: override display title
  async renameSession(sessionId, newTitle) {
    this._localSessionOverrides.set(sessionId, {
      ...this._localSessionOverrides.get(sessionId),
      title: newTitle,
    });
  }
}

// ══════════════════════════════════════════════════════════════
// EXPORT — determined by REACT_APP_USE_MOCK_GATEWAY
// ══════════════════════════════════════════════════════════════

export const IS_MOCK_MODE = USE_MOCK;

export const gateway = USE_MOCK
  ? new MockGatewayAdapter()
  : new RealGatewayAdapter(GATEWAY_URL, GATEWAY_TOKEN);
