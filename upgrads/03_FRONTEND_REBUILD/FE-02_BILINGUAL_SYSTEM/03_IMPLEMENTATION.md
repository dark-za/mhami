# FE-02: Bilingual i18n system — Implementation

## Files added
- `frontend/src/i18n/index.ts`
- `frontend/src/i18n/locales/en.json`
- `frontend/src/i18n/locales/ar.json`
- `frontend/src/hooks/useDirection.ts`
- `frontend/src/components/LocaleSwitcher.tsx`
- `frontend/src/i18n/i18n.test.tsx`
- `frontend/src/components/LocaleSwitcher.test.tsx`

## Files changed
- `frontend/src/main.tsx` — imports `./i18n` so the module is
  initialised at boot.
- `frontend/src/shell/AppShell.tsx` — calls `useDirection()` and keeps
  i18n aligned with the prop-driven `locale` so the chip controls and
  the switcher stay in sync. Renders `<LocaleSwitcher />` in the header.

## Approach
1. `i18n/index.ts` initialises `i18next` with the `en` and `ar`
   resources and overrides `changeLanguage` to persist the choice to
   `localStorage`.
2. `useDirection` is a tiny hook that mutates the `dir` and `lang`
   attributes whenever the active language changes.
3. `<LocaleSwitcher />` is an accessible `<select>` that wraps
   `i18n.changeLanguage` so the rest of the shell reacts through the
   `useTranslation` hook.
4. The shell calls `useDirection` and keeps `i18n.changeLanguage` in
   sync with the prop-driven `locale` so the chip controls continue to
   work alongside the new switcher.
