/**
 * FE-02 acceptance tests for the i18n module and `useDirection` hook.
 */
import { describe, expect, test, beforeEach } from "vitest";
import { act, render } from "@testing-library/react";
import i18n from "./index";
import { useDirection } from "../hooks/useDirection";

beforeEach(() => {
  localStorage.removeItem("mhami.locale");
  document.documentElement.dir = "ltr";
  document.documentElement.lang = "en";
  void i18n.changeLanguage("en");
});

function DirectionProbe() {
  const probe = useDirection();
  return <span data-testid="dir">{probe.dir}</span>;
}

describe("FE-02 i18n + direction", () => {
  test("defaults to English when no persisted locale", () => {
    expect(i18n.resolvedLanguage ?? i18n.language).toBe("en");
  });

  test("changeLanguage persists to localStorage", async () => {
    await act(async () => {
      await i18n.changeLanguage("ar");
    });
    expect(localStorage.getItem("mhami.locale")).toBe("ar");
  });

  test("translations return the expected key set in English", () => {
    expect(i18n.t("common.login")).toBe("Sign in");
    expect(i18n.t("nav.tasks")).toBe("Tasks");
    expect(i18n.t("reviews.approve")).toBe("Approve");
  });

  test("translations return the expected key set in Arabic", async () => {
    await act(async () => {
      await i18n.changeLanguage("ar");
    });
    expect(i18n.t("common.login")).toBe("تسجيل الدخول");
    expect(i18n.t("nav.tasks")).toBe("المهام");
    expect(i18n.t("reviews.approve")).toBe("اعتماد");
  });

  test("useDirection flips document dir/lang for Arabic", async () => {
    const { rerender, unmount } = render(<DirectionProbe />);
    expect(document.documentElement.dir).toBe("ltr");

    await act(async () => {
      await i18n.changeLanguage("ar");
    });
    rerender(<DirectionProbe />);
    expect(document.documentElement.dir).toBe("rtl");
    expect(document.documentElement.lang).toBe("ar");

    unmount();
  });
});
