# FE-05: CSRF Integration — Implementation

## Files added
- `frontend/src/api/client.test.ts` — unit tests for the CSRF flow.

## Files changed
- `frontend/src/api/client.ts` — adds `getCsrfToken`, `ensureCsrfToken`,
  and `X-CSRFToken` injection for unsafe methods.
- `frontend/src/shell/AppShell.tsx` — calls `ensureCsrfToken` before
  submitting the login form.

## Approach
1. `getCsrfToken` reads the `csrftoken` cookie (URL-decoded) and
   returns `null` when the cookie is missing.
2. `ensureCsrfToken` pre-flights `GET /api/v1/bootstrap` if the cookie
   is missing so the next mutation succeeds.
3. The shared `api()` client sets `X-CSRFToken` on every
   `POST`/`PUT`/`PATCH`/`DELETE` request.
