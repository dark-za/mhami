# FE-02: Bilingual i18n system — Testing

## Unit tests
- `src/i18n/i18n.test.tsx` — verifies the i18n module, key coverage in
  English and Arabic, `localStorage` persistence, and the `useDirection`
  hook flips `document.dir`/`document.lang` correctly.
- `src/components/LocaleSwitcher.test.tsx` — verifies the switcher
  defaults to English and persists the chosen locale.

## E2E tests
- `tests/e2e/i18n.spec.ts` — verifies the English locale sets LTR, the
  Arabic locale sets RTL (and persists across reloads), and the
  `LocaleSwitcher` flips direction at runtime.

## Manual checklist
- [x] `npm run typecheck` passes
- [x] `npm run test` passes (32 tests, 0 failures)
- [x] `npm run build` succeeds
- [x] `npm run test:e2e` covers the locale flip
