# FE-05: CSRF Integration — Verification

## Evidence
- `frontend/src/api/client.ts` reads the `csrftoken` cookie and sets
  `X-CSRFToken` on every unsafe request.
- `frontend/src/api/client.ts` exports `getCsrfToken` and
  `ensureCsrfToken` so the shell and the login form can guarantee a
  cookie is present before submitting.
- `frontend/src/shell/AppShell.tsx` calls `ensureCsrfToken` before
  submitting the login form.

## Tests
- `src/api/client.test.ts` — verifies the cookie read, the
  `ensureCsrfToken` flow, the `X-CSRFToken` header on unsafe
  methods, and the `credentials: "include"` flag.

## Acceptance criteria
| ID | Criterion | Status |
|---|---|---|
| AC-1 | getCsrfToken() works | ✅ |
| AC-2 | unsafe methods send X-CSRFToken | ✅ |
| AC-3 | E2E test passes | ✅ (`tests/e2e/auth.spec.ts`) |
| AC-4 | typecheck passes | ✅ |
