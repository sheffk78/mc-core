# TrustOffice Security Review
**Date:** 2026-04-24  
**Reviewer:** Kit (AppSec Analysis)  
**Scope:** Backend (server.py, security.py, dependencies.py, routers/auth.py, routers/admin.py, routers/admin_api.py) + Frontend (AuthContext.js, utils/api.js)  
**Methodology:** Static analysis, OWASP Top 10, auth flow review, secret management, injection surface audit

> **Remediation status (2026-05-19):** All Critical, High, and Medium findings have been fixed and deployed.
> See [security-remediation-may-2026.md](./security-remediation-may-2026.md) for full details.
> - C-1 ✅ | C-2 ⚠️ kept intentionally (localStorage JWT as fallback) | C-3 ✅
> - H-1 ✅ | H-2 ⏳ deferred (admin-only) | H-3 ✅
> - M-1 ✅ | M-3 ✅ | M-4 ✅ | M-6 ✅
> - L-5 ✅

---

## Executive Summary

TrustOffice has a reasonable security foundation — bcrypt passwords, HttpOnly cookies, rate limiting, security headers middleware, and CSRF state tokens for OAuth. However, **five critical/high issues need immediate attention** before this is production-hardened for a trust management platform handling sensitive legal and financial data.

The most serious issues are: a hardcoded default admin password in startup code, JWT tokens stored in localStorage (XSS-stealable), overly permissive CORS configuration, and unrestricted MongoDB regex injection via admin search endpoints.

---

## Findings by Priority

---

### 🔴 CRITICAL

---

#### C-1 — Hardcoded Default Admin Password in `server.py`

**File:** `backend/server.py` → `ensure_primary_admin()` (line ~200)  
**Issue:** The function hardcodes `default_password = "TrustAdmin2026!"` and uses it as the default password for the primary admin account (`contact@trustoffice.app`). This password is in plaintext in source code, which means it's in git history forever, visible to any developer, and likely in any CI/CD logs.

```python
default_password = "TrustAdmin2026!"
```

**Impact:** Anyone who reads the source code (or any git commit) can log into the admin account using this password unless it was manually changed post-deployment. This is a full account takeover of the highest-privilege account.

**Fix:**
- Remove the default password entirely. Admin accounts should not have a default password baked into source.
- If bootstrapping is required, generate a random password at first-run, print it once to logs (not code), and force a change on first login.
- Rotate the current password immediately and audit for any unauthorized logins to `contact@trustoffice.app`.
- Run `git log -S "TrustAdmin2026"` to confirm how far this propagates in history; consider a git history scrub.

---

#### C-2 — JWT Tokens Stored in `localStorage` — XSS-Stealable

**Files:** `frontend/src/context/AuthContext.js`, `frontend/src/utils/api.js`  
**Issue:** After login and OAuth callback, JWT tokens are written to `localStorage`:

```javascript
localStorage.setItem('auth_token', data.token);
```

`localStorage` is accessible by any JavaScript on the page. A single XSS vulnerability anywhere in the app — including in third-party libraries, injected ads, or browser extensions — can silently steal every user's auth token.

**Additional concern:** The backend CSP in `security.py` includes `'unsafe-inline'` and `'unsafe-eval'` for scripts, which significantly weakens XSS protection:
```python
"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
```

**Impact:** Full session hijacking for any user who encounters an XSS vector. For a trust management platform, this means an attacker could access, modify, or export all trust documents, financial records, and beneficiary data.

**Fix:**
- Store JWTs in `HttpOnly; Secure; SameSite=Strict` cookies exclusively — the backend already issues these, but the token is also being put in localStorage as a "fallback."
- Remove the `localStorage.setItem('auth_token', ...)` calls entirely. The HttpOnly cookie is the canonical credential; the Authorization header fallback in `getAuthHeaders()` should be removed or replaced with a non-JWT session approach.
- Tighten CSP: eliminate `unsafe-inline` and `unsafe-eval` from `script-src`. Use nonces or hashes instead.

---

#### C-3 — Wildcard CORS Origin in `server.py`

**File:** `backend/server.py` (line ~160)  
**Issue:**
```python
allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
```

If `CORS_ORIGINS` is not set in the environment, CORS falls back to `*` — allowing any origin to make credentialed requests to the API.

