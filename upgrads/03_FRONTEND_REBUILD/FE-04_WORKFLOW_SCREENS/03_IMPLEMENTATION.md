# FE-04: P0/P1 Workflow Screens — Implementation

## Files added
- `frontend/src/components/AsyncState.tsx` — composable
  loading/error/empty surface.
- `frontend/src/components/AsyncState.test.tsx` — unit tests.
- `frontend/src/pages/auth/LoginPage.tsx` — standalone login surface
  wired to the lazy `/login` route.

## Files changed
- `frontend/src/routes/index.tsx` — uses the new `LoginPage` for the
  public route.

## Approach
1. `AsyncState` is the canonical loading/error/empty surface; every
   page surfaces a similar look-and-feel through this component.
2. `LoginPage` is the standalone login surface used by the lazy
   `/login` route. The shell still ships the inline login form for the
   unauthenticated chrome.
3. Every P0/P1 page is reachable through the route table and exposes
   ARIA attributes for screen readers.
