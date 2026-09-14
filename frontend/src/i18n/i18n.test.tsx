/**
 * FE-02 acceptance tests for the i18n module and `useDirection` hook.
 *
 * The shared test setup initializes the application i18n singleton before
 * components render, while production initialization remains unchanged.
 */
import { describe, expect, test, beforeEach } from "vitest";
import { act, render } from "@testing-library/react";
import i18n from "./index";
import en from "./locales/en.json";
import ar from "./locales/ar.json";
import { useDirection } from "../hooks/useDirection";

function translationKeys(value: Record<string, unknown>, prefix = ""): string[] {
  return Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return child && typeof child === "object" && !Array.isArray(child)
      ? translationKeys(child as Record<string, unknown>, path)
      : [path];
  });
}

function DirectionProbe() {
  const probe = useDirection();
  return <span data-testid="dir">{probe.dir}</span>;
}

beforeEach(() => {
  localStorage.removeItem("mhami.locale");
  document.documentElement.dir = "ltr";
  document.documentElement.lang = "en";
});

describe("FE-02 i18n + direction", () => {
  test("defaults to Arabic when no persisted locale (initializer config)", () => {
    // No persisted locale: readPersistedLocale() returns null, production init falls back to "ar"
    expect(localStorage.getItem("mhami.locale")).toBeNull();
    // Verify module config without forcing changeLanguage: initializer uses "ar" as lng/fallbackLng
    const fallback = i18n.options.fallbackLng as unknown as string | string[];
    const fallbackIsAr = Array.isArray(fallback) ? fallback.includes("ar") : fallback === "ar";
    expect(fallbackIsAr).toBe(true);
    const configuredLng = (i18n.options as unknown as { lng?: string }).lng ?? (Array.isArray(fallback) ? fallback[0] : (fallback as string));
    expect(configuredLng).toBe("ar");
    expect(i18n.options.supportedLngs).toContain("ar");
    // Also ensure i18n has Arabic resources available
    expect(i18n.hasResourceBundle("ar", "translation")).toBe(true);
  });

  test("changeLanguage persists to localStorage", async () => {
    await act(async () => {
      await i18n.changeLanguage("ar");
    });
    expect(localStorage.getItem("mhami.locale")).toBe("ar");
  });

  test("translations return the expected key set in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });
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

  test("Arabic and English expose the same translation keys", () => {
    expect(translationKeys(ar).sort()).toEqual(translationKeys(en).sort());
  });

  test("useDirection flips document dir/lang for en -> ar -> en", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });
    const { rerender, unmount } = render(<DirectionProbe />);
    expect(document.documentElement.dir).toBe("ltr");
    expect(document.documentElement.lang).toBe("en");
    expect(document.documentElement.lang).toBe("en");

    await act(async () => {
      await i18n.changeLanguage("ar");
    });
    rerender(<DirectionProbe />);
    expect(document.documentElement.dir).toBe("rtl");
    expect(document.documentElement.lang).toBe("ar");

    await act(async () => {
      await i18n.changeLanguage("en");
    });
    rerender(<DirectionProbe />);
    expect(document.documentElement.dir).toBe("ltr");
    expect(document.documentElement.lang).toBe("en");

    unmount();
  });
});