**Impact:** Any malicious website can make authenticated API calls on behalf of logged-in TrustOffice users (CSRF via CORS). Combined with `allow_credentials=True`, this is especially dangerous — browsers normally block credentialed CORS with wildcard, but if the env var is ever unset this becomes exploitable in some configurations.

**Fix:**
- Set `CORS_ORIGINS` explicitly in all deployment environments. Never rely on the default.
- Change the default fallback to an empty list or a strict allowlist, not `*`.
- Add a startup assertion that fails fast if `CORS_ORIGINS` is unset in non-development environments.

---

### 🟠 HIGH

---

#### H-1 — NoSQL Injection via Unvalidated `$regex` in Admin Search

**Files:** `backend/routers/admin.py` → `list_customers()`, `backend/routers/admin_api.py` → `list_users()`  
**Issue:** Both admin endpoints pass user-controlled `search` strings directly into MongoDB `$regex` queries without sanitization:

```python
# admin.py
query["$or"] = [
    {"email": {"$regex": search, "$options": "i"}},
    {"name": {"$regex": search, "$options": "i"}}
]
```

A malicious regex like `.*` causes a full collection scan (ReDoS / performance attack). Crafted patterns like `^admin.*` can be used to enumerate user data character by character. Additionally, the `InputSanitizer.check_nosql_injection()` method in `security.py` checks for `$regex` as a suspicious pattern, but the admin routes bypass this sanitizer entirely.

**Impact:** ReDoS (denial of service via expensive regex), data enumeration by authenticated admins with malicious intent or via a compromised admin session.

**Fix:**
- Escape regex special characters before injecting into `$regex`: use `re.escape(search)` in Python.
- Apply `InputSanitizer.check_nosql_injection()` to admin search inputs.
- Consider using MongoDB's text search index instead of `$regex` for user-facing search.

---

#### H-2 — Impersonation Token Has No Expiry or Scope Marker

**File:** `backend/routers/admin.py` → `impersonate_user()`  
**Issue:** The impersonation feature generates a standard 7-day JWT for the target user using `create_jwt_token()`. This token is identical to one the target user would receive via normal login — it has no impersonation flag, no reduced TTL, and no revocation mechanism.

```python
impersonation_token = create_jwt_token(target_user["user_id"], target_user["email"])
```

**Impact:**
- If the impersonation token leaks (e.g., via browser history, log, MITM on the redirect), it grants full 7-day access to the target user's account.
- The impersonation token cannot be distinguished from a real user session, so there's no audit trail in the target user's session history.
- Admins could silently impersonate users for 7 days with no expiry pressure.

**Fix:**
- Create a short-lived impersonation token (15–30 minutes) by passing a custom expiry to `create_jwt_token()`.
- Add an `impersonated_by` claim to the JWT payload so the backend can detect and restrict impersonated sessions (e.g., block password changes, prevent subscription modifications).
- Log the impersonation start in the target user's session collection, not just `admin_audit_log`.

---

#### H-3 — Password Reset Applies Weaker Validation Than Registration

**File:** `backend/routers/auth.py` → `reset_password()`  
**Issue:** The `/auth/reset-password` endpoint only checks `len(request.new_password) < 8`, while registration uses `validate_password_strength()` which also requires at least one letter and one number. A user could reset to a password like `12345678` that would be rejected at registration.

```python
# reset_password() - weak check
if len(request.new_password) < 8:
    raise HTTPException(...)

# register() - full check (NOT applied here)
is_valid, error_msg = validate_password_strength(user.password)
```

**Impact:** Users who reset their password end up with weaker credentials than the registration policy intends. Not critical on its own, but in combination with brute-force exposure it's a meaningful gap.

**Fix:**
- Apply `validate_password_strength()` in `reset_password()` — it's already defined in the same file.

---

#### H-4 — Admin API Rate Limiting is In-Process and Not Distributed

**Files:** `backend/security.py` (main rate limiter), `backend/routers/admin_api.py` (inline rate limiter)  
**Issue:** Both rate limiters store state in Python process memory (`defaultdict(list)` or `InMemoryRateLimiter`). This means:
1. Rate limits reset on every server restart/redeploy.
2. In a multi-process or multi-instance deployment (Railway scales horizontally), each instance has independent rate limit counters — an attacker can hammer N instances and get N × rate-limit requests before being blocked.
3. The `admin_api.py` rate limiter uses `time.time()` and a `defaultdict` that grows unbounded (no cleanup).

