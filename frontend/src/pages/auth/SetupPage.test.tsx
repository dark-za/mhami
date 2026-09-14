/**
 * SetupPage locale switcher — defect 1.
 */
import { describe, expect, test, beforeEach } from "vitest";
import { act, render } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import i18n from "../../i18n";
import SetupPage from "./SetupPage";

beforeEach(async () => {
  await act(async () => {
    await i18n.changeLanguage("ar");
  });
});

describe("SetupPage locale switcher", () => {
  test("renders the locale switcher inside the unauthenticated setup page", async () => {
    let result: any = null;
    await act(async () => {
      result = render(
        <MemoryRouter>
          <SetupPage />
        </MemoryRouter>,
      );
    });
    if (!result) throw new Error("render failed");
    const { getByTestId, container } = result;
    const select = getByTestId("locale-switcher") as HTMLSelectElement;
    expect(select).toBeTruthy();
    expect(container.querySelector(".login-page .login-locale-switcher")).toBeTruthy();
  });

  test("setup page exposes English persistence via the switcher", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });
    let result: any = null;
    await act(async () => {
      result = render(
        <MemoryRouter>
          <SetupPage />
        </MemoryRouter>,
      );
    });
    if (!result) throw new Error("render failed");
    const select = result.getByTestId("locale-switcher") as HTMLSelectElement;
    expect(select.value).toBe("en");
  });
});
