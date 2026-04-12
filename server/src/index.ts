import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { serveStatic } from "hono/bun";

import { authMiddleware } from "../middleware/auth";
import { brandsRouter } from "../routes/brands";
import { tasksRouter } from "../routes/tasks";
import { approvalsRouter } from "../routes/approvals";
import { activitiesRouter } from "../routes/activities";
import { costsRouter } from "../routes/costs";
import { statsRouter } from "../routes/stats";
import { revenueRouter } from "../routes/revenue";
import { wsHandlers } from "../ws";

const app = new Hono();

// ---------------------------------------------------------------------------
// Global middleware
// ---------------------------------------------------------------------------
const frontendUrl = process.env.FRONTEND_URL || "http://localhost:5173";
app.use(
  "*",
  cors({
    origin: [frontendUrl, "https://mc.agentictrust.app"],
    allowMethods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization", "X-MC-Key"],
    credentials: true,
  })
);
app.use("*", logger());

// ---------------------------------------------------------------------------
// Health endpoint (no auth)
// ---------------------------------------------------------------------------
app.get("/health", (c) => {
  return c.json({
    status: "ok",
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

// ---------------------------------------------------------------------------
// API v1 routes (auth required)
// ---------------------------------------------------------------------------
app.use("/api/v1/*", authMiddleware);

app.route("/api/v1/brands", brandsRouter);
app.route("/api/v1/tasks", tasksRouter);
app.route("/api/v1/approvals", approvalsRouter);
app.route("/api/v1/activities", activitiesRouter);
app.route("/api/v1/costs", costsRouter);
app.route("/api/v1/stats", statsRouter);
app.route("/api/v1/revenue", revenueRouter);

// ---------------------------------------------------------------------------
// Serve static frontend (built Vite output)
// ---------------------------------------------------------------------------
app.get(
  "/*",
  serveStatic({
    root: "../web/dist",
    rewriteRequestPath: (path) => {
      if (path.match(/\.\w+$/)) return path;
      return "/index.html";
    },
  })
);

// ---------------------------------------------------------------------------
// Start server with Bun native WebSocket support
// ---------------------------------------------------------------------------
const port = Number(process.env.PORT) || 3000;

Bun.serve({
  port,
  fetch(req, server) {
    // WebSocket upgrade handling
    if (new URL(req.url).pathname === "/ws") {
      const token = new URL(req.url).searchParams.get("token");
      if (token !== process.env.MC_AUTH_TOKEN) {
        return new Response("Unauthorized", { status: 401 });
      }
      if (server.upgrade(req)) {
        return; // WebSocket upgraded — no HTTP response needed
      }
      return new Response("WebSocket upgrade failed", { status: 400 });
    }
    // Everything else goes to Hono
    return app.fetch(req, server);
  },
  websocket: wsHandlers,
});

console.log(`🚀 Mission Control v2 running on port ${port}`);
console.log(`   Health: http://localhost:${port}/health`);
console.log(`   API:    http://localhost:${port}/api/v1`);
console.log(`   WS:     ws://localhost:${port}/ws`);
