# 🗺️ الخريطة الرسمية — المرجع الشامل للصقل والتطوير

> **الاسم الرسمي:** MHAMI Refinement Roadmap v1.0
> **التاريخ:** 2026-08-28
> **الحالة:** معتمدة للتنفيذ
> **المرجع:** هذا الملف هو **single source of truth** لتسلسل التنفيذ

---

## 🎯 الرؤية

تحويل **MHAMI** من "قاعدة عاملة 85%" إلى "منتج مُصقَل 100%" عبر **16 مرحلة** موزعة على **6 أقسام**، مع:
- ✅ **أقل مساحة** (−3,700 سطر)
- ✅ **أكبر فائدة** (+40% readability)
- ✅ **أنضج** (حوكمة دائمة)
- ✅ **تسلسل آمن** (لا كسر، لا regressions)

---

## 🗺️ الخريطة الرسمية

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    🎯 MHAMI Refinement Roadmap                          │
│                         16 مرحلة / 6 أقسام                              │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ 🏛️ القسم 1   │         │ 🧩 القسم 2    │         │ 🎨 القسم 3    │
│ الأساسات      │ ──────► │ أنماط الوحدات │ ──────► │ الواجهة       │
│ 4 مراحل       │         │ 2 مرحلتان     │         │ 2 مرحلتان     │
│ يوم 1-2       │         │ يوم 3-4       │         │ يوم 5-7       │
└───────────────┘         └───────────────┘         └───────────────┘
        │                                                   │
        │ R-01 ✓ R-02 ✓ R-03 ✓ R-04 ✓                      │ R-07 ✓ R-08 ✓
        │ ~−900 سطر                                        │ ~−1,000 سطر
        ▼                                                   ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ 🧪 القسم 4   │         │ 🔬 القسم 5    │         │ 🛡️ القسم 6   │
│ الجودة        │ ──────► │ أنماط         │ ──────► │ الحوكمة       │
│ والاختبار     │         │ متقدمة        │         │ 4 مراحل       │
│ 2 مرحلتان     │         │ 2 مرحلتان     │         │ يوم 13-14     │
│ يوم 8-9       │         │ يوم 10-12     │         │               │
└───────────────┘         └───────────────┘         └───────────────┘
        │                                                   │
        │ R-09 ✓ R-10 ✓                                    │ R-13 ✓ R-14 ✓ R-15 ✓ R-16 ✓
        │ ~−700 سطر                                        │ ~−150 سطر + حوكمة
        ▼                                                   ▼
                              ┌──────────────┐
                              │  ✅ DONE     │
                              │  ~−3,700 سطر │
                              │  +40% جودة   │
                              └──────────────┘
