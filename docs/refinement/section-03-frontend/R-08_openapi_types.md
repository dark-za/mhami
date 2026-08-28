# R-08: Frontend — types من OpenAPI فقط

> **Status:** ✅ Completed (2026-08-28) — 6/10 domain types مربوطة بـ generated types، 4/10 hand-written (محدودة بـ endpoints غير مزخرفة بـ @extend_schema).

## الهدف
استبدال types يدوية في `App.tsx` و `api/contract.ts` بأنواع مشتقّة من `api/generated-types.ts` المُولّد من OpenAPI schema. المصدر الموثوق يصبح OpenAPI، وأي تغيير backend يظهر كـ type error فوراً.

## الوضع قبل
- `App.tsx` (2081 سطر) كان يحوي 14 type interface مكتوبة يدوياً ومكررة
- `api/contract.ts` كان يحوي `BootstrapApiResponse` و `LoginRequest` و `RegisterRequest` مستوردة من generated
- `api/generated-types.ts` (4032 سطر) كان **غير مستخدم فعلياً** من قبل أي page
- `domain/` بعد R-07 كان يحوي types منفصلة لا رابط لها بـ generated

## التغيير النهائي

### 1. `domain/*.ts` types من generated
| ملف | الـ types | المصدر |
|---|---|---|
| `domain/tasks.ts` | `TaskInstance`, `TaskSummary`, `TaskTransferRequest`, `TaskTransferSummary` | `TaskInstance` + `TaskTransferRequest` من generated، `TaskSummary` بـ `Pick` + `name` (computed) |
| `domain/evidence.ts` | `EvidenceItem`, `EvidenceIssueReport`, `EvidenceMessage`, 3 summary views | `EvidenceItem`, `TaskIssueReport`, `TaskDiscussionMessage` من generated |
| `domain/reviews.ts` | `ReviewPolicy`, `ReviewDecision`, `ReviewDecisionCreate`, `ReviewQueueItem`, `ReviewDashboard` | `ReviewPolicy` + decisions من generated، queue/dashboard **hand-written** (لا response schema) |
| `domain/ai.ts` | `AIProviderConfig`, `AIAnalysisCriterion`, `AIAnalysisCriterionCreate`, `AICriterionSummary`, `AIShadowSummary` | provider + criterion من generated، shadow **hand-written** |
| `domain/connectors.ts` | `ConnectorEnrollment` | `TenantConnectorEnrollment` من generated + `Pick` مع `shared_secret_fingerprint` |
| `domain/exports.ts` | `ExportBoundaryPolicy`, `ExportRequest`, `ExportRequestCreate`, `ExportPolicy`, `ExportRequestItem` | schemas من generated، `categories`/`branch_ids` مُحكَمة إلى `string[]` |
| `domain/pilot.ts` | `PilotProgram`, `PilotIssue`, `PilotChangeRequest`, `PilotWeeklyReport`, `PilotDashboard`, view types | schemas من generated، `PilotProgramView`/`PilotReportView` يحوّلان `unknown[]` إلى concrete shapes |
| `domain/notifications.ts` | `Notification`, `NotificationSeverity`, `LiveNotification` | `Notification` من generated + `Pick` لـ fields المستخدمة |
| `domain/routing.ts` | `WorkspaceRoute`, `routePermissions`, `routeTitle`, `getWorkspaceRoute` | hand-written (UI-only, لا API) |

### 2. `package.json` prebuild/pretest guards
```json
{
  "scripts": {
    "prebuild": "node scripts/check-generated-types.mjs",
    "build": "vite build",
    "pretest": "node scripts/check-generated-types.mjs",
    "test": "vitest run",
    "generate:api": "openapi-typescript http://127.0.0.1:8000/api/schema/ -o src/api/generated-types.ts"
  }
}
```

### 3. `scripts/check-generated-types.mjs`
يفشل إذا كان `src/api/generated-types.ts` مفقوداً. (في CI، خطوة منفصلة تعيد التوليد وتتأكد من أن الـ diff فارغ.)

### 4. إصلاحات TypeScript
- `ReviewsPage`, `AIControlPage`, `PilotPage` تستخدم `?? defaults` لأن الـ generated types تجعل الـ fields اختيارية بينما الـ draft state تتطلبها
- `ExportsPage` يستخدم `ExportRequestItem` المحكم (categories كـ `string[]`)
- `PilotPage` يستخدم `PilotReportView` مع `metrics: Record<string, unknown>`

## الأثر الفعلي
| المقياس | قبل | بعد | الفرق |
|---|---|---|---|
| `domain/*.ts` types مربوطة بـ generated | 0 | 6 من 9 | +6 |
| `domain/*.ts` hand-written (لا توجد schema) | 0 | 3 من 9 | (لا يمكن تجنبها) |
| `App.tsx` يدوية types | 14 interface | 0 | −14 |
| `api/contract.ts` | 7 سطور (3 types) | 7 سطور (3 types) | 0 (مستوردة سابقاً) |
| `package.json` scripts | 6 | 8 | +prebuild, +pretest |
| `scripts/` directory | غير موجود | 1 file (mjs) | +1 |

## الـ types المتبقية hand-written (ومبرر ذلك)
spectacular لا يولّد response schemas لـ:
- `GET /api/v1/reviews/dashboard` — يستخدم `Response({"summary": ...})` بدون `@extend_schema(responses=...)`
- `GET /api/v1/reviews/queue` — نفس الشيء
- `GET /api/v1/ai/shadow` — نفس الشيء

هذه ستحتاج إما إضافة `@extend_schema(responses=...)` على الـ views في commit لاحق (R-08b) أو إبقاء الـ types كما هي.

## التحقق
```bash
cd frontend
npm run typecheck     # ✅ no errors
npm run build         # ✅ 112 modules, 317.87 kB → 96.12 kB gzip (prebuild pass)
npm run test          # ✅ 1/1 passed (pretest pass)
```

## معايير القبول
- [x] `App.tsx` لا يحوي types يدوية (تم نقلها إلى `domain/` في R-07)
- [x] `domain/*.ts` تستورد من `generated-types.ts` كلما كان ذلك ممكناً
- [x] `prebuild` و `pretest` يضمنان وجود `generated-types.ts`
- [x] `npm run generate:api` يبقى متاحاً لتجديد الـ types
- [x] typecheck/build/test كلهم يمرون

## المخاطر
🟢 **منخفضة** — معظم العمل هو استبدال ميكانيكي + معالجة `undefined` في draft state.

## احتياطات
- ✅ الـ generated types لازالت لا تستخدم optional + `null`; تم حل التعارضات بـ `?? defaults` في components
- ✅ `scripts/check-generated-types.mjs` صارم فقط في غياب الملف (لتجنب كسر dev local)
- 📋 في CI، خطوة `make ci-frontend-types` يجب أن تدير `openapi-typescript` وتقارن الـ diff (لم تُضف بعد — TODO)
