import type { Context, Next, MiddlewareHandler } from "hono";
import { timingSafeEqual } from "crypto";

/**
 * Timing-safe string comparison to prevent timing attacks.
 */
function safeCompare(a: string, b: string): boolean {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  if (bufA.length !== bufB.length) return false;
  return timingSafeEqual(bufA, bufB);
}

/**
 * Read the expected auth token from environment.
 * Falls back to empty string so requests always fail if unconfigured.
 */
function getExpectedToken(): string {
  return Bun.env.MC_AUTH_TOKEN ?? "";
}

/**
 * Extract the token from a Hono request context.
 * Accepts both:
 *   - Authorization: Bearer <token>
 *   - X-MC-Key: <token>
 */
function extractToken(c: Context): string | null {
  // Check Authorization header first
  const authHeader = c.req.header("Authorization");
  if (authHeader?.startsWith("Bearer ")) {
    return authHeader.slice(7).trim();
  }

  // Check X-MC-Key header
  const mcKey = c.req.header("X-MC-Key");
  if (mcKey) {
    return mcKey.trim();
  }

  return null;
}

/**
 * authMiddleware — blocks unauthenticated requests on /api/v1/* routes.
 * Returns 401 JSON for missing or invalid tokens.
 */
export const authMiddleware: MiddlewareHandler = async (c: Context, next: Next) => {
  const expected = getExpectedToken();

  if (!expected) {
    console.warn(`[AUTH] MC_AUTH_TOKEN not configured — denying request from ${c.req.header("x-forwarded-for") ?? "unknown"} at ${new Date().toISOString()}`);
    return c.json({ error: "Unauthorized", message: "Auth not configured" }, 401);
  }

  const token = extractToken(c);

  if (!token) {
    const ip = c.req.header("x-forwarded-for") ?? c.req.header("x-real-ip") ?? "unknown";
    console.warn(`[AUTH] Missing token from ${ip} at ${new Date().toISOString()} — ${c.req.method} ${c.req.path}`);
    return c.json({ error: "Unauthorized", message: "Missing authentication token" }, 401);
  }

  if (!safeCompare(token, expected)) {
    const ip = c.req.header("x-forwarded-for") ?? c.req.header("x-real-ip") ?? "unknown";
    console.warn(`[AUTH] Invalid token from ${ip} at ${new Date().toISOString()} — ${c.req.method} ${c.req.path}`);
    return c.json({ error: "Unauthorized", message: "Invalid authentication token" }, 401);
  }

  await next();
};

/**
 * optionalAuth — sets `authenticated` context variable but does NOT block.
 * Used for WebSocket upgrade and health endpoints.
 */
export const optionalAuth: MiddlewareHandler = async (c: Context, next: Next) => {
  const expected = getExpectedToken();

  if (!expected) {
    c.set("authenticated", false);
    await next();
    return;
  }

  const token = extractToken(c);
  const isAuthenticated = token !== null && safeCompare(token, expected);
  c.set("authenticated", isAuthenticated);

  await next();
};
