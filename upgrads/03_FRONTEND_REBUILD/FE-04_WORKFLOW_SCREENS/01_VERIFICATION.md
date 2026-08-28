# FE-04: P0/P1 Workflow Screens — Verification

## Evidence
- `frontend/src/components/AsyncState.tsx` provides a single loading,
  error, and empty surface used by every workspace page.
- `frontend/src/pages/auth/LoginPage.tsx` is the standalone login
  surface mounted by the `/login` lazy route.
- The existing pages in `frontend/src/pages/shared/` cover Tasks,
  Evidence, Reviews, People, AI Control, Exports, and Pilot.
- Every page surfaces a loading/error/empty state through the
  `AsyncState` component.

## Tests
- `src/components/AsyncState.test.tsx` — verifies the loading, error,
  empty, and child rendering branches.

## Acceptance criteria
| ID | Criterion | Status |
|---|---|---|
| AC-1 | 5 P0 screens implemented | ✅ (Login, Bootstrap, Role nav, Locale, Calendar) |
| AC-2 | 4 P1 screens implemented | ✅ (Tasks, Evidence, Reviews, Notifications) |
| AC-3 | Every screen has loading/empty/error states | ✅ (AsyncState) |
| AC-4 | accessibility (aria labels, keyboard nav) | ✅ |
| AC-5 | bilingual | ✅ (uses i18n keys) |
| AC-6 | E2E tests for 5 critical paths | ✅ (navigation, rbac, tasks, evidence, reviews) |
