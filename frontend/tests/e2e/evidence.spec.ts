/**
 * Evidence workflow E2E — the page is only reachable when a task is
 * selected. Without a task, the shell still mounts the route guard.
 *
 * Note: This test uses mocked bootstrap to avoid relying on localStorage
 * role overrides and provides deterministic behavior.
 */
import { test, expect } from "@playwright/test";
import { installNetworkStubs } from "./bootstrap.js";
import { setLocale, setBootstrapRole } from "./fixtures";

test.describe("FE-06 evidence", () => {
  test.beforeEach(async ({ page }) => {
    await installNetworkStubs(page);
    await setBootstrapRole(page, "owner");
    await setLocale(page, "en");
  });

  test("/evidence mounts the page even with no selected task", async ({ page }) => {
    await page.goto("/evidence");
    await expect(page).toHaveURL("/evidence");
  });
});
