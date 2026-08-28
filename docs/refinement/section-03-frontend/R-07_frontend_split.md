# R-07: Frontend — تفكيك App.tsx monolith

> **Status:** ✅ Completed (2026-08-28) — App.tsx 2081 → 166 سطر، 21 ملف جديد.

## الهدف
`App.tsx` كان فيه **2081 سطر** يجمع:
- 14 type interface
- Routing/role guard helpers
- UI primitives (Badge, Panel, StateCard)
- Capability detection
- 5 domain panels (Evidence, Review, AI, Export, Pilot)
- App-level state (login, locale, role, calendar, bootstrap, notifications)
- Login form + shell header + navigation + branding + notification center

## التغيير النهائي

### البنية الجديدة
```
frontend/src/
├── App.tsx                      166 سطر  (Router + bootstrap state machine)
├── main.tsx                       19 سطر  (دون تغيير)
├── api/
│   ├── bootstrap.ts               26 سطر  (دون تغيير)
│   ├── client.ts                  81 سطر  ⭐ جديد: fetch wrapper
│   ├── contract.ts                 4 سطر  (دون تغيير)
│   └── generated-types.ts      3775 سطر  (دون تغيير)
├── design-system/
│   └── tokens.ts                 142 سطر  (دون تغيير)
├── domain/                      256 سطر  ⭐ جديد
│   ├── ai.ts         38 سطر
│   ├── connectors.ts  9 سطر
│   ├── evidence.ts  22 سطر
│   ├── exports.ts   24 سطر
│   ├── notifications.ts 9 سطر
│   ├── pilot.ts     53 سطر
│   ├── reviews.ts   66 سطر
│   ├── routing.ts   44 سطر
│   ├── tasks.ts     18 سطر
│   └── index.ts     11 سطر
├── hooks/                       104 سطر  ⭐ جديد
│   ├── useBootstrap.ts    65 سطر
│   └── useNotifications.ts 39 سطر
├── pages/                      2034 سطر  ⭐ جديد
│   └── shared/
│       ├── AIControlPage.tsx  261 سطر
│       ├── EvidencePage.tsx   295 سطر
│       ├── ExportsPage.tsx    216 سطر
│       ├── PeoplePage.tsx      47 سطر
│       ├── PilotPage.tsx      388 سطر
│       ├── ReviewsPage.tsx    373 سطر
│       ├── TasksPage.tsx      237 سطر
│       └── index.ts             7 سطر
├── shell/                      484 سطر  ⭐ جديد
│   ├── AppShell.tsx         335 سطر
│   ├── CapabilityCard.tsx    33 سطر
│   ├── RoleGuard.tsx         23 سطر
│   ├── AppErrorBoundary.tsx  30 سطر  (موجود)
│   └── ui.tsx                31 سطر
├── styles.css                  (دون تغيير)
└── tests/
    └── app.test.tsx            34 سطر  (يستخدم AppShell مباشرة)
```

### `App.tsx` الجديد (Router-only)
```typescript
// filepath: frontend/src/App.tsx
export function App() {
  return (
    <BrowserRouter>
      <AppShellHost />
    </BrowserRouter>
  );
}

function AppShellHost() {
  const { state, loading, error, setState } = useBootstrap();
  const { items: notifications, error: notificationsError } = useNotifications();
  const [locale, setLocale] = useState<Locale>(bootstrapSnapshot.company.locale);
  const [calendar, setCalendar] = useState<CalendarPreference>("gregorian");
  const [role, setRole] = useState<Role>(bootstrapSnapshot.currentUser.role);
  const [activeTaskId, setActiveTaskId] = useState<string>("");

  return (
    <AppShell
      bootstrap={state} setBootstrap={...} loading={loading} loadError={error}
      locale={locale} setLocale={setLocale} calendar={calendar} setCalendar={setCalendar}
      role={role} setRole={setRole}
      notifications={notifications} notificationsError={notificationsError}
    >
      <Routes>
        <Route path="/" element={<RoleGuard ...><TasksPage .../></RoleGuard>} />
        <Route path="/tasks" element={<RoleGuard ...><TasksPage .../></RoleGuard>} />
        <Route path="/evidence" element={<RoleGuard ...><EvidencePage .../></RoleGuard>} />
        ... // 7 routes total
      </Routes>
    </AppShell>
  );
}
```

