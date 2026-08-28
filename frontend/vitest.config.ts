import { defineConfig } from "vitest/config";

/**
 * Vitest configuration. Uses jsdom so the `window`/`document` calls in
 * the test suite resolve correctly. Playwright e2e specs are excluded
 * from the unit-test run and live in `tests/e2e/` with their own
 * configuration in `playwright.config.ts`.
 */
export default defineConfig({
  test: {
    environment: "happy-dom",
    globals: true,
    include: ["src/**/*.test.{ts,tsx}", "src/**/__tests__/**/*.{ts,tsx}"],
    exclude: ["node_modules", "dist", "tests/e2e/**", "**/*.spec.ts"],
    setupFiles: ["./src/tests/setup.ts"],
  },
});
