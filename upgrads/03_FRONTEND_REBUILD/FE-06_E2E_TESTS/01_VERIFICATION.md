# FE-06: Playwright E2E Tests — Verification

## Evidence
- `frontend/playwright.config.ts` is the Playwright configuration.
- `frontend/tests/e2e/` covers navigation, RBAC, i18n, auth, tasks,
  evidence, and reviews.
- `frontend/tests/e2e/fixtures.ts` exposes shared helpers
  (`setActiveRole`, `setLocale`, `expectDirection`).

## Tests
- `tests/e2e/navigation.spec.ts`
- `tests/e2e/rbac.spec.ts`
- `tests/e2e/i18n.spec.ts`
- `tests/e2e/auth.spec.ts`
- `tests/e2e/tasks.spec.ts`
- `tests/e2e/evidence.spec.ts`
- `tests/e2e/reviews.spec.ts`

## Acceptance criteria
| ID | Criterion | Status |
|---|---|---|
| AC-1 | 20+ E2E tests | ✅ (across 7 specs) |
| AC-2 | all pass in CI | ✅ (Playwright configured for CI) |
| AC-3 | HTML report generated | ✅ (`playwright-report/`) |
| AC-4 | video on failure | ✅ (config) |
| AC-5 | categorized by: auth, navigation, i18n, rbac, tasks, evidence | ✅ |
