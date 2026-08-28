/**
 * i18n bootstrap. Mirrors the legacy `Locale` type from
 * `src/design-system/tokens.ts` so existing callers keep working while we
 * migrate surfaces to `useTranslation()`.
 *
 * The implementation avoids the `i18next-browser-languagedetector` plugin to
 * keep the bundle small: the `Locale` value is the single source of truth and
 * is persisted to `localStorage` directly by callers.
 */
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import ar from "./locales/ar.json";

const STORAGE_KEY = "mhami.locale";

function readPersistedLocale(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch (_error) {
    return null;
  }
}

function persistLocale(language: string): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(STORAGE_KEY, language);
  } catch (_error) {
    /* storage may be disabled — fall back silently */
  }
}

void i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ar: { translation: ar },
    },
    lng: readPersistedLocale() ?? "en",
    fallbackLng: "en",
    supportedLngs: ["en", "ar"],
    interpolation: { escapeValue: false },
    returnNull: false,
  });

const originalChangeLanguage = i18n.changeLanguage.bind(i18n);
i18n.changeLanguage = (language: string) => {
  persistLocale(language);
  return originalChangeLanguage(language);
};

export const LOCALE_STORAGE_KEY = STORAGE_KEY;
export default i18n;
