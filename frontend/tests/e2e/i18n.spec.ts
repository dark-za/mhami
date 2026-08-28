/**
 * Locale + direction E2E.
 */
import { test, expect } from "@playwright/test";
import { setActiveRole, setLocale, expectDirection } from "./fixtures";

test.describe("FE-06 locale + direction", () => {
  test.beforeEach(async ({ page }) => {
    await setActiveRole(page, "owner");
  });

  test("English locale sets LTR", async ({ page }) => {
    await setLocale(page, "en");
    await page.goto("/");
    await expectDirection(page, "ltr");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
  });

  test("Arabic locale sets RTL and persists across reloads", async ({ page }) => {
    await setLocale(page, "ar");
    await page.goto("/");
    await expectDirection(page, "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
    await page.reload();
    await expectDirection(page, "rtl");
  });

  test("LocaleSwitcher toggles direction at runtime", async ({ page }) => {
    await page.goto("/");
    await expectDirection(page, "ltr");
    await page.selectOption('[data-testid="locale-switcher"]', "ar");
    await expectDirection(page, "rtl");
    await page.selectOption('[data-testid="locale-switcher"]', "en");
    await expectDirection(page, "ltr");
  });
});
