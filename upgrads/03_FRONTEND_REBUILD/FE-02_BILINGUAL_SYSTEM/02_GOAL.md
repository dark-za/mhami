# FE-02: Bilingual i18n system — Goal

## Objective
Provide a deterministic i18n system with English and Arabic resources,
RTL/LTR direction handling, and an accessible locale switcher so the
shell can serve both audiences from a single bundle.

## Acceptance criteria
1. `i18next` and `react-i18next` are wired in `src/i18n/index.ts`.
2. Locale resources cover `common`, `auth`, `nav`, `shell`, `tasks`,
   `evidence`, `reviews`, `people`, `admin`, `operations`, `errors`.
3. The active locale is persisted in `localStorage` so the choice
   survives page reloads.
4. `useDirection` keeps `document.dir` and `document.lang` in sync.
5. `<LocaleSwitcher />` is rendered in the shell header.
6. E2E specs cover the locale switcher and the direction flip.

## Design decisions
- **No detector plugin** — the `Locale` value is the single source of
  truth and is persisted directly to `localStorage`. This avoids a
  bundle-size hit and prevents the plugin from racing the chip-based
  controls in the shell.
- **i18n + RTL co-located** — `useDirection` is exported from the
  hooks folder so any surface that needs to flip CSS-only layouts (e.g.
  flex direction) can subscribe to the active language.
- **Accessible switcher** — `<LocaleSwitcher />` uses a native
  `<select>` so it is operable through keyboard and screen readers.
