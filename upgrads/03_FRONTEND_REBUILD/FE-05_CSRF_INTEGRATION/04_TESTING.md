# FE-05: CSRF Integration — Testing

## Unit tests
- `src/api/client.test.ts` — verifies the cookie read, the
  `ensureCsrfToken` flow, the `X-CSRFToken` header on unsafe
  methods, the lack of the header on safe methods, the
  `ApiError` thrown on 4xx responses, and the
  `credentials: "include"` flag.

## E2E tests
- `tests/e2e/auth.spec.ts` — verifies the login page renders and the
  `X-CSRFToken` header is sent on submit (when a backend is
  available).

## Manual checklist
- [x] `npm run typecheck` passes
- [x] `npm run test` passes (32 tests, 0 failures)
- [x] `npm run build` succeeds
