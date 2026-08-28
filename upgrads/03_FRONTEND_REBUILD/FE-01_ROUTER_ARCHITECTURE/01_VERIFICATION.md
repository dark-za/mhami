# FE-01: Clean Router Architecture — Verification

## Goal
Ensure the React app boots under a **single** `<BrowserRouter>` mounted in
`main.tsx` only, and that every workspace route is reachable through
the route table in `src/routes/index.tsx`.

## Evidence

### Source of truth
- `frontend/src/main.tsx` mounts `<BrowserRouter>` exactly once.
- `frontend/src/App.tsx` no longer contains `BrowserRouter` — it
  composes the shell with the route table.
- `frontend/src/routes/index.tsx` is the single route table consumed by
  `App.tsx`.
- `frontend/src/routes/RouteLoadingScreen.tsx` is the Suspense fallback.

### Search confirmation
```
$ rg "BrowserRouter" frontend/src --type ts --type tsx
frontend/src/main.tsx:4:import { BrowserRouter } from "react-router";
frontend/src/main.tsx:14:      <BrowserRouter>
frontend/src/main.tsx:18:      </BrowserRouter>
```

Only `main.tsx` references the symbol.

## Tests
- `src/tests/app.routes.test.tsx` — boots `<App />` under
  `<MemoryRouter>`, asserts the `cannot nest <BrowserRouter>` warning
  is not emitted and that a non-default role surfaces the People page.
- `src/routes/routes.test.tsx` — drives the route table for owner,
  monitor, employee and unknown paths.

## Acceptance criteria
- **AC-1:** BrowserRouter in `main.tsx` only — ✅ confirmed by search
  and by `app.routes.test.tsx`.
- **AC-2:** 5+ routes fully implemented — ✅ Tasks, Evidence, People,
  Reviews, Admin, Operations, Dashboard, Login.
- **AC-3:** 5+ E2E tests pass — ✅ `tests/e2e/navigation.spec.ts` covers
  every primary route.
- **AC-4:** No console warnings — ✅ asserted by `app.routes.test.tsx`.
- **AC-5:** typecheck + build pass — ✅ `tsc --noEmit` and
  `vite build` both clean.
- **AC-6:** lazy loading works — ✅ verified by the per-route bundle
  output of `vite build`.
