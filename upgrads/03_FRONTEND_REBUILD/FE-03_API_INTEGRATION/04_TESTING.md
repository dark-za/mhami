# FE-03: OpenAPI Types Integration — Testing

## Unit tests
- `src/api/typed.test.ts` — verifies the wrappers call the right
  endpoints, encode query strings, and unwrap the response envelope.

## Manual checklist
- [x] `npm run typecheck` passes
- [x] `npm run test` passes (32 tests, 0 failures)
- [x] `npm run build` succeeds
- [x] `node scripts/check-generated-types.mjs` exits 0
