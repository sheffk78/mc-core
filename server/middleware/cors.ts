import { cors } from "hono/cors";

/**
 * CORS middleware configuration for Mission Control v2.
 *
 * Allows the frontend (dev or production) to make cross-origin requests
 * to the API with the required auth headers.
 */
const corsMiddleware = cors({
  origin: [
    Bun.env.FRONTEND_URL ?? "http://localhost:5173",
    "https://mc.agentictrust.app",
  ],
  allowMethods: ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
  allowHeaders: ["Content-Type", "Authorization", "X-MC-Key"],
  maxAge: 86400,
});

export default corsMiddleware;
