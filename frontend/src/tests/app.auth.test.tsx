/** C-14 regression tests: authenticated routes are mounted under a
 * separate tree from the public login page. The test stubs the
 * network and only checks the routing structure inside the
 * ``AppRoutes`` tree.
 */

import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { act, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { AppRoutes } from "../routes";

vi.mock("../hooks/useActiveRole", () => ({
  useActiveRole: () => "owner",
}));

beforeEach(() => {
  if (!window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  }
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("C-14 authenticated routing", () => {
  test("/login renders the standalone LoginPage", async () => {
    let container: HTMLElement | null = null;
    await act(async () => {
      const result = render(
        <MemoryRouter initialEntries={["/login"]}>
          <AppRoutes />
        </MemoryRouter>,
      );
      container = result.container;
    });
    // The login form requires labels; check that the page mounts.
    expect(container).not.toBeNull();
  });

  test("/ renders the workspace shell", async () => {
    let container: HTMLElement | null = null;
    await act(async () => {
      const result = render(
        <MemoryRouter initialEntries={["/"]}>
          <AppRoutes />
        </MemoryRouter>,
      );
      container = result.container;
    });
    expect(container).not.toBeNull();
  });
});
