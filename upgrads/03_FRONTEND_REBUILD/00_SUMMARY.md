# Section 3: Frontend Rebuild

## List of Fixes

| # | Title | Folder | Priority | Duration |
|---|---|---|---|---|
| FE-01 | Clean Router architecture | `FE-01_ROUTER_ARCHITECTURE/` | P0 | 1 week |
| FE-02 | i18n system + RTL/LTR | `FE-02_BILINGUAL_SYSTEM/` | P0 | 1 week |
| FE-03 | OpenAPI Types integration | `FE-03_API_INTEGRATION/` | P0 | 1 week |
| FE-04 | P0/P1 screens | `FE-04_WORKFLOW_SCREENS/` | P0 | 3 weeks |
| FE-05 | CSRF integration in client | `FE-05_CSRF_INTEGRATION/` | P0 | 2 days |
| FE-06 | Playwright E2E | `FE-06_E2E_TESTS/` | P0 | 2 weeks |

## FE-01: Clean Router Architecture (Detail)

### Current State
- `main.tsx:14` and `App.tsx:162` both contain a nested `BrowserRouter`.
- 14 different pages, most of which are placeholders.

### Target
```
src/
├── main.tsx                    # Single BrowserRouter
├── App.tsx                     # <Routes> definitions
├── routes/
│   ├── index.tsx               # Route table
│   ├── public.tsx              # /login, /register
│   ├── workspace.tsx           # authenticated routes
│   └── admin.tsx               # /admin/* (role-gated)
├── pages/
│   ├── auth/
│   ├── tasks/
│   ├── evidence/
│   ├── reviews/
│   ├── people/
│   ├── admin/
│   └── operations/
├── shell/
│   ├── AppShell.tsx            # chrome layout
│   ├── AppErrorBoundary.tsx
│   └── RoleGuard.tsx
└── design-system/
    ├── tokens.ts
    └── i18n.ts
```

### Acceptance Standards
- AC-1: Only one BrowserRouter
- AC-2: At least 5 routes fully implemented
- AC-3: 5 E2E tests pass
- AC-4: No console warnings
- AC-5: typecheck and build pass

## FE-02: i18n system + RTL/LTR (Detail)

### Libraries
- `react-i18next` + `i18next`
- `i18next-browser-languagedetector`

### Structure
```typescript
// src/i18n/index.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import ar from './locales/ar.json';

i18n
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en }, ar: { translation: ar } },
    lng: 'en',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
  });

export default i18n;
```

### Hooks
```typescript
// src/hooks/useDirection.ts
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export function useDirection() {
  const { i18n } = useTranslation();
  useEffect(() => {
    const dir = i18n.language === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.dir = dir;
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);
  return { dir: i18n.language === 'ar' ? 'rtl' : 'ltr' };
}
```

### Locale keys
- `tasks.title`, `tasks.completed`, `tasks.overdue`
- `evidence.upload`, `evidence.retake`
- `reviews.queue`, `reviews.approve`, `reviews.reject`
- `nav.dashboard`, `nav.tasks`, etc.

## FE-03: OpenAPI Types Integration (Detail)

### Tool
- `openapi-typescript` v7

### Scripts
```json
{
  "scripts": {
    "generate:api": "openapi-typescript http://localhost:8000/api/schema/ -o src/api/generated-types.ts",
    "prebuild": "node scripts/check-generated-types.mjs",
    "predev": "node scripts/check-generated-types.mjs"
  }
}
```

### Usage
```typescript
// src/api/client.ts
import type { components } from './generated-types';

type Company = components['schemas']['Company'];
type EvidenceItem = components['schemas']['EvidenceItem'];

export async function listEvidence(taskId: string): Promise<EvidenceItem[]> {
  return api(`/api/v1/evidence/${taskId}/`);
}
```

## FE-04: P0/P1 screens (Detail)

### P0 (Production)
1. Login/Register
2. Bootstrap
3. Role-based navigation
4. Locale switching
5. Calendar preference

### P1 (workflows)
1. Tasks list & detail
2. Evidence capture flow
3. Review queue
4. Notifications

### P2 (admin)
1. People/branch management
2. AI provider config
3. Connector management
4. Exports/Backups UI

## FE-05: CSRF Integration (Covered in C-04)

## FE-06: E2E Tests (Playwright)

### Structure
```
frontend/tests/e2e/
├── auth.spec.ts           # Login, register, MFA
├── navigation.spec.ts     # All routes
├── tasks.spec.ts          # Task workflow
├── evidence.spec.ts       # Capture flow
├── reviews.spec.ts        # Review decisions
├── i18n.spec.ts           # Locale switching
└── rbac.spec.ts           # Role-based access
```

### Success Criteria
- 30+ E2E tests
- All passing in CI
- Coverage of P0 + P1 workflows