```

---

## 📊 الأقسام الستة — نظرة سريعة

| # | القسم | المراحل | المدة | الأثر | المخاطرة |
|---|---|---|---|---|---|
| **1** | 🏛️ [الأساسات](section-01-foundation/README.md) | R-01 → R-04 | 1-2 يوم | −900 سطر | 🟢 |
| **2** | 🧩 [أنماط الوحدات](section-02-modules/README.md) | R-05 → R-06 | 1 يوم | −520 سطر | 🟡 |
| **3** | 🎨 [الواجهة الأمامية](section-03-frontend/README.md) | R-07 → R-08 | 2-3 أيام | −1,000 سطر | 🟡 |
| **4** | 🧪 [الجودة والاختبار](section-04-quality/README.md) | R-09 → R-10 | 1-2 يوم | −700 سطر | 🟢 |
| **5** | 🔬 [أنماط متقدمة](section-05-patterns/README.md) | R-11 → R-12 | 2-3 أيام | −400 سطر | 🟡 |
| **6** | 🛡️ [الحوكمة](section-06-governance/README.md) | R-13 → R-16 | 2-3 أيام | −150 سطر | 🟢 |
| | | **16 مرحلة** | **9-14 يوم** | **~−3,700 سطر** | |

---

## 🔢 المراحل الـ 16 — الفهرس الكامل

### القسم 1: 🏛️ الأساسات
| المرحلة | الوصف | الأثر | المخاطرة |
|---|---|---|---|
| [R-01](section-01-foundation/R-01_health_consolidation.md) | توحيد health endpoints | −150 سطر | 🟢 |
| [R-02](section-01-foundation/R-02_manifest_base.md) | توحيد ModuleManifest | −200 سطر | 🟢 |
| [R-03](section-01-foundation/R-03_tenant_mixin.md) | TenantContext Mixin | −300 سطر | 🟡 |
| [R-04](section-01-foundation/R-04_error_handler.md) | معالجة أخطاء موحّدة | −250 سطر | 🟡 |

### القسم 2: 🧩 أنماط الوحدات
| المرحلة | الوصف | الأثر | المخاطرة |
|---|---|---|---|
| [R-05](section-02-modules/R-05_service_layer.md) | @audited_service decorator | −400 سطر | 🟡 |
| [R-06](section-02-modules/R-06_module_registration.md) | Module registration موحّد | −120 سطر | 🟡 |

### القسم 3: 🎨 الواجهة الأمامية
| المرحلة | الوصف | الأثر | المخاطرة |
|---|---|---|---|
| [R-07](section-03-frontend/R-07_frontend_split.md) | تفكيك App.tsx | −800 سطر | 🟡 |
| [R-08](section-03-frontend/R-08_openapi_types.md) | OpenAPI types only | −200 سطر | 🟢 |

### القسم 4: 🧪 الجودة والاختبار
| المرحلة | الوصف | الأثر | المخاطرة |
|---|---|---|---|
| [R-09](section-04-quality/R-09_test_fixtures.md) | conftest fixtures | −200 سطر | 🟢 |
| [R-10](section-04-quality/R-10_dead_code.md) | حذف الكود الميت | −500 سطر | 🟡 |

### القسم 5: 🔬 أنماط متقدمة
| المرحلة | الوصف | الأثر | المخاطرة |
|---|---|---|---|
| [R-11](section-05-patterns/R-11_outbox_events.md) | Outbox events موحّدة | −150 سطر | 🟡 |
| [R-12](section-05-patterns/R-12_tenant_querysets.md) | Tenant QuerySets | −250 سطر | 🟡 |

### القسم 6: 🛡️ الحوكمة
| المرحلة | الوصف | الأثر | المخاطرة |
|---|---|---|---|
| [R-13](section-06-governance/R-13_config_centralization.md) | Pydantic Settings | −100 سطر | 🟢 |
| [R-14](section-06-governance/R-14_compose_compression.md) | Compose compression | −50 سطر | 🟡 |
| [R-15](section-06-governance/R-15_docstrings.md) | Docstrings إلزامية | +جودة | 🟢 |
| [R-16](section-06-governance/R-16_metrics_and_ci.md) | CI quality gates | +جودة | 🟢 |

---

## 📐 قواعد المسار (Dependency Graph)

```
[القسم 1] R-01 ─┐
                ├─→ R-03 ─→ R-04
        R-02 ──┘
                │
                ▼
[القسم 2] R-05 ──→ R-06
                │
                ▼
[القسم 3] R-08 ──→ R-07   (يفضّل: R-08 قبل R-07)
                │
                ▼
[القسم 4] R-09 و R-10 (مستقلان)
                │
                ▼
[القسم 5] R-11 و R-12 (مستقلان)
                │
                ▼
[القسم 6] R-13 ──→ R-15 ──→ R-16
        R-14 (مستقل)
