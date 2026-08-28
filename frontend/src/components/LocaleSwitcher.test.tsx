/**
 * LocaleSwitcher acceptance tests for FE-02.
 */
import { describe, expect, test, beforeEach, vi } from "vitest";
import { act, fireEvent, render } from "@testing-library/react";
import i18n from "../i18n";
import { LocaleSwitcher } from "./LocaleSwitcher";

beforeEach(() => {
  localStorage.removeItem("mhami.locale");
  document.documentElement.dir = "ltr";
  document.documentElement.lang = "en";
});

describe("LocaleSwitcher", () => {
  test("defaults to English and offers Arabic as an option", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });
    const { getByTestId } = render(<LocaleSwitcher />);
    const select = getByTestId("locale-switcher") as HTMLSelectElement;
    expect(select.value).toBe("en");
    expect(select.options).toHaveLength(2);
  });

  test("switching to Arabic persists the locale and changes i18n.language", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });
    const { getByTestId } = render(<LocaleSwitcher />);
    const select = getByTestId("locale-switcher") as HTMLSelectElement;
    await act(async () => {
      fireEvent.change(select, { target: { value: "ar" } });
    });
    expect(localStorage.getItem("mhami.locale")).toBe("ar");
    expect((i18n.resolvedLanguage ?? i18n.language) === "ar" || i18n.language === "ar").toBeTruthy();
  });
});
