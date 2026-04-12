// ── Types ──

export interface WsEvent {
  type: string;
  data: unknown;
  ts: number;
}

export type WsHandler = (event: WsEvent) => void;

// ── Module state ──

let ws: WebSocket | null = null;
const subscriptions = new Map<string, Set<WsHandler>>();
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let reconnectDelay = 2000;
let pingInterval: ReturnType<typeof setInterval> | null = null;
let isConnected = false;

const MAX_RECONNECT_DELAY = 30000;
const PING_INTERVAL_MS = 30000;

// ── Internal helpers ──

function getWsUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws`;
}

function handleMessage(event: MessageEvent) {
  try {
    const parsed: WsEvent = JSON.parse(event.data);
    const handlers = subscriptions.get(parsed.type);
    if (handlers) {
      for (const handler of handlers) {
        try {
          handler(parsed);
        } catch (err) {
          console.error(`[ws] handler error for ${parsed.type}:`, err);
        }
      }
    }

    // Wildcard handlers
    const wildcardHandlers = subscriptions.get('*');
    if (wildcardHandlers) {
      for (const handler of wildcardHandlers) {
        try {
          handler(parsed);
        } catch (err) {
          console.error('[ws] wildcard handler error:', err);
        }
      }
    }
  } catch (err) {
    console.error('[ws] failed to parse message:', err);
  }
}

function startPing() {
  stopPing();
  pingInterval = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
    }
  }, PING_INTERVAL_MS);
}

function stopPing() {
  if (pingInterval) {
    clearInterval(pingInterval);
    pingInterval = null;
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, reconnectDelay);
  reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);
}

// ── Public API ──

export function subscribe(eventType: string, handler: WsHandler): () => void {
  if (!subscriptions.has(eventType)) {
    subscriptions.set(eventType, new Set());
  }
  subscriptions.get(eventType)!.add(handler);

  return () => {
    subscriptions.get(eventType)?.delete(handler);
    if (subscriptions.get(eventType)?.size === 0) {
      subscriptions.delete(eventType);
    }
  };
}

export function connect() {
  // Don't reconnect if already open or connecting
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  // Clear any pending reconnect
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  try {
    ws = new WebSocket(getWsUrl());

    ws.onopen = () => {
      isConnected = true;
      reconnectDelay = 2000; // Reset backoff
      startPing();
      console.log('[ws] connected');
    };

    ws.onmessage = handleMessage;

    ws.onclose = () => {
      isConnected = false;
      stopPing();
      ws = null;
      console.log('[ws] disconnected, reconnecting...');
      scheduleReconnect();
    };

    ws.onerror = (err) => {
      console.error('[ws] error:', err);
    };
  } catch (err) {
    console.error('[ws] connection error:', err);
    scheduleReconnect();
  }
}

export function disconnect() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  stopPing();
  if (ws) {
    ws.close();
    ws = null;
  }
  isConnected = false;
}

export function getConnected(): boolean {
  return isConnected;
}

// Auto-connect on module load
connect();
