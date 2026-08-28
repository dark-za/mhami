/**
 * Evidence workflow E2E — the page is only reachable when a task is
 * selected. Without a task, the shell still mounts the route guard.
 */
import { test, expect } from "@playwright/test";
import { setActiveRole, setLocale } from "./fixtures";

test.describe("FE-06 evidence", () => {
  test.beforeEach(async ({ page }) => {
    await setActiveRole(page, "owner");
    await setLocale(page, "en");
  });

  test("/evidence mounts the page even with no selected task", async ({ page }) => {
    await page.goto("/evidence");
    await expect(page).toHaveURL("/evidence");
  });
});
