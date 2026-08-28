# FE-03: OpenAPI Types Integration — Verification

## Evidence
- `frontend/src/api/generated-types.ts` is present, auto-generated, and
  contains the workspace-critical paths.
- `frontend/src/api/typed.ts` exposes type-safe wrappers
  (`getTaskInstance`, `listTasks`, `listEvidence`) derived from the
  OpenAPI schema.
- `frontend/src/api/client.ts` is the central `fetch` wrapper that
  drives CSRF and JSON content-type negotiation.
- `frontend/scripts/check-generated-types.mjs` is invoked by the
  `prebuild`, `predev`, and `pretest` scripts in `package.json`.

## Tests
- `src/api/typed.test.ts` — verifies the wrappers call the right
  endpoints, encode query strings, and unwrap the response envelope.

## Acceptance criteria
| ID | Criterion | Status |
|---|---|---|
| AC-1 | generated-types.ts exists and is up to date | ✅ |
| AC-2 | client.ts uses types | ✅ |
| AC-3 | No `any` in components | ✅ (no `any` in `frontend/src`) |
| AC-4 | typecheck passes | ✅ |
| AC-5 | build passes | ✅ |
