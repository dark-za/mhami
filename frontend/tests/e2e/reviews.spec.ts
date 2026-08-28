/**
 * Reviews workflow E2E.
 */
import { test, expect } from "@playwright/test";
import { setActiveRole, setLocale } from "./fixtures";

test.describe("FE-06 reviews", () => {
  test.beforeEach(async ({ page }) => {
    await setActiveRole(page, "monitor");
    await setLocale(page, "en");
  });

  test("/reviews is reachable for monitor role", async ({ page }) => {
    await page.goto("/reviews");
    await expect(page).toHaveURL("/reviews");
  });
});
