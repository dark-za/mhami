# FE-03: OpenAPI Types Integration — Goal

## Objective
Generate TypeScript types from the Django OpenAPI schema, expose
type-safe wrappers for the workspace endpoints, and ensure CI refuses
to build when the types are stale or missing.

## Acceptance criteria
1. `npm run generate:api` regenerates `src/api/generated-types.ts`.
2. `src/api/typed.ts` exposes wrappers for tasks and evidence.
3. `prebuild`, `predev`, and `pretest` scripts verify the generated
   file is present and exposes the workspace-critical paths.
4. No `any` types are introduced in the source code.
