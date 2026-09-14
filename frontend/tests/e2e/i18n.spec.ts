import { test, expect } from "@playwright/test";
import { installNetworkStubs } from "./bootstrap.js";
import { setLocale, setBootstrapRole, expectDirection } from "./fixtures";

/**
 * Locale + direction E2E.
 */

test.describe("FE-06 locale + direction", () => {
  test.beforeEach(async ({ page }) => {
    await installNetworkStubs(page);
    await setBootstrapRole(page, "owner");
  });

  test("default locale is Arabic RTL without explicit selection", async ({ page }) => {
    await page.goto("/");
    await expectDirection(page, "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  });

  test("explicit English locale sets LTR and persists across reloads", async ({ page }) => {
    await setLocale(page, "en");
    await page.goto("/");
    await expectDirection(page, "ltr");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await page.reload();
    await expectDirection(page, "ltr");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
  });

  test("explicit Arabic locale sets RTL and persists across reloads", async ({ page }) => {
    await setLocale(page, "ar");
    await page.goto("/");
    await expectDirection(page, "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
    await page.reload();
    await expectDirection(page, "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  });

  test("LocaleSwitcher toggles direction both ways at runtime and persists", async ({ page }) => {
    // Start from default Arabic RTL
    await page.goto("/");
    await expectDirection(page, "rtl");
    await expect(page.locator('[data-testid="locale-switcher"]')).toHaveValue("ar");

    // Switch to English LTR via real locale switcher
    await page.selectOption('[data-testid="locale-switcher"]', "en");
    await expectDirection(page, "ltr");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await expect(page.locator('[data-testid="locale-switcher"]')).toHaveValue("en");

    // Switch back to Arabic RTL
    await page.selectOption('[data-testid="locale-switcher"]', "ar");
    await expectDirection(page, "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");

    // Verify persistence after reload (should remain Arabic)
    await page.reload();
    await expectDirection(page, "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");

    // Toggle again to English and verify persistence
    await page.selectOption('[data-testid="locale-switcher"]', "en");
    await expectDirection(page, "ltr");
    await page.reload();
    await expectDirection(page, "ltr");
  });
});
