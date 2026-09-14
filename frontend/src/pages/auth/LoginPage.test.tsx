/**
 * LoginPage locale switcher — defect 1.
 * Verifies unauthenticated Login screen exposes the existing LocaleSwitcher
 * without a duplicate router/shell and with accessible placement.
 */
import { describe, expect, test, beforeEach } from "vitest";
import { act, render } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import i18n from "../../i18n";
import LoginPage from "./LoginPage";

beforeEach(async () => {
  await act(async () => {
    await i18n.changeLanguage("ar");
  });
});

describe("LoginPage locale switcher", () => {
  test("renders the locale switcher inside the unauthenticated login page", async () => {
    let result: any = null;
    await act(async () => {
      result = render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>,
      );
    });
    if (!result) throw new Error("render failed");
    const { getByTestId, container } = result;
    const select = getByTestId("locale-switcher") as HTMLSelectElement;
    expect(select).toBeTruthy();
    expect(select.value).toBe("ar");
    // Accessible placement: switcher lives inside .login-page and .login-locale-switcher
    expect(container.querySelector(".login-page .login-locale-switcher")).toBeTruthy();
    expect(container.querySelector(".login-page .login-locale-switcher .locale-switcher")).toBeTruthy();
  });

  test("does not mount a nested BrowserRouter/AppShell duplicate", async () => {
    let result: any = null;
    await act(async () => {
      result = render(
        <MemoryRouter initialEntries={["/login"]}>
          <LoginPage />
        </MemoryRouter>,
      );
    });
    if (!result) throw new Error("render failed");
    // Only one locale switcher, no AppShell header
    expect(result.container.querySelectorAll('[data-testid="locale-switcher"]')).toHaveLength(1);
    expect(result.container.textContent ?? "").not.toContain("Role-aware navigation");
  });
});
