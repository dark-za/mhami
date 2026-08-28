#!/usr/bin/env node
// Verify that `src/api/generated-types.ts` exists and exposes the
// workspace-critical endpoints. A more thorough freshness check
// (comparing mtimes against backend serializer/view files) is too
// brittle in dev because backend changes do not always alter the schema.
//
// In CI, a dedicated step runs `openapi-typescript` against a live API
// container and asserts the generated file is up to date. Locally,
// developers regenerate by running `npm run generate:api` after pulling.

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const GENERATED = resolve(HERE, "..", "src", "api", "generated-types.ts");

const REQUIRED_PATHS = [
  "/api/v1/bootstrap",
  "/api/v1/auth/login",
  "/api/v1/auth/register",
  "/api/v1/tasks/instances",
  "/api/v1/evidence/submit",
  "/api/v1/reviews/queue",
  "/api/v1/reviews/dashboard",
  "/api/v1/notifications/",
];

if (!existsSync(GENERATED)) {
  console.error(
    "src/api/generated-types.ts is missing. Run `npm run generate:api`.",
  );
  process.exit(1);
}

const content = readFileSync(GENERATED, "utf8");
const missing = REQUIRED_PATHS.filter((path) => !content.includes(`"${path}":`));
if (missing.length > 0) {
  console.error(
    `src/api/generated-types.ts is missing the following paths:\n  - ${missing.join("\n  - ")}\n` +
      `Regenerate the types by running \`npm run generate:api\`.`,
  );
  process.exit(1);
}

console.log("Generated types file is present and includes the workspace paths.");
