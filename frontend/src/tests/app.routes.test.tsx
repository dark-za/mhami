import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { act, render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { App } from "../App";
import { createFallbackState } from "../api/bootstrap";
import { bootstrapSnapshot } from "../design-system/tokens";
import type { Role } from "../design-system/tokens";
import i18n from "../i18n";

vi.mock("../hooks/useBootstrap", () => ({
  useBootstrap: () => ({
    state: createFallbackState(bootstrapSnapshot),
    loading: false,
    error: null,
    setState: () => undefined,
  }),
}));

vi.mock("../hooks/useNotifications", () => ({
  useNotifications: () => ({ items: null, error: false }),
}));

beforeEach(async () => {
  // Default to owner so the / route does not trip the RoleGuard.
  window.localStorage.removeItem("mhami.activeRole");
  await i18n.changeLanguage("ar");
});

afterEach(() => {
  vi.clearAllMocks();
  window.localStorage.removeItem("mhami.activeRole");
});

describe("C-01 unified BrowserRouter (FE-01)", () => {
  test("App renders without nested router warning and fails closed before authentication", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const error = vi.spyOn(console, "error").mockImplementation(() => undefined);

    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/"]}>
          <App />
        </MemoryRouter>,
      );
    });

    await waitFor(() => {
      expect(document.body.textContent ?? "").toContain("تسجيل الدخول إلى مساحة العمل");
    });

    const nestedRouterWarning = warn.mock.calls
      .concat(error.mock.calls)
      .some((args) =>
        args.some(
          (arg) =>
            typeof arg === "string" &&
            /cannot nest <BrowserRouter>|nested <BrowserRouter>/i.test(arg),
        ),
      );
    expect(nestedRouterWarning).toBe(false);

    warn.mockRestore();
    error.mockRestore();
  });

  test("App does not let a development role preview expose People before authentication", async () => {
    window.localStorage.setItem("mhami.activeRole", "monitor" satisfies Role);
    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/people"]}>
          <App />
        </MemoryRouter>,
      );
    });
    await waitFor(() => {
      expect(document.body.textContent ?? "").toContain("تسجيل الدخول إلى مساحة العمل");
    });
  });
});
