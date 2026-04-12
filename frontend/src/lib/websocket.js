import { useState, useEffect, useRef, useCallback } from "react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const WS_URL = BACKEND_URL
  ? BACKEND_URL.replace(/^https:/, "wss:").replace(/^http:/, "ws:") + "/api/v1/ws"
  : null;

export function useWebSocket(onEvent) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectDelay = useRef(1000);
  const onEventRef = useRef(onEvent);
  const mountedRef = useRef(true);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const connect = useCallback(() => {
    if (!WS_URL || !mountedRef.current) return;
    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setConnected(true);
        reconnectDelay.current = 1000;
        // Request full state sync
        ws.send(JSON.stringify({ type: "sync_state" }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "pong") return;
          if (onEventRef.current) onEventRef.current(msg);
        } catch (e) {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setConnected(false);
        wsRef.current = null;
        // Reconnect with backoff
        const delay = reconnectDelay.current;
        reconnectDelay.current = Math.min(delay * 1.5, 30000);
        setTimeout(() => {
          if (mountedRef.current) connect();
        }, delay);
      };

      ws.onerror = () => {
        // onclose will fire after onerror
      };
    } catch (e) {
      // retry
      setTimeout(() => {
        if (mountedRef.current) connect();
      }, reconnectDelay.current);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    // Keepalive ping every 30s
    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);

    return () => {
      mountedRef.current = false;
      clearInterval(pingInterval);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { connected };
}
