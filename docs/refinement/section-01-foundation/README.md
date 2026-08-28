# القسم الأول: الأساسات (Foundation)

> **المراحل:** R-01 → R-02 → R-03 → R-04
> **المدة المقدرة:** 1-2 يوم
> **الأثر:** ~−900 سطر كود
> **المخاطرة:** 🟢 منخفضة إلى متوسطة

## فلسفة القسم

تنظيف **الأساسات المشتركة** التي يستخدمها كل module. كل تغيير هنا يُسهّل المراحل اللاحقة.

## القاعدة الذهبية لهذا القسم

> **لا تغيّر منطق العمل — فقط استبدل التكرار بـ factory / decorator / mixin**

---

## المراحل بالترتيب

| # | المرحلة | الأثر | المخاطرة | المدة |
|---|---|---|---|---|
| **R-01** | [توحيد health endpoints](R-01_health_consolidation.md) | −150 سطر | 🟢 | 1 ساعة |
| **R-02** | [توحيد ModuleManifest](R-02_manifest_base.md) | −200 سطر | 🟢 | 1 ساعة |
| **R-03** | [TenantContext Mixin](R-03_tenant_mixin.md) | −300 سطر | 🟡 | 3 ساعات |
| **R-04** | [معالجة أخطاء موحّدة](R-04_error_handler.md) | −250 سطر | 🟡 | 2 ساعات |

**المجموع:** ~−900 سطر، ~7 ساعات عمل

---

## 🎯 معايير إكمال القسم

- [ ] R-01: كل `health.py` ≤ 2 سطر (factory call)
- [ ] R-02: كل `manifest.py` ≤ 8 أسطر
- [ ] R-03: كل `APIView` يرث من `TenantAPIView` أو يوثّق سبب عدم ذلك
- [ ] R-04: لا `_service_error()` helper محلي في أي view
- [ ] CI يمر بالكامل
- [ ] عدد الـ tests passing لم ينخفض

---

## 📊 مقاييس Baseline (قبل البدء)

```
backend/apps/*/health.py:     13 ملف × ~5 سطر = ~65 سطر
backend/apps/*/manifest.py:   14 ملف × ~15 سطر = ~210 سطر
backend/apps/*/api/views.py:  30+ view مع tenant_context مكرر
backend/apps/*/api/views.py:  25+ view مع try/except مكرر
```

## 📊 مقاييس مستهدفة (بعد الإكمال)

```
backend/apps/*/health.py:     13 ملف × 2 سطر = 26 سطر (−60%)
backend/apps/*/manifest.py:   14 ملف × 8 سطور = 112 سطر (−47%)
backend/apps/*/api/views.py:  30+ view بـ TenantAPIView (نظيف)
backend/apps/*/api/views.py:  25+ view بـ @platform_service_call
```

---

## 🔗 العلاقات بين المراحل

```
R-01 ──┐
       ├──> R-03 ──> R-04
R-02 ──┘
```

- R-01 و R-02 مستقلان (نفّذ أيهما أولاً)
- R-03 يعتمد على فهم R-01/R-02 للـ patterns
- R-04 يُكمّل R-03 (نفس الـ APIView)

---

## ⚠️ احتياطات القسم

1. **نفّذ على دفعات صغيرة** — كل refactor في commit منفصل
2. **CI أولاً** — شغّل `pytest` بعد كل خطوة
3. **لا تغيّر** توقيعات `tenant_context()` أو `record_audit_event()`
4. **وثّق** أي deviasiion في الـ commit message

---

## 🚀 الخطوة التالية بعد إكمال القسم

عند اكتمال R-01 → R-04، انتقل إلى **[القسم الثاني: أنماط الوحدات](../section-02-modules/README.md)**