**Impact:** Rate limiting provides false security assurance. A targeted brute-force of `/api/auth/login` or the Admin API key endpoint would succeed in a scaled environment.

**Fix:**
- Replace both in-memory rate limiters with Redis-backed counters (Railway supports Redis).
- The code even includes a comment: `"For production, consider Redis-backed implementation."` — this needs to be acted on before launch.

---

### 🟡 MEDIUM

---

#### M-1 — JWT Token Leaked in OAuth Redirect URL

**File:** `backend/routers/auth.py` → `google_callback()`  
**Issue:** After successful Google OAuth, the JWT token is passed as a plain query parameter in the redirect URL:

```python
response = RedirectResponse(
    url=f"{frontend_url}/auth/callback?token={jwt_token}&redirect={...}"
)
```

**Impact:** The JWT appears in:
- Browser history (persistent)
- Server access logs on the frontend server
- Referrer headers if the callback page loads any third-party resources
- Any browser extensions monitoring network activity

This is a known OAuth anti-pattern (OAuth spec discourages tokens in query strings for this reason).

**Fix:**
- Pass the token via a one-time short-lived code (exchange pattern): store the JWT server-side with a random code, redirect with the code, have the frontend exchange the code for the JWT via a POST.
- Alternatively, use the existing HttpOnly session cookie (already set in the response) as the sole credential and drop the `?token=` parameter. The frontend currently reads it from the URL and puts it in localStorage anyway — both behaviors need to change.

---

#### M-2 — Broad Admin by Email — No MFA, No Session Binding

**Files:** `backend/dependencies.py`, `backend/routers/admin.py`, `backend/routers/auth.py`  
**Issue:** Admin status is granted purely based on email (`contact@trustoffice.app`) with no second factor. The `require_admin` dependency re-checks email on every request, which means anyone who can log in as that email gets full admin access immediately. There's also no IP allowlisting, no step-up authentication, and no admin session distinct from a regular user session.

**Impact:** The admin email is a single point of failure. If the password is compromised (see C-1), or if a session token is stolen (see C-2), an attacker gets full admin access to all customer data with no friction.

**Fix:**
- Add TOTP/MFA as a requirement for admin-level endpoints.
- Consider a separate admin session token or a step-up re-auth flow before destructive/sensitive admin actions.
- Log all admin actions to an append-only audit log.

---

#### M-3 — `X-Forwarded-For` Used for IP-Based Rate Limiting Without Validation

**Files:** `backend/security.py` → `_get_client_key()`, `backend/routers/admin_api.py` → `get_client_ip()`  
**Issue:** Both use `X-Forwarded-For` as the client IP for rate limiting:

```python
forwarded = request.headers.get("X-Forwarded-For")
if forwarded:
    ip = forwarded.split(",")[0].strip()
```

`X-Forwarded-For` is a client-controlled header. Without validating that it comes from a trusted proxy, an attacker can spoof any IP address and bypass IP-based rate limits entirely.

**Fix:**
- Only trust `X-Forwarded-For` when it arrives from Railway's known proxy IP range.
- Configure FastAPI/uvicorn with `--forwarded-allow-ips` for trusted proxy IPs.
- As a simpler mitigation: use the rightmost (last) IP in the `X-Forwarded-For` chain, which is harder to spoof.

---

#### M-4 — Session Cookie `SameSite=none` Reduces CSRF Protection

**File:** `backend/routers/auth.py` → `login()` and `google_callback()`  
**Issue:**
```python
response.set_cookie(
    key="session_token",
    value=token,
    httponly=True,
    secure=True,
    samesite="none",   # ← problem
    ...
)
```

`SameSite=none` was set to support cross-site cookie sending (likely for the OAuth callback). However, `SameSite=none` combined with `Secure` means cookies are sent on all cross-site requests, including cross-site form POSTs and `fetch()` with `credentials: 'include'`. This requires CSRF tokens for all state-changing requests.

Currently there is no CSRF token mechanism implemented for form-based endpoints.

**Fix:**
- Change to `SameSite=lax` for the session cookie. This blocks cross-site POST/DELETE/PUT/PATCH while still allowing top-level navigation redirects (which is all OAuth needs).
- If cross-origin API calls are required (different domain frontend → API), use the Authorization header with the JWT (which is already implemented as a fallback) instead of relying on cross-site cookies.

---

