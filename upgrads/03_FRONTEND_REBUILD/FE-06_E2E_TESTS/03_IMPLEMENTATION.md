# FE-06: Playwright E2E Tests — Implementation

## Files added
- `frontend/playwright.config.ts`
- `frontend/tests/e2e/fixtures.ts`
- `frontend/tests/e2e/navigation.spec.ts`
- `frontend/tests/e2e/rbac.spec.ts`
- `frontend/tests/e2e/i18n.spec.ts`
- `frontend/tests/e2e/auth.spec.ts`
- `frontend/tests/e2e/tasks.spec.ts`
- `frontend/tests/e2e/evidence.spec.ts`
- `frontend/tests/e2e/reviews.spec.ts`
- `frontend/tests/e2e/README.md`

## Files changed
- `frontend/package.json` — `test:e2e` and `test:e2e:ui` scripts.

## Approach
1. `playwright.config.ts` boots the Vite dev server and targets
   chromium on a desktop viewport.
2. The `fixtures.ts` module exposes helpers that pre-seed
   `localStorage` with the active role and locale.
3. Each spec focuses on a single concern (navigation, RBAC, i18n,
   auth, tasks, evidence, reviews) so failures are easy to triage.
