# القسم السادس: الحوكمة (Governance)

> **المراحل:** R-13 → R-14 → R-15 → R-16
> **المدة المقدرة:** 2-3 أيام
> **الأثر:** ~−200 سطر + حوكمة دائمة
> **المخاطرة:** 🟢 منخفضة

## فلسفة القسم

**الحوكمة الدائمة** التي تمنع الانحدار في الجودة:
- تكوين مركزي (Pydantic)
- Docker Compose مضغوط
- توثيق ذاتي إلزامي
- CI يفرض المعايير تلقائياً

## القاعدة الذهبية

> **المعايير التي لا تُفرض آلياً = معايير لن تُحترم**

---

## المراحل بالترتيب

| # | المرحلة | الأثر | المخاطرة | المدة |
|---|---|---|---|---|
| **R-13** | [Pydantic Settings](R-13_config_centralization.md) | −100 سطر | 🟢 | 3 ساعات |
| **R-14** | [Compose compression](R-14_compose_compression.md) | −50 سطر | 🟡 | 2 ساعات |
| **R-15** | [Docstrings إلزامية](R-15_docstrings.md) | +جودة | 🟢 | 4 ساعات |
| **R-16** | [CI quality gates](R-16_metrics_and_ci.md) | +جودة | 🟢 | 3 ساعات |

**المجموع:** ~−150 سطر + حوكمة، ~12 ساعة عمل

---

## 🎯 معايير إكمال القسم

### R-13
- [ ] كل قراءة env تمر عبر `PlatformSettings`
- [ ] لا `os.getenv()` في `base.py` (إلا safety checks)
- [ ] `.env.example` يطابق `PlatformSettings`
- [ ] CI يمر في dev, test, prod

### R-14
- [ ] `compose.yml` (base) ≤ 60 سطر
- [ ] `compose.dev.yml` ≤ 20 سطر
- [ ] `compose.prod.yml` ≤ 100 سطر
- [ ] نفس الـ output من `docker compose config` قبل/بعد

### R-15
- [ ] كل public function/class في `apps/` عنده docstring
- [ ] Google style
- [ ] pre-commit hook يكتشف الناقص
- [ ] README/CHANGELOG يذكر القاعدة

### R-16
- [ ] CI يفشل على PR يكسر أحد الفحوصات
- [ ] تقرير `METRICS.md` يُحدّث أسبوعياً
- [ ] pre-commit hooks مُفعّلة
- [ ] لا ملف يتجاوز 500 سطر

---

## 📊 مقاييس Baseline

```
config/settings/base.py: 200+ سطر مع os.getenv() مكرر
compose.yml + dev + prod: ~200 سطر
بدون pre-commit hooks
بدون CI quality gates
بدون METRICS.md
```

## 📊 مقاييس مستهدفة

```
config/settings/base.py: أنظف مع Pydantic
compose.yml: ≤ 60 سطر
compose.dev.yml: ≤ 20 سطر
compose.prod.yml: ≤ 100 سطر
pre-commit hooks: ✓ مفعّلة
CI quality gates: ✓ تفرض المعايير
METRICS.md: ✓ تقرير أسبوعي
```

---

## 🔗 العلاقات

```
R-13 ──> R-15 ──> R-16
R-14 (مستقل)
```

- R-13 و R-14 مستقلان
- R-15 يحتاج R-13 (لتجنب توثيق env vars المتغيرة)
- R-16 يحتاج R-15 (يفرض docstrings كـ gate)

---

## ⚠️ احتياطات القسم

1. **R-13**: ابدأ بـ `base.py` فقط (لا تلمس `dev.py`, `prod.py` في نفس الـ commit)
2. **R-14**: **لا تحذف `compose.prod.yml`** في البداية؛ فقط أضف `compose.common.yml`
3. **R-15**: **لا تكتب docstring مُضلّل** — إذا لم تفهم، اكتب "TODO: document"
4. **R-16**: ابدأ بـ file size check، ثم complexity، ثم coverage

---

## 🎉 اكتمال الخطة

عند اكتمال R-13 → R-16، تكون الخطة الكاملة قد انتهت.

**الإجمالي النهائي المتوقع:**
- **~−3,700 سطر** كود مكرر
- **+40%** readability
- **−30%** cognitive load
- **حوكمة دائمة** تمنع الانحدار
- **جاهز لـ Phase 13** ببنية أنظف
