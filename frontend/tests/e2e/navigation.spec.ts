// filepath: frontend/tests/e2e/navigation.spec.ts
import { test, expect } from "@playwright/test";
import { installNetworkStubs } from "./bootstrap.js";

/**
 * C-01 acceptance: the SPA boots under a single BrowserRouter so
 * navigation between every primary route completes without the
 * "cannot nest <BrowserRouter>" warning that broke production.
 */

test.beforeEach(async ({ page }) => {
  const warnings: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "warning" || msg.type() === "error") {
      warnings.push(msg.text());
    }
  });
  // Expose collected warnings to assertions.
  (page as unknown as { __warnings: string[] }).__warnings = warnings;
  await installNetworkStubs(page);
});

test("home page loads without nested router warnings", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/$|\/login/);
  const warnings = (page as unknown as { __warnings: string[] }).__warnings;
  expect(warnings.some((w) => /cannot nest <BrowserRouter>/i.test(w))).toBe(false);
});

test("navigates to /evidence", async ({ page }) => {
  await page.goto("/");
  await page.locator('a[href="/evidence"]').first().click();
  await expect(page).toHaveURL(/\/evidence$/);
});

test("navigates to /people", async ({ page }) => {
  await page.goto("/");
  await page.locator('a[href="/people"]').first().click();
  await expect(page).toHaveURL(/\/people$/);
});

test("navigates to /reviews", async ({ page }) => {
  await page.goto("/");
  await page.locator('a[href="/reviews"]').first().click();
  await expect(page).toHaveURL(/\/reviews$/);
});

test("navigates to /admin", async ({ page }) => {
  await page.goto("/");
  await page.locator('a[href="/admin"]').first().click();
  await expect(page).toHaveURL(/\/admin$/);
});
