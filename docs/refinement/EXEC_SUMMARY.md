# 🎯 الخطة التنفيذية — ملخص تنفيذي

**المشروع:** Mhami
**المهمة:** صقل الكود والبنية
**التاريخ:** 2026-08-28
**عدد المراحل:** 16 مرحلة / 6 أقسام
**الفلسفة:** أقل مساحة، أكبر فائدة، أعلى نضج

> **📍 الخريطة الرسمية:** [`00_OFFICIAL_MAP.md`](00_OFFICIAL_MAP.md)

---

## 📊 النتيجة المستهدفة

| البُعد | قبل | بعد (مستهدف) | التحسين |
|---|---|---|---|
| أسطر Python في `apps/` | ~10,000 | ~6,300 | **−37%** |
| حجم `App.tsx` | ~800 سطر | < 60 سطر | **−92%** |
| ملفات `health.py` مكررة | 13 متطابقة | 1 factory + 13 use | **−85%** |
| boilerplate في views | 30+ view مع try/except | 1 decorator | **−250 سطر** |
| setup مكرر في tests | ~15 سطر/test | ~3 أسطر | **−85%** |
| كود ميت (مُقدّر) | ~500 سطر | 0 | **−100%** |
| تغطية tests | غير مقاسة | ≥ 70% | **+قياس** |

**الإجمالي المتوقع: −3,700 سطر مع تحسين الجودة**

---

## 🗺️ خريطة المراحل

### المرحلة 1: تنظيف الأساسات (يوم 1-2)
- **R-01**: توحيد `health.py` (13 ملف → 1 factory)
- **R-02**: توحيد `manifest.py` (14 ملف → factory)
- **R-03**: `TenantContext` كـ Mixin (30+ view)
- **R-04**: decorator لمعالجة الأخطاء (250 سطر)

### المرحلة 2: توحيد أنماط الوحدات (يوم 3-4)
- **R-05**: `@audited_service` decorator
- **R-06**: module registration عبر AppConfig

### المرحلة 3: صقل الـ Frontend (يوم 5-7)
- **R-07**: تفكيك `App.tsx` monolith (800 → 50 سطر)
- **R-08**: types من OpenAPI فقط

### المرحلة 4: اختبارات وكود ميت (يوم 8-9)
- **R-09**: conftest factories مشتركة
- **R-10**: حذف الكود الميت (Vulture)

### المرحلة 5: أنماط متقدمة (يوم 10-12)
- **R-11**: Outbox events موحّدة
- **R-12**: Tenant-aware QuerySets

### المرحلة 6: تكوين، CI، توثيق (يوم 13-14)
- **R-13**: Pydantic Settings
- **R-14**: YAML anchors في compose
- **R-15**: docstrings إلزامية
- **R-16**: CI quality gates + metrics

---

## 🎁 الفوائد النوعية

### أقل مساحة ✅
- حذف 3,700 سطر كود مكرر
- ضغط 800 سطر `App.tsx` إلى 50
- إزالة 14 ملف boilerplate

### أكبر فائدة ✅
- `@audited_service` ينظم transaction + audit في decorator واحد
- `TenantAPIView` يجمع الصلاحيات في الكلاس
- `@platform_service_call` يلغي try/except المكرر

### أنضج ✅
- Type safety عبر OpenAPI
- Pydantic settings يمنع typos
- CI يفحص file size + complexity
- Pre-commit hooks تفرض الجودة

---

## ⚠️ المخاطر المُدارة

| المرحلة | المخاطرة | الاحتياط |
|---|---|---|
| R-03 (Tenant Mixin) | 🟡 متوسطة | تنفيذ على دفعات (3 modules/يوم) |
| R-05 (Services) | 🟡 متوسطة | audit chain integrity test |
| R-07 (Frontend split) | 🟡 متوسطة | feature flag للـ pages الجديدة |
| R-11 (Outbox) | 🟡 متوسطة | اختبار transaction rollback |
| R-12 (QuerySets) | 🟡 متوسطة | ابدأ بـ model واحد، test, ثم تعميم |

**لا مرحلة بمخاطرة عالية** — كل التغييرات additive أو refactor.

---

## 📋 معايير القبول العامة

كل مرحلة يجب أن:
- [ ] تحافظ على CI خضراء (`pytest`, `ruff`, `mypy`, `npm run test/build`)
- [ ] لا تكسر public API
- [ ] تُراجع في PR منفصل
- [ ] تذكر الـ metric قبل/بعد في الوصف

---

## 🚀 الخطوة التالية

1. **احصل على موافقة** على الخطة الشاملة
2. **ابدأ بـ R-01** (أسهل، أعلى عائد)
3. **سجّل baseline metrics** قبل البدء
4. **تقرير أسبوعي** بالتقدم
5. **احتفاء** عند اكتمال R-16 🎉

---

## 📂 الهيكل الكامل (6 أقسام)

```
docs/refinement/
├── 00_OFFICIAL_MAP.md          ← الخريطة الرسمية (المرجع)
├── 00_REFINEMENT_ROADMAP.md    ← النظرة العامة
├── EXEC_SUMMARY.md             ← هذا الملف
│
├── section-01-foundation/      🏛️  الأساسات (R-01 → R-04)
├── section-02-modules/         🧩  أنماط الوحدات (R-05 → R-06)
├── section-03-frontend/        🎨  الواجهة الأمامية (R-07 → R-08)
├── section-04-quality/         🧪  الجودة والاختبار (R-09 → R-10)
├── section-05-patterns/        🔬  أنماط متقدمة (R-11 → R-12)
└── section-06-governance/      🛡️  الحوكمة (R-13 → R-16)
```

**كل قسم فيه:**
- `README.md` — نظرة عامة على القسم
- `R-XX_*.md` — تفاصيل كل مرحلة

**كل ملف مرحلة يحتوي على:**
- الهدف
- الوضع الحالي
- التغيير المقترح مع كود
- الأثر المتوقع
- التحقق
- معايير القبول
- المخاطر + الاحتياطات

---

> **"أبسط ما يمكن أن يعمل، وأعمق ما يمكن أن يُفهم"**
> — فلسفة الصقل في 16 مرحلة
