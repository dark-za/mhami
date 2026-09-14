/**
 * Reviews workflow E2E.
 *
 * Note: This test uses mocked bootstrap to avoid relying on localStorage
 * role overrides and provides deterministic behavior.
 */
import { test, expect } from "@playwright/test";
import { installNetworkStubs } from "./bootstrap.js";
import { setLocale, setBootstrapRole } from "./fixtures";

test.describe("FE-06 reviews", () => {
  test.beforeEach(async ({ page }) => {
    await installNetworkStubs(page);
    await setBootstrapRole(page, "monitor");
    await setLocale(page, "en");
  });

  test("/reviews is reachable for monitor role", async ({ page }) => {
    await page.goto("/reviews");
    await expect(page).toHaveURL("/reviews");
  });

  test("owner sees reviews workspace headings and non-empty state labels in English", async ({ page }) => {
    await setBootstrapRole(page, "owner");
    await setLocale(page, "en");
    await page.goto("/reviews");
    await expect(page).toHaveURL("/reviews");
    await expect(page.getByRole("heading", { name: "Queue, policy, and AI criteria" })).toBeVisible();
    await expect(page.getByText("Queue, policy, and AI criteria").first()).toBeVisible();
    // Non-empty state labels
    await expect(page.getByText("The review queue is empty.")).toBeVisible();
    await expect(page.getByText("Score visibility", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Save review policy" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Create criteria version" })).toBeVisible();
  });

  test("owner sees reviews workspace headings and labels in Arabic (RTL)", async ({ page }) => {
    await setBootstrapRole(page, "owner");
    await setLocale(page, "ar");
    await page.goto("/reviews");
    await expect(page).toHaveURL("/reviews");
    await expect(page.getByRole("heading", { name: "قائمة المراجعة والسياسات ومعايير الذكاء الاصطناعي" })).toBeVisible();
    // Non-empty state labels in Arabic (empty queue)
    await expect(page.getByText("قائمة المراجعة فارغة.")).toBeVisible();
    await expect(page.getByText("عرض الدرجة", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "حفظ سياسة المراجعة" })).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  });
});