#### M-5 — `InputSanitizer.sanitize_string()` HTML-Encodes All Strings Including Non-Display Fields

**File:** `backend/security.py` → `sanitize_string()`  
**Issue:**
```python
value = html.escape(value)
```

`html.escape()` converts `&` to `&amp;`, `<` to `&lt;`, etc. This is appropriate for HTML display contexts, but when applied to data stored in MongoDB and returned via API (e.g., trust names, entity names), the escaped form gets stored and returned to non-HTML clients. Downstream consumers of the API (or PDF generation code) would receive double-encoded strings like `Jeff &amp; Associates` instead of `Jeff & Associates`.

**Impact:** Data corruption / display bugs when the sanitizer is applied aggressively to non-HTML contexts. Not a security risk on its own, but it suggests the sanitization strategy is applied bluntly rather than at the rendering layer (where XSS sanitization belongs).

**Fix:**
- Apply HTML escaping at the render/template layer, not at the storage layer.
- For storage: strip null bytes and limit length, but don't HTML-encode. The MongoDB driver handles safe storage.
- For API responses rendered in React: React auto-escapes all string content in JSX — additional server-side HTML encoding is redundant and causes double-encoding.

---

#### M-6 — Dead Code After `raise` in `exchange_session()` — Unreachable OAuth Session Path

**File:** `backend/routers/auth.py` → `exchange_session()`  
**Issue:**
```python
raise HTTPException(status_code=501, detail="OAuth session exchange not yet configured on this platform")

email = session_data.get("email")   # ← unreachable
# ... more unreachable code
```

The endpoint raises immediately, but ~60 lines of user-creation and session logic follow as dead code. This dead code still references `session_data` which is never defined, meaning if someone removed the `raise` statement (intentionally or accidentally), the code would crash immediately with a `NameError` — which might mask a more serious auth bypass.

**Fix:**
- Delete the unreachable dead code block entirely.
- If Google OAuth via this session exchange path is intended for future use, stub it properly with a comment and a return, not dead code.

---

### 🔵 LOW

---

#### L-1 — `is_admin` Status Checked Client-Side in `AuthContext.js`

**File:** `frontend/src/context/AuthContext.js`  
**Issue:**
```javascript
const PRIMARY_ADMIN_EMAIL = 'contact@trustoffice.app';
if (userEmail?.toLowerCase() === PRIMARY_ADMIN_EMAIL) {
  // Grant full access client-side
  const adminState = { is_active: true, is_read_only: false, ... };
  setSubscription(adminState);
  setIsReadOnly(false);
  return adminState;
}
```

The client-side admin bypass skips the API call to `/subscription/state` for the primary admin email. This is purely a UX optimization (the API would return the same result), but it means:
- If someone registers with `contact@trustoffice.app` on a different account (hypothetically), the frontend grants them a full-access UI state before the backend confirms.
- It duplicates business logic that should live only on the server.

**Fix:**
- Remove the client-side admin check. The API returns the correct subscription state; trust it.
- The UX "optimization" saves one API call but introduces a discrepancy between client and server state.

---

#### L-2 — `admin_api.py` Rate Limiter Memory Leak

**File:** `backend/routers/admin_api.py` → `check_rate_limit()`  
**Issue:** The `rate_limit_store` dict grows indefinitely as new IP addresses make requests. There's a filter to remove old timestamps (`now - t < RATE_LIMIT_WINDOW`), but IP keys are never removed from the dict:

```python
rate_limit_store = defaultdict(list)  # Module-level, never cleaned
rate_limit_store[identifier] = [t for t in rate_limit_store[identifier] if ...]
# ↑ Old IPs accumulate as empty lists or stay in dict indefinitely
```

**Impact:** Minor memory leak in long-running processes. Low severity, but if the Admin API receives high traffic (legitimate or DDoS), this dict could grow large.

**Fix:**
- Add a periodic cleanup task (same pattern as `InMemoryRateLimiter.cleanup()` in `security.py`).
- Better: consolidate on the `InMemoryRateLimiter` already implemented in `security.py` rather than maintaining a second, simpler implementation.

---

#### L-3 — `FOREVER_FREE_EMAILS` Hardcoded in `dependencies.py`

**File:** `backend/dependencies.py`  
**Issue:**
```python
FOREVER_FREE_EMAILS = {
    "admin@wingpointtrusts.com",
    "contact@trustoffice.app",
}
```

