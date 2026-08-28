/**
 * LocaleSwitcher — accessible control that flips the active language and
 * (transitively via `useDirection`) the document `dir` attribute.
 *
 * Uses native `<option>` elements so it works without a popover layer and
 * remains operable through keyboard and screen readers.
 */
import { useTranslation } from "react-i18next";
import type { ChangeEvent } from "react";

const LANGUAGES: Array<{ code: string; label: string }> = [
  { code: "en", label: "English" },
  { code: "ar", label: "العربية" },
];

export interface LocaleSwitcherProps {
  testId?: string;
}

export function LocaleSwitcher({ testId = "locale-switcher" }: LocaleSwitcherProps) {
  const { i18n, t } = useTranslation();
  const current = (i18n.resolvedLanguage ?? i18n.language ?? "en").startsWith("ar") ? "ar" : "en";

  const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    void i18n.changeLanguage(event.target.value);
  };

  return (
    <label className="locale-switcher">
      <span className="visually-hidden">{t("common.language")}</span>
      <select data-testid={testId} value={current} onChange={handleChange}>
        {LANGUAGES.map((language) => (
          <option key={language.code} value={language.code}>
            {language.label}
          </option>
        ))}
      </select>
    </label>
  );
}
