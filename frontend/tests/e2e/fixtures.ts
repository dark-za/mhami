/**
 * Shared Playwright helpers. The E2E specs only target the live
 * bootstrap surface so the helpers focus on booting the shell, switching
 * the role, and toggling the locale.
 */
import { expect, type Page, type BrowserContext } from "@playwright/test";

export async function setActiveRole(page: Page, role: "owner" | "monitor" | "employee" | "platform_admin") {
  await page.addInitScript((nextRole) => {
    window.localStorage.setItem("mhami.activeRole", nextRole);
  }, role);
}

export async function setLocale(page: Page, locale: "en" | "ar") {
  await page.addInitScript((nextLocale) => {
    window.localStorage.setItem("mhami.locale", nextLocale);
  }, locale);
}

export async function expectDirection(page: Page, dir: "ltr" | "rtl") {
  await expect(page.locator("html")).toHaveAttribute("dir", dir);
}

export async function gotoShell(context: BrowserContext, path = "/") {
  const page = await context.newPage();
  await page.goto(path);
  return page;
}
