# FE-02: i18n system + RTL/LTR

## Discovery

### Status
- `bootstrapSnapshot.company.locale` exists
- `useState<Locale>` in `App.tsx`
- No i18next and no react-intl
- No actual direction toggle

### Fix

#### 1. Add packages

```bash
cd frontend
npm install i18next react-i18next i18next-browser-languagedetector
```

#### 2. Setup

**`src/i18n/index.ts`:**
```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import en from './locales/en.json';
import ar from './locales/ar.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en }, ar: { translation: ar } },
    fallbackLng: 'en',
    supportedLngs: ['en', 'ar'],
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;
```

#### 3. Locales

**`src/i18n/locales/en.json`:**
```json
{
  "nav.dashboard": "Dashboard",
  "nav.tasks": "Tasks",
  "nav.evidence": "Evidence",
  "nav.people": "People",
  "nav.reviews": "Reviews",
  "nav.admin": "Admin",
  "nav.operations": "Operations",
  "common.login": "Login",
  "common.logout": "Logout",
  "common.save": "Save",
  "common.cancel": "Cancel",
  "tasks.title": "Tasks",
  "tasks.completed": "Completed",
  "tasks.overdue": "Overdue",
  "evidence.capture": "Capture Evidence",
  "evidence.retake": "Retake",
  "reviews.queue": "Review Queue",
  "reviews.approve": "Approve",
  "reviews.reject": "Reject"
}
```

**`src/i18n/locales/ar.json`:**
```json
{
  "nav.dashboard": "Dashboard",
  "nav.tasks": "Tasks",
  "nav.evidence": "Evidence",
  "nav.people": "People",
  "nav.reviews": "Reviews",
  "nav.admin": "Admin",
  "nav.operations": "Operations",
  "common.login": "Login",
  "common.logout": "Logout",
  "common.save": "Save",
  "common.cancel": "Cancel",
  "tasks.title": "Tasks",
  "tasks.completed": "Completed",
  "tasks.overdue": "Overdue",
  "evidence.capture": "Capture Evidence",
  "evidence.retake": "Retake",
  "reviews.queue": "Review Queue",
  "reviews.approve": "Approve",
  "reviews.reject": "Reject"
}
```

#### 4. Hook for direction

**`src/hooks/useDirection.ts`:**
```typescript
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export function useDirection() {
  const { i18n } = useTranslation();
  useEffect(() => {
    const dir = i18n.language === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.dir = dir;
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);
  return { dir: i18n.language === 'ar' ? 'rtl' : 'ltr' as const };
}
```

#### 5. Locale switcher component

**`src/components/LocaleSwitcher.tsx`:**
```typescript
import { useTranslation } from 'react-i18next';

export function LocaleSwitcher() {
  const { i18n } = useTranslation();
  return (
    <select
      value={i18n.language}
      onChange={e => i18n.changeLanguage(e.target.value)}
      data-testid="locale-switcher"
    >
      <option value="en">English</option>
      <option value="ar">Arabic</option>
    </select>
  );
}
```

### Acceptance Standards
- AC-1: i18next is configured
- AC-2: en.json and ar.json complete (50+ keys)
- AC-3: dir changes to rtl/ltr
- AC-4: LocaleSwitcher works
- AC-5: E2E test passes
