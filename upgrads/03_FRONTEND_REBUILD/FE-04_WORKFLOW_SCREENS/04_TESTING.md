# FE-04: P0/P1 Workflow Screens — Testing

## Unit tests
- `src/components/AsyncState.test.tsx` — verifies the loading, error,
  empty, and child rendering branches.

## E2E tests
- `tests/e2e/auth.spec.ts` — login page renders and the CSRF header is
  sent on submit.
- `tests/e2e/navigation.spec.ts` — every primary route mounts the
  expected surface.
- `tests/e2e/tasks.spec.ts` — Tasks page lifecycle.
- `tests/e2e/evidence.spec.ts` — Evidence route mount.
- `tests/e2e/reviews.spec.ts` — Reviews route mount.

## Manual checklist
- [x] `npm run typecheck` passes
- [x] `npm run test` passes (32 tests, 0 failures)
- [x] `npm run build` succeeds
