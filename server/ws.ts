import type { ServerWebSocket } from "bun";

// Connected clients set (Bun native WebSocket)
const clients = new Set<ServerWebSocket>();

// Broadcast a JSON event to all connected clients
export function wsEmit(event: string, data: unknown): void {
  try {
    const msg = JSON.stringify({ type: event, data, ts: Date.now() });
    for (const client of clients) {
      try {
        client.send(msg);
      } catch {
        // Client may have disconnected between iteration and send
      }
    }
  } catch {
    // Swallow all errors — wsEmit must never throw
  }
}

// Bun native WebSocket handlers (used by Bun.serve())
export const wsHandlers = {
  open(ws: ServerWebSocket) {
    clients.add(ws);
    try {
      ws.send(JSON.stringify({ type: "connected", data: { ts: Date.now() } }));
    } catch {}
  },

  message(ws: ServerWebSocket, message: string | Buffer) {
    try {
      const parsed = JSON.parse(typeof message === "string" ? message : message.toString());
      if (parsed.type === "ping") {
        ws.send(JSON.stringify({ type: "pong", data: { ts: Date.now() } }));
      }
    } catch {
      // Ignore non-JSON messages
    }
  },

  close(ws: ServerWebSocket) {
    clients.delete(ws);
  },
};

// Return number of connected WebSocket clients
export function getConnectedCount(): number {
  return clients.size;
}
