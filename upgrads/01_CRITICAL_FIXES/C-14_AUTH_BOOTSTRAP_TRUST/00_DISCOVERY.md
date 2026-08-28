# C-14: Establish Trusted Authentication and Bootstrap State

## Discovery

The frontend can render a demo owner snapshot when bootstrap fails, derives the
role from local state, and redirects `/login` to the workspace:

- `frontend/src/hooks/useBootstrap.ts`
- `frontend/src/App.tsx:36-38,57`
- `frontend/src/shell/AppShell.tsx`

This makes authorization UX unreliable and hides session/network failures.

## Goal

Separate public authentication from the authenticated workspace so all visible
roles, modules, and actions derive from a live server session.

## Acceptance Criteria

1. `/login`, registration, MFA enrollment, logout, and `/auth/me` have explicit
   routes and no workspace is rendered before authenticated bootstrap succeeds.
2. Network, 401, 403, expiry, and bootstrap failures show truthful states, not
   demo data.
3. Role/module permissions come from the server contract and cannot be changed
   by a UI preview control.
4. Browser E2E covers first load, login, logout, MFA-required user, session
   expiry, direct URL access, and offline/bootstrap failure.
5. The design-system preview is isolated from production routes.

## Required Evidence

- Browser recording or E2E artifact for each authentication state.
- Frontend and Security reviewer approval.
