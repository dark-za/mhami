/**
 * useDirection — sync the document `dir` and `lang` attributes with the
 * active i18n language. Returns a `dir` token that callers can use to flip
 * CSS-only layouts (e.g. flex direction).
 */
import { useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";

export type Direction = "rtl" | "ltr";

export function useDirection(): { dir: Direction; language: string } {
  const { i18n } = useTranslation();
  const language = i18n.resolvedLanguage ?? i18n.language ?? "en";
  const dir: Direction = language.startsWith("ar") ? "rtl" : "ltr";

  useEffect(() => {
    if (typeof document === "undefined") {
      return;
    }
    document.documentElement.dir = dir;
    document.documentElement.lang = language;
  }, [dir, language]);

  return useMemo(() => ({ dir, language }), [dir, language]);
}
