# FE-02: i18n system + RTL/LTR — Verification

## Evidence
- `frontend/src/i18n/index.ts` — `i18next` initialised with English and
  Arabic resources.
- `frontend/src/i18n/locales/en.json` and `ar.json` — 50+ keys across
  `common`, `auth`, `nav`, `shell`, `tasks`, `evidence`, `reviews`,
  `people`, `admin`, `operations`, `errors`.
- `frontend/src/hooks/useDirection.ts` — syncs `document.dir` and
  `document.lang` with the active i18n language.
- `frontend/src/components/LocaleSwitcher.tsx` — accessible control
  surfaced in the shell header.

## Tests
- `src/i18n/i18n.test.tsx` — verifies the i18n module, translation keys,
  `localStorage` persistence, and the `useDirection` hook.
- `src/components/LocaleSwitcher.test.tsx` — verifies the switcher
  defaults to English and persists the chosen locale.

## Acceptance criteria
| ID | Criterion | Status |
|---|---|---|
| AC-1 | i18next is configured | ✅ |
| AC-2 | en.json and ar.json complete (50+ keys) | ✅ (50+ keys each) |
| AC-3 | dir changes to rtl/ltr | ✅ (`useDirection` test) |
| AC-4 | LocaleSwitcher works | ✅ |
| AC-5 | E2E test passes | ✅ (`tests/e2e/i18n.spec.ts`) |
