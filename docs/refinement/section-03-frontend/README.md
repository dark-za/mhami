# القسم الثالث: الواجهة الأمامية (Frontend)

> **المراحل:** R-07 → R-08
> **المدة المقدرة:** 2-3 أيام
> **الأثر:** ~−1,000 سطر (App.tsx: 800 → 50)
> **المخاطرة:** 🟡 متوسطة

## فلسفة القسم

`App.tsx` الحالي يجمع كل شيء في ملف واحد:
- Types يدوية
- Views حسب الدور
- Navigation
- Notification logic
- API client wrapper

**الهدف:** فصل هذه المسؤوليات إلى layers نظيفة، مع **single source of truth** للـ types (OpenAPI).

## القاعدة الذهبية

> **كل صفحة في ملف، كل type من OpenAPI، كل fetch عبر client موحّد**

---

## المراحل بالترتيب

| # | المرحلة | الأثر | المخاطرة | المدة |
|---|---|---|---|---|
| **R-07** | [تفكيك App.tsx](R-07_frontend_split.md) | −800 سطر | 🟡 | 12 ساعة |
| **R-08** | [OpenAPI types](R-08_openapi_types.md) | −200 سطر | 🟢 | 2 ساعات |

**المجموع:** ~−1,000 سطر، ~14 ساعة عمل

---

## 🎯 معايير إكمال القسم

- [ ] R-07: `App.tsx` ≤ 60 سطر (Router فقط)
- [ ] R-07: كل صفحة في `pages/` مستقلة وقابلة للتصدير
- [ ] R-07: `shell/AppShell.tsx` و `shell/RoleGuard.tsx` منفصلتان
- [ ] R-07: `api/client.ts` يُستخدم لكل fetch
- [ ] R-08: لا types يدوية في `App.tsx` أو `api/contract.ts`
- [ ] R-08: `prebuild` و `pretest` يولّدان types
- [ ] R-08: CI يفشل إذا `generated-types.ts` out-of-date
- [ ] bilingual + responsive + role guards كما هي
- [ ] لقطات شاشة لـ 4 أدوار متطابقة

---

## 📁 الهيكل المستهدف

```
frontend/src/
├── App.tsx                    # Router فقط (~50 سطر)
├── main.tsx                   # نقطة الدخول
├── shell/
│   ├── AppShell.tsx           # layout
│   ├── RoleGuard.tsx          # role-based
│   └── ErrorBoundary.tsx
├── pages/
│   ├── platform/              # Platform Admin views
│   ├── owner/                 # Company Owner views
│   ├── monitor/               # Quality Monitor views
│   ├── employee/              # Employee views
│   └── shared/                # TasksPage, EvidencePage, ...
├── domain/                    # types و services مجمّعة
├── hooks/                     # custom hooks
├── design-system/
│   └── tokens.ts              # (موجود)
└── api/
    ├── contract.ts            # re-export من generated
    ├── bootstrap.ts           # (موجود)
    ├── generated-types.ts     # OpenAPI source of truth
    └── client.ts              # fetch wrapper
```

---

## 🔗 العلاقات

```
R-08 ──> R-07
```

- R-08 (types) يجب أن يسبِق R-07 (split) لتجنب duplication أثناء النقل
- أو: نفّذ R-07 أولاً مع types يدوية، ثم R-08 لتحويلها

---

## ⚠️ احتياطات القسم

1. **تنفيذ R-07 على دفعات** (R-07a → R-07i كما هو موثّق)
2. **اختبر على Chrome desktop + Android** (المتصفح المعتمد)
3. **لا تغيّر `design-system/tokens.ts`** (مصدر الحقيقة للـ UI)
4. **وثّق خريطة التحويل** في `MAPPING.md` (manual type → generated component)

---

## 🚀 الخطوة التالية بعد إكمال القسم

عند اكتمال R-07 → R-08، انتقل إلى **[القسم الرابع: الجودة والاختبار](../section-04-quality/README.md)**
