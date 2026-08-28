# FE-01: Clean Router Architecture — Implementation

## Files added
- `frontend/src/routes/index.tsx` — single route table consumed by
  `App.tsx`.
- `frontend/src/routes/RouteLoadingScreen.tsx` — Suspense fallback.
- `frontend/src/hooks/useActiveRole.ts` — single source of role state.
- `frontend/src/pages/auth/LoginPage.tsx` — standalone login surface
  used by the `/login` lazy route.
- `frontend/src/pages/{tasks,evidence,reviews,people,admin,operations}/*.tsx`
  — lazy-loaded re-exports of the canonical pages in `pages/shared/`.

## Files changed
- `frontend/src/App.tsx` — removed the inline `<Routes>` block and
  delegates to `<AppRoutes />`.
- `frontend/src/shell/AppShell.tsx` — `role` and `setRole` props were
  removed; the shell now uses `useActiveRole()` internally.
- `frontend/src/tests/app.test.tsx` — `setRole` prop removed.
- `frontend/src/tests/app.routes.test.tsx` — wraps `<App />` in a
  `<MemoryRouter>` so the test boots under a single router.
- `frontend/src/tests/app.auth.test.tsx` — `useBootstrap` mock now
  returns a full snapshot so the shell renders the header.
- `frontend/vitest.config.ts` — uses `happy-dom` and excludes the
  Playwright specs.
- `frontend/src/tests/setup.ts` — `matchMedia` and observer polyfills.
- `frontend/package.json` — added `i18next`, `react-i18next`,
  `@playwright/test`, `@testing-library/*`, `happy-dom`, `jsdom`.

## Approach
1. The route table in `src/routes/index.tsx` exposes an
   `<AppRoutes />` component that takes the same props the shell
   previously inlined (`activeTaskId`, `activeLocale`, `bootstrap`).
2. Each page is loaded via `React.lazy()` and the route is wrapped in
   a Suspense boundary with a `RouteLoadingScreen` fallback.
3. `RoleGuard` is applied at the route level so the route table is the
   single source of truth for the workspace surface area.
4. The shell no longer owns role state — `useActiveRole` reads
   `localStorage` and broadcasts changes via the `storage` event.