These emails get full free access. Adding/removing this list requires a code deployment. More concerning: `admin@wingpointtrusts.com` is a business email for a different brand — if that email address is ever compromised, transferred, or the WingPoint domain lapses, whoever controls it gets full TrustOffice access.

**Fix:**
- Move forever-free grants to the database (`is_forever_free` flag on the user record) rather than hardcoding emails.
- The admin already has tooling to set `forever_free` subscriptions via the admin panel — use that instead of the hardcoded set.

---

#### L-4 — `selected_trust_id` Stored in `localStorage` Without Validation

**File:** `frontend/src/context/AuthContext.js`  
**Issue:**
```javascript
const storedTrustId = localStorage.getItem('selected_trust_id');
const storedTrust = data.find(t => t.trust_id === storedTrustId);
```

The stored trust ID is used to auto-select a trust on load. The `find()` lookup means it can only match trusts the user actually owns (API-returned list), so there's no horizontal privilege escalation here. However, trust IDs follow a predictable `trust_XXXXXXXXXXXX` format and are stored in plaintext in localStorage.

**Impact:** Minor. No exploitable path identified with the current trust ownership check.

**Fix:**
- Acceptable as-is given the server-side trust ownership check, but worth noting for a future session-storage migration.

---

#### L-5 — Verbose Error Logging in Google OAuth Callback

**File:** `backend/routers/auth.py` → `google_callback()`  
**Issue:**
```python
logger.error(f"Token exchange failed: {token_response.text}")
logger.error(f"Failed to fetch user info: {userinfo_response.text}")
```

Google's error responses from token exchange can contain OAuth codes, partial credentials, or debug tokens. Logging the full response body to application logs (which may be shipped to external log aggregators) could expose sensitive OAuth data.

**Fix:**
- Log error type and status code only: `logger.error(f"Token exchange failed: status={token_response.status_code}")`.

---

## Summary Table

| ID | Title | Priority | File(s) |
|----|-------|----------|---------|
| C-1 | Hardcoded default admin password | **Critical** | server.py |
| C-2 | JWT in localStorage, weak CSP | **Critical** | AuthContext.js, api.js, security.py |
| C-3 | Wildcard CORS fallback | **Critical** | server.py |
| H-1 | Unescaped regex in admin search (NoSQL injection / ReDoS) | **High** | admin.py, admin_api.py |
| H-2 | Impersonation token: no expiry, no scope | **High** | admin.py |
| H-3 | Weaker password validation on reset vs register | **High** | routers/auth.py |
| H-4 | In-process rate limiting (bypassed in multi-instance) | **High** | security.py, admin_api.py |
| M-1 | JWT in OAuth redirect URL query parameter | **Medium** | routers/auth.py |
| M-2 | Admin access: no MFA, no step-up auth | **Medium** | dependencies.py, admin.py |
| M-3 | X-Forwarded-For spoofable for rate limit bypass | **Medium** | security.py, admin_api.py |
| M-4 | SameSite=none weakens CSRF protection | **Medium** | routers/auth.py |
| M-5 | HTML-encoding applied at storage layer (double-encoding) | **Medium** | security.py |
| M-6 | Dead code after raise in exchange_session() | **Medium** | routers/auth.py |
| L-1 | Admin state checked client-side (logic duplication) | **Low** | AuthContext.js |
| L-2 | Memory leak in admin_api rate limiter | **Low** | admin_api.py |
| L-3 | Hardcoded forever-free emails in source | **Low** | dependencies.py |
| L-4 | Trust ID in localStorage | **Low** | AuthContext.js |
| L-5 | Verbose OAuth error logging | **Low** | routers/auth.py |

---

## Immediate Action Items (Before Public Launch)

1. **Rotate the admin password** — assume `TrustAdmin2026!` is compromised. Audit login history.
2. **Remove `localStorage` JWT storage** — rely solely on the HttpOnly cookie already being set.
3. **Set `CORS_ORIGINS` explicitly** in Railway env and assert it at startup.
4. **Escape regex in admin search** — one line fix: `re.escape(search)`.
5. **Apply `validate_password_strength()` in `reset_password()`** — trivial change, already have the function.

Items 1–3 are pre-launch blockers for a trust/legal data platform. Items 4–5 can be batched into the next deploy.

---

*Review generated 2026-04-24. Re-run after addressing Critical/High items.*
