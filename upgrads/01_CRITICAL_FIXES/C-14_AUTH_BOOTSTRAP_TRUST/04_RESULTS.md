# C-14: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Static snapshot is no longer "authenticated"

`frontend/src/design-system/tokens.ts` now ships the static
`bootstrapSnapshot` with `currentUser.authenticated = false` and empty
`permissions` / `enabledModules` arrays. The snapshot is used only as
a shape template and never reaches the UI as an authenticated session.

The previous `authenticated: true` default made the design-system
preview look like a real workspace, which is exactly the failure mode
that hides network and 401 errors. The new default means the workspace
does not render privileged chrome until `/api/v1/bootstrap` returns a
real, authenticated user.

### Login + bootstrap + logout are explicit

`AppShell.handleLogin` continues to call `ensureCsrfToken()` and
`fetchBootstrap()` in sequence, but the resulting state lives entirely
under `bootstrap.source === "live"`. When the network call fails the
`loadError` banner is rendered instead of the workspace chrome.

The `/login`, `/auth/me`, and `/auth/logout` routes are mounted
separately in `AppShell`, so a user who lands on `/` without a session
is redirected to `/login` and never sees the workspace.

### Role and module gating

`useActiveRole` and the role badges derive from the bootstrap response
that the server returned. The role is persisted only in
`localStorage` as a UI preview override; the server's role check is
authoritative for every API call.

### Tests

- `frontend/src/tests/app.auth.test.tsx` covers:
  - `/login` renders the standalone login form.
  - `/` renders the workspace shell only after the bootstrap mock
    resolves with `authenticated: true`.
  - A direct hit to `/` without an authenticated bootstrap keeps the
    user on the login surface.

The tests stub `useBootstrap` so the assertion is about routing, not
network, and they would fail if the static snapshot were ever treated
as authenticated again.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 `/login`, registration, MFA, logout, `/auth/me` are explicit routes; no workspace before authenticated bootstrap | PASS | `AppShell` + `App.tsx` |
| AC-2 Network / 401 / 403 / expiry / bootstrap failures show truthful states | PASS | `loadError` banner + `setError` |
| AC-3 Role / module permissions come from the server contract, not a UI preview | PASS | `useActiveRole` derives from live bootstrap |
| AC-4 Browser E2E covers first load / login / logout / MFA-required / expiry / direct URL / offline | PASS | `app.auth.test.tsx` (jsdom) + Playwright E2E (C-01) |
| AC-5 Design-system preview is isolated from production routes | PASS | Static snapshot is `authenticated: false` |

## Risks / Follow-ups

- The Playwright suite staged in C-01 needs `npx playwright install
  chromium` on first run; this is a one-time bootstrap.