```

---

## ✅ معايير القبول العامة (لكل مرحلة)

- [ ] `pytest` يمر (CI يبقى أخضر)
- [ ] `ruff check .` و `mypy .` نظيف
- [ ] `npm run typecheck && npm run build && npm run test` نظيف
- [ ] لا انحدار في عدد الـ tests passing
- [ ] Diff صافي ≤ 400 سطر (أو مذكور خلاف ذلك)
- [ ] تحديث الوثائق المرتبطة (ADR إن لزم)
- [ ] لا تغيير في schema DB بدون migration منفصل
- [ ] لا تغيير في الـ API URLs أو contracts
- [ ] PR منفصل مع description واضح
- [ ] Baseline metrics محسوبة قبل/بعد

---

## 🚀 ترتيب التنفيذ الموصى به

### الأسبوع 1: الأساسات + الوحدات (يوم 1-4)
```
يوم 1: R-01 + R-02          (الأسهل، يضع الـ pattern)
يوم 2: R-03                  (يبدأ يلمس views)
يوم 3: R-04 + R-05          (decorator-based cleanup)
يوم 4: R-06                  (إكمال أنماط الوحدات)
```

### الأسبوع 2: الواجهة الأمامية (يوم 5-7)
```
يوم 5: R-08 (OpenAPI types)  (أولاً لتجنب duplication)
يوم 6: R-07a-d (Frontend split - الجزء 1)
يوم 7: R-07e-i (Frontend split - الجزء 2)
```

### الأسبوع 3: الجودة والأنماط (يوم 8-12)
```
يوم 8: R-09 (conftest)       (يُسهّل R-10)
يوم 9: R-10 (كود ميت)       (بحذر)
يوم 10: R-11 (Outbox)        (transactions)
يوم 11: R-12 (Tenant QS)     (model by model)
يوم 12: R-12 (continuation)
```

### الأسبوع 4: الحوكمة (يوم 13-14)
```
يوم 13: R-13 + R-14          (تكوين + docker)
يوم 14: R-15 + R-16          (docstrings + CI gates)
```

---

## 📈 المقاييس المتوقعة

| المؤشر | قبل | بعد | التحسين |
|---|---|---|---|
| أسطر Python في `apps/` | ~10,000 | ~6,300 | **−37%** |
| حجم `App.tsx` | ~800 | < 60 | **−92%** |
| ملفات `health.py` مكررة | 13 | 1+13 | **−85%** |
| boilerplate في views | 30+ | 0 | **−100%** |
| setup مكرر في tests | ~15/test | ~3 | **−80%** |
| كود ميت | ~500 | 0 | **−100%** |
| تغطية tests | غير مقاسة | ≥ 70% | **+قياس** |
| `compose.yml` (base) | 50 | ≤ 60 (مع anchor) | مضغوط |
| **الإجمالي** | — | **~−3,700 سطر** | **+40% جودة** |

---

## 🎯 KPI النجاح (عند اكتمال الخطة)

1. ✅ **CI أخضر** 100% من الوقت
2. ✅ **لا ملف** > 500 سطر (ما عدا migrations/tests)
3. ✅ **لا دالة** بدون docstring
4. ✅ **لا تكرار** في `health.py`, `manifest.py`, `apps.py`
5. ✅ **كل view** يستخدم `TenantAPIView` + `@platform_service_call`
6. ✅ **OpenAPI** هو single source of truth للـ types
7. ✅ **تغطية tests** ≥ 70%
8. ✅ **Cyclomatic complexity** ≤ C في كل module
9. ✅ **METRICS.md** يُحدّث أسبوعياً
10. ✅ **جاهز لـ Phase 13** (الإطلاق الإنتاجي)

---

## 📞 التواصل والمتابعة

### التقارير
- **يومياً**: PR description يذكر المرحلة
- **أسبوعياً**: تحديث `docs/refinement/METRICS.md`
- **عند الإكمال**: تحديث هذا الملف بحالة كل قسم

### التصعيد
- 🟢 **مرحلة بمخاطرة منخفضة**: تنفيذ مباشر
- 🟡 **مرحلة بمخاطرة متوسطة**: PR + 1 reviewer
- 🟠 **مرحلة بمخاطرة عالية**: PR + 2 reviewers + migration review

### الأوامر السريعة

```bash
# قياس baseline قبل البدء
cd backend && cloc apps/ --include-lang=Python
cd frontend && cloc src/ --include-lang=TypeScript

# قياس التقدم بعد كل قسم
cd backend && cloc apps/ --include-lang=Python
git diff --stat  # الأسطر المضافة/المحذوفة

# فحص الجودة
cd backend && ruff check . && mypy . && pytest
cd frontend && npm run typecheck && npm run build && npm run test
```

---

## 📂 هيكل الملفات

```
docs/refinement/
├── 00_OFFICIAL_MAP.md          ← أنت هنا (المرجع الرسمي)
├── 00_REFINEMENT_ROADMAP.md    ← النظرة العامة
├── EXEC_SUMMARY.md             ← ملخص تنفيذي
│
├── section-01-foundation/      ← القسم 1
│   ├── README.md
│   ├── R-01_health_consolidation.md
│   ├── R-02_manifest_base.md
│   ├── R-03_tenant_mixin.md
│   └── R-04_error_handler.md
│
├── section-02-modules/         ← القسم 2
│   ├── README.md
│   ├── R-05_service_layer.md
│   └── R-06_module_registration.md
│
├── section-03-frontend/        ← القسم 3
│   ├── README.md
│   ├── R-07_frontend_split.md
│   └── R-08_openapi_types.md
│
├── section-04-quality/         ← القسم 4
│   ├── README.md
│   ├── R-09_test_fixtures.md
│   └── R-10_dead_code.md
│
├── section-05-patterns/        ← القسم 5
│   ├── README.md
│   ├── R-11_outbox_events.md
│   └── R-12_tenant_querysets.md
│
└── section-06-governance/      ← القسم 6
    ├── README.md
    ├── R-13_config_centralization.md
    ├── R-14_compose_compression.md
    ├── R-15_docstrings.md
    └── R-16_metrics_and_ci.md
```

---

## 🏁 نقطة البداية

**ابدأ بـ:** [القسم 1 → R-01: توحيد health endpoints](section-01-foundation/R-01_health_consolidation.md)

**الأسباب:**
- ✅ الأسهل فنياً (factory + import)
- ✅ الأعلى عائد (−150 سطر / ساعة)
- ✅ يُثبت الـ pattern (factory) للقسم كاملاً
- ✅ يضع الأساس لـ R-02, R-03, R-04

---

> **"أبسط ما يمكن أن يعمل، وأعمق ما يمكن أن يُفهم"**
> — فلسفة MHAMI Refinement Roadmap v1.0
