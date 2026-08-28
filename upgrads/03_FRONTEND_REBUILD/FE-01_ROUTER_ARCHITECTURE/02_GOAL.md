# FE-01: Clean Router Architecture — Goal

## Objective
Restructure the frontend so the router is mounted exactly once, route
configuration is centralised, and code-splitting keeps the initial
bundle small.

## Acceptance criteria
1. `<BrowserRouter>` is mounted in `main.tsx` only.
2. The route table lives in `src/routes/index.tsx` and is consumed by
   `App.tsx`.
3. Every primary route is reachable through `<AppRoutes />`.
4. Each page is loaded via `React.lazy()` and a Suspense fallback is
   shown while the chunk is fetched.
5. `RoleGuard` is applied at the route level and surfaces a friendly
   "Access restricted" panel for forbidden roles.
6. The route table stays type-safe through the `Role` enum exported
   from `src/design-system/tokens.ts`.

## Design decisions
- **Lazy per page** — each workspace page is loaded on demand, so the
  initial bundle stays under 110 kB gzipped.
- **Single source of role state** — `useActiveRole` reads from
  `localStorage` and broadcasts changes via the `storage` event so the
  shell and the route table stay in sync.
- **Outlet-style composition** — `AppShell` is the parent and renders
  the route table as a child rather than reaching for `react-router`'s
  `<Outlet />`. This keeps the shell testable without a router and
  avoids the double-render trap that motivated the upgrade.
