import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { act, render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { App } from "../App";
import { createFallbackState } from "../api/bootstrap";
import { bootstrapSnapshot } from "../design-system/tokens";
import type { Role } from "../design-system/tokens";

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

beforeEach(() => {
  // Default to owner so the / route does not trip the RoleGuard.
  window.localStorage.removeItem("mhami.activeRole");
});

afterEach(() => {
  vi.clearAllMocks();
  window.localStorage.removeItem("mhami.activeRole");
});

describe("C-01 unified BrowserRouter (FE-01)", () => {
  test("App renders without nested router warning and exposes primary route", async () => {
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
      expect(document.body.textContent ?? "").toMatch(/Tasks|Task|Mhami/i);
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

  test("App supports a non-default role via localStorage and renders People page", async () => {
    window.localStorage.setItem("mhami.activeRole", "monitor" satisfies Role);
    await act(async () => {
      render(
        <MemoryRouter initialEntries={["/people"]}>
          <App />
        </MemoryRouter>,
      );
    });
    await waitFor(() => {
      expect(document.body.textContent ?? "").toMatch(/People|Roster|Branch/);
    });
  });
});
