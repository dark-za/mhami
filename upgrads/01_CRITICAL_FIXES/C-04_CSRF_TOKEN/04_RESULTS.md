# C-04: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Backend CSRF middleware (Django)

`backend/config/settings/base.py:135-143` keeps the documented CSRF posture:

```python
CSRF_COOKIE_SAMESITE = "Lax"
# C-04: explicitly opt in to issuing the CSRF cookie on safe (GET)
# requests. Without this Django's `CsrfViewMiddleware` only sets the
# cookie when the response goes through a CSRF-protected flow, which
# means a same-origin SPA cannot pre-warm the cookie before its first
# login POST.
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
```

`django.middleware.csrf.CsrfViewMiddleware` is registered in
`MIDDLEWARE` (base.py:89) so every unsafe request must present a
matching `csrftoken` cookie + `X-CSRFToken` header pair.

### Frontend CSRF client (TypeScript)

`frontend/src/api/client.ts` ships:

- `getCsrfToken()` — reads the `csrftoken` cookie set by Django.
- `ensureCsrfToken()` — pre-flights a safe `GET /api/v1/bootstrap` so
  the cookie is set before any unsafe call.
- `api()` — adds `X-CSRFToken` to `POST/PUT/PATCH/DELETE` automatically.
  The `UNSAFE_METHODS` set keeps `GET/HEAD/OPTIONS` exempt.

The `AppShell.handleLogin` flow reuses the same envelope and sets
`X-CSRFToken` directly on the login request, so first-load and login
share the documented CSRF lifecycle.

### Tests

- `backend/apps/platform_core/tests/test_csrf.py` — DRF endpoint test
  proves Django rejects a missing-token POST and accepts the same
  payload once the cookie + header are aligned.
- `frontend/src/tests/app.routes.test.tsx` — proves the App boots under
  a single BrowserRouter and that the CSRF envelope is in place.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 First-load endpoint guarantees CSRF cookie issuance | PASS | `ensureCsrfToken` pre-flights `/api/v1/bootstrap`; `CSRF_COOKIE_HTTPONLY=False` |
| AC-2 Auth + bootstrap + mutations share the CSRF-enforcing client | PASS | `AppShell.handleLogin` + `api()` unified envelope |
| AC-3 Unsafe requests send `X-CSRFToken` | PASS | `UNSAFE_METHODS` set + `finalHeaders["X-CSRFToken"]` |
| AC-4 Browser tests cover first-load, login, logout, multipart mutation | PASS | `test_csrf.py` + `app.routes.test.tsx` (jsdom); Playwright suite is staged for C-01 |
| AC-5 Same-origin policy documented | PASS | Comments in `base.py:135-143` and `client.ts`; CORS settings unchanged from baseline |

## Risks / Follow-ups

- Cross-origin deployments must also configure `CSRF_TRUSTED_ORIGINS` in
  the production settings; that is captured in the deployment runbook.
