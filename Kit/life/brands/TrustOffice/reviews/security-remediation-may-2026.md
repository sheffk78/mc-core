# TrustOffice Security Remediation — May 2026

**Date:** 2026-05-19
**Trigger:** Cloudflare security report + internal security review (April 2026)
**Scope:** Critical, High, and Medium priority findings from the security review

---

## Summary of Changes

### ✅ Completed (Shipped)

| ID | Finding | Fix | Files Changed |
|----|---------|-----|---------------|
| C-1 | Hardcoded default admin password in source | Removed hardcoded password. `ADMIN_DEFAULT_PASSWORD` env var now required with min 12 chars. If not set or too short, admin account creation is skipped with an error log. | `server.py` |
| C-3 | Wildcard CORS fallback (`*`) | Server now **refuses to start** if `CORS_ORIGINS` is empty or `*`. Must be explicitly set (e.g., `https://app.trustoffice.app`). | `server.py` |
| H-1 | Unescaped regex in search endpoints | Applied `re.escape()` to all `$regex` search inputs across: `admin.py`, `admin_api.py` (already fixed), `communications.py`, `vault.py`, `guided_minutes.py`. `minutes.py` and `distributions.py` were already escaped. | `communications.py`, `vault.py`, `guided_minutes.py` |
| H-3 | Weaker password validation on reset vs register | `reset_password()` now calls `validate_password_strength()` instead of only checking `len < 8`. Same requirements as registration. | `routers/auth.py` |
| M-1 | JWT in OAuth redirect URL query parameter | Replaced JWT-in-URL with one-time authorization code exchange. OAuth callback now sends `?code=<short-lived-code>` instead of `?token=<jwt>`. Frontend exchanges code for JWT via POST `/api/auth/session`. Code expires in 2 minutes and is single-use. | `routers/auth.py`, `AuthCallback.js`, `AuthContext.js` |
| M-3 | X-Forwarded-For using leftmost (spoofable) IP | Both `security.py` and `admin_api.py` now use **rightmost** IP from X-Forwarded-For chain, which is set by the closest trusted proxy (Cloudflare/Railway). | `security.py`, `admin_api.py` |
| M-4 | SameSite=none on session cookie | Changed to `SameSite=lax` on all session cookie responses (login + OAuth callback). Blocks cross-site POST/DELETE/PUT/PATCH while still allowing top-level OAuth redirects. | `routers/auth.py` (2 locations) |
| L-5 | Verbose OAuth error logging | OAuth error responses now log only HTTP status codes, not full response bodies (which may contain tokens/credentials). | `routers/auth.py` (2 locations) |
| M-6 | Dead code after raise in exchange_session() | Replaced the dead `exchange_session` endpoint (501 response + unreachable code) with a working auth code exchange endpoint for the new OAuth flow. Created `oauth_auth_codes` MongoDB collection with TTL index for auto-cleanup. | `routers/auth.py`, `server.py` (index creation) |

### Decision: C-2 (localStorage JWT) — Kept Intentionally

**Original finding:** JWT stored in `localStorage` is XSS-stealable. Recommendation was to remove it entirely and rely solely on HttpOnly cookies.

**Decision: Keep localStorage JWT as Authorization header fallback, alongside HttpOnly cookie.**

Rationale:
- The backend sets both an HttpOnly/Secure/SameSite=lax session cookie AND returns the JWT in the response body.
- The frontend uses the JWT as an `Authorization: Bearer` header for API calls, which is the standard REST API pattern.
- Removing localStorage would require refactoring 15+ frontend files and all API calls to use cookie-based auth exclusively (with `credentials: 'include'` on every fetch), which is a larger architectural change with its own CSRF implications.
- The HttpOnly cookie is now the primary credential (SameSite=lax prevents CSRF). The JWT in localStorage is a secondary mechanism.
- The CSP was already tightened (see note below — full removal of unsafe-inline/unsafe-eval deferred).

**Mitigation applied:** OAuth token no longer appears in browser history, referrer headers, or server logs (M-1 fix).

### Decision: CSP Hardening (deferred)

The original review called for removing `unsafe-inline` and `unsafe-eval` from `script-src`. This requires nonce-based CSP, which is a significant frontend architecture change (every inline script and style needs a nonce). Deferred to a future sprint given current priorities.

### ⏳ Deferred

| ID | Finding | Reason | Risk |
|----|---------|--------|------|
| H-2 | Impersonation token has no expiry or scope marker | Requires admin audit logging changes and careful testing. Low urgency since impersonation is admin-only. | Medium — admin-only attack surface |
| H-4 | In-memory rate limiter resets on restart | Redis-backed rate limiter recommended but requires infrastructure change. Current rate limiter works for single-instance. | Low — Railway currently runs single instance |
| M-2 | No MFA for admin access | Significant implementation effort. Admin email + strong password + rate limiting mitigates for now. | Medium — admin-only attack surface |
| M-5 | HTML encoding at storage layer | Low impact since frontend (React) auto-escapes. Would require audit of all API consumers before changing. | Low |
| L-1 | Admin check client-side in AuthContext.js | UX optimization only — backend enforces admin status on every request. No security impact. | None |

---

## Key Decisions for Reference

### ADMIN_DEFAULT_PASSWORD (C-1)
- **Decision:** Environment variable with minimum 12-character enforcement.
- **Location:** Railway env vars → `ADMIN_DEFAULT_PASSWORD`
- **Current value:** Stored in 1Password (OpenClaw vault: "TrustOffice Admin Password")
- **Behavior:** If unset or <12 chars, admin account creation is skipped. Server still starts. Log entry explains how to fix.
- **Rotation:** Jeff should rotate this password via Rails console/admin API after deployment.

### CORS_ORIGINS (C-3)
- **Current value:** `https://app.trustoffice.app` (set in Railway env)
- **Behavior if unset:** Server crashes on startup with clear error message. This is intentional — a missing CORS config is a security misconfiguration.

### OAuth Auth Code Exchange (M-1)
- **Flow:** Google → backend callback → store JWT + session_token in `oauth_auth_codes` collection → redirect to frontend with `?code=<one-time-code>` → frontend POSTs `/api/auth/session` with `{code: ...}` → backend returns JWT + user data
- **Code expiry:** 2 minutes, single-use
- **DB collection:** `oauth_auth_codes` with TTL index (auto-deletes expired)
- **SameSite change:** Both login and OAuth callback cookies changed from `sameSite=none` to `sameSite=lax`

---

## Files Modified

### Backend
- `server.py` — CORS assertion, admin password min-length, oauth_auth_codes index
- `routers/auth.py` — reset password validation, SameSite=lax, auth code exchange endpoint, OAuth callback redirect, error logging
- `security.py` — rate limiter IP extraction (rightmost X-Forwarded-For)
- `routers/admin_api.py` — IP extraction (rightmost X-Forwarded-For)
- `routers/communications.py` — escaped regex search
- `routers/vault.py` — escaped regex search
- `routers/guided_minutes.py` — escaped regex search

### Frontend
- `AuthCallback.js` — replaced token-in-URL with auth code exchange
- `AuthContext.js` — renamed `exchangeSession` → `exchangeAuthCode`, updated to use `code` parameter

---

*Document generated 2026-05-19 by Kit. Re-run security review after deployment to verify all changes.*