# القسم الثاني: أنماط الوحدات (Module Patterns)

> **المراحل:** R-05 → R-06
> **المدة المقدرة:** 1 يوم
> **الأثر:** ~−520 سطر كود
> **المخاطرة:** 🟡 متوسطة

## فلسفة القسم

كل module في المشروع له نفس **البنية المنطقية**:
- `models.py` — تعريف البيانات
- `services.py` — منطق العمل
- `api/views.py` — واجهة HTTP
- `manifest.py` — metadata للـ registry
- `health.py` — فحص الصحة
- `apps.py` — Django AppConfig

المشكلة: **الكود المكرر عبر الـ 14 module** في `services.py` و `apps.py`.

## القاعدة الذهبية

> **Decorator واحد = transactional + audit موحّد**

---

## المراحل بالترتيب

| # | المرحلة | الأثر | المخاطرة | المدة |
|---|---|---|---|---|
| **R-05** | [@audited_service decorator](R-05_service_layer.md) | −400 سطر | 🟡 | 4 ساعات |
| **R-06** | [Module registration موحّد](R-06_module_registration.md) | −120 سطر | 🟡 | 2 ساعات |

**المجموع:** ~−520 سطر، ~6 ساعات عمل

---

## 🎯 معايير إكمال القسم

- [ ] R-05: كل service public function يستخدم `@audited_service` أو يوثّق سبب عدم ذلك
- [ ] R-05: عدد الـ `AuditEvent` المُنشأ متطابق قبل/بعد
- [ ] R-05: audit chain integrity test يمر
- [ ] R-06: `PLATFORM_MODULES` يُحسب تلقائياً من `INSTALLED_APPS`
- [ ] R-06: 14 module manifest مكتشَفة كما هي
- [ ] CI يمر بالكامل

---

## 📊 مقاييس Baseline

```
backend/apps/*/services.py:    ~15 service function × 14 module = 210 function
                                مع @transaction.atomic مكرر
backend/apps/*/manifest.py:    14 ملف (تم تبسيطه في R-02)
backend/apps/*/apps.py:        14 ملف مع نفس النمط
config/settings/base.py:       PLATFORM_MODULES list (14 سطر)
```

## 📊 مقاييس مستهدفة

```
backend/apps/*/services.py:    service functions أنظف، @audited_service موحّد
backend/apps/*/apps.py:        metadata مدمج في AppConfig
config/settings/base.py:       PLATFORM_MODULES محسوب تلقائياً
```

---

## 🔗 العلاقات

```
R-05 ──> R-06
```

- R-05 لا يعتمد على R-06
- R-06 يُسهّل صيانة الـ module registry

---

## ⚠️ احتياطات القسم

1. **اختبر audit chain** بعد تطبيق R-05 (`previous_hash` و `event_hash` يجب أن يبقيا متطابقين)
2. **R-06** يجب أن يحافظ على `manifest.py` كـ re-export في البداية (deprecation في commit لاحق)
3. **Django app loading order** حساس — `manifest.ready()` يجب أن يعمل بعد كل الـ apps

---

## 🚀 الخطوة التالية بعد إكمال القسم

عند اكتمال R-05 → R-06، انتقل إلى **[القسم الثالث: الواجهة الأمامية](../section-03-frontend/README.md)**