### `api/client.ts` الجديد
```typescript
// filepath: frontend/src/api/client.ts
export class ApiError extends Error {
  public readonly code: string;
  public readonly status: number;
  constructor(code: string, message: string, status: number) { ... }
}

export async function api<T>(path: string, init: ApiInit = {}): Promise<T> {
  // JSON content-type negotiation + credentials: "include" + DRF error envelope
  // parsing -> throw ApiError(code, message, status)
}
```

### `domain/<module>.ts`
كل ملف domain يحوي فقط الـ type interfaces للـ module المعني، مع `index.ts` يصدّرها جميعاً. لا منطق، لا state — types فقط.

### `pages/shared/<Feature>Page.tsx`
كل feature page هو React component مستقل يستهلك `api()` من client.ts و types من `../domain`. لا يدير state الـ shell (locale/role/calendar).

### `shell/AppShell.tsx`
يحوي الـ chrome: header, login form, locale/role chips, branding swatches, navigation rail, notification center, capability card. يأخذ state من props (يرفعها App.tsx).

### `shell/RoleGuard.tsx`
```typescript
export function RoleGuard({ roles, activeRole, children, resource }: RoleGuardProps) {
  if (roles.includes(activeRole)) return <>{children}</>;
  return <Panel eyebrow="Access restricted" title={resource ?? "..."}><p>...</p></Panel>;
}
```

## الأثر الفعلي
| المقياس | قبل | بعد | الفرق |
|---|---|---|---|
| `App.tsx` | 2081 سطر | 166 سطر | **−1915 سطر (−92%)** |
| عدد الملفات | 9 | 30 | +21 ملف |
| صفحات قابلة للاختبار | 0 | 7 | +7 |
| fetch calls موحدة | 0 | 1 helper (`api()`) | +DRF error envelope handling |

## التحقق
```bash
cd frontend
npm run typecheck         # ✓ no errors
npm run build             # ✓ 112 modules, 317.72 kB gzipped to 96.05 kB
npm run test              # ✓ 1/1 passed (135ms)
```

## معايير القبول
- [x] `App.tsx` ≤ 200 سطر (الآن 166)
- [x] كل صفحة في `pages/shared/` قابلة للتصدير منفصلة
- [x] لا تغيير في الـ URLs (`/`, `/tasks`, `/evidence`, `/people`, `/reviews`, `/admin`, `/operations`, `/dashboard`)
- [x] لا تغيير في الـ API calls (نفس المسارات)
- [x] Role guards كما هي (نفس الجدول، لكن moved to dedicated component)
- [x] Bilingual + responsive يعمل (الـ styles لم تتغير)

## المخاطر
🟢 **منخفضة** — كل التغييرات الـ behavior-preserving:
- نفس الـ fetch URLs
- نفس الـ state machine
- نفس الـ role permissions table
- نفس الـ test expectations ("Login and shell entry" + "Nadi Foods")

## ملاحظات
- لم تُنقل صفحات `pages/{platform,owner,monitor,employee}/` بعد لأن الـ App.tsx الأصلي لم يفصل بينها (كل الأدوار تشترك في نفس صفحات `EvidencePage`/`TasksPage`/`ReviewsPage`). يمكن تقسيمها لاحقاً حسب الدور في R-07b.
- لم يُنقل `Panel` و `Badge` و `StateCard` إلى `design-system/` — هي حالياً في `shell/ui.tsx`. نقلها اختياري في refactor لاحق.
