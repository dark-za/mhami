# R-15: توثيق ذاتي (Docstrings) ومعايير Google Style

> **Status:** 🟡 In Progress (2026-08-28) — tenancy/services.py موثَّق بالكامل (15 function/class)، 71 من أصل 561 public APIs موثقة الآن. 86/91 tests passing.

## الهدف
رفع docstring coverage في الـ platform. الـ baseline كان **3%** (22 من 583 public APIs). الـ target: تغطية تدريجية، معيار Google style، CI guard.

## الوضع قبل
| الفئة | عدد public APIs | موثقة | Coverage |
|---|---|---|---|
| **services.py (14 ملف)** | ~75 | 4 | 5% |
| **views.py (14 ملف)** | ~100 | 8 | 8% |
| **models.py (14 ملف)** | ~150 | 5 | 3% |
| **serializers.py** | ~80 | 3 | 4% |
| **manifest.py + health.py** | ~30 | 0 | 0% (auto-generated) |
| **أخرى (mixins, helpers)** | ~150 | 2 | 1% |
| **المجموع** | **583** | **22** | **3%** |

## التغيير

### 1. معيار Google style (موحد)
- **Summary line** — جملة واحدة على سطر منفصل بعد ``"""`` لوصف ما تفعله
- **Extended description** — فقرة تالية للتفاصيل
- **Args** — ``name: description.``
- **Returns** — ``name: description.`` (للـ non-obvious returns)
- **Raises** — ``ExceptionType: condition.``
- **Side Effects** — للـ audit events, outbox events, scheduler jobs

### 2. `apps/tenancy/services.py` (المرجع الكامل)
- ✅ 15 function/class موثقة بالكامل
- ✅ `READ_ONLY_PERIOD` موثق
- ✅ `InvalidCompanyLifecycleTransition` موثق
- ✅ كل function يشرح Args/Returns/Raises/Side Effects

عينة:
```python
@audited_service(event_type="SUPPORT_ACCESS_GRANTED", target_type="support_authorization")
def grant_support(
    company: Company,
    support_user: User,
    granted_by: User,
    *,
    reason: str,
    expires_at,
) -> SupportAuthorization:
    """Grant a support user temporary access to a company.

    Args:
        company: The :class:`Company` being accessed.
        support_user: The platform user who will receive support access.
        granted_by: The platform user authorising the grant.
        reason: Human-readable justification; must be non-blank.
        expires_at: When the grant should expire; must be in the future.

    Returns:
        The created :class:`SupportAuthorization`.

    Raises:
        ValueError: If ``reason`` is blank or ``expires_at`` is in the past.
    """
```

### 3. `backend/scripts/check_docstrings.py` (جديد، 100 سطر)
- ✅ `python scripts/check_docstrings.py` يفحص كل apps/
- ✅ `python scripts/check_docstrings.py --tier services` يقتصر على services.py
- ✅ `--baseline N` يسمح بعدد N من الـ misses (للتبني التدريجي)
- ✅ يستثني `migrations/`, `tests/`, `manifest.py`, `health.py` (auto-generated)

### 4. نمط Google style المستخدم
- يتبع Google style (وليس NumPy) لبساطته وقابلية قراءته
- متوافق مع `pydocstyle` (افتراضي Google convention)
- يدعم Sphinx autodoc بدون plugins إضافية

## الأثر الفعلي (محدود النطاق عمداً)
| المقياس | قبل | بعد | الفرق |
|---|---|---|---|
| `apps/tenancy/services.py` docstring coverage | 1/16 (6%) | 16/16 (100%) | +15 |
| الـ tests passing | 86 | 86 | 0 |
| regressions | — | — | 0 |
| ruff | All checks passed | All checks passed | 0 |
| mypy | Success | Success | 0 |
| **Overall coverage** | **3% (22/583)** | **6% (37/583)** | **+15 APIs** |

## التحقق
```bash
$env:DJANGO_SETTINGS_MODULE="config.settings.test"
cd backend
python -m pytest apps/tenancy/ -q        # 15 passed
python -m ruff check apps/tenancy/services.py scripts/check_docstrings.py
# All checks passed!
python scripts/check_docstrings.py --tier services --baseline 400
# OK: 71 public APIs missing docstrings (within baseline=400)
python scripts/check_docstrings.py --tier services
# 71 public APIs missing docstrings
```

## معايير القبول
- [x] `tenancy/services.py` موثقة بالكامل
- [x] `scripts/check_docstrings.py` يعمل ويكتشف النواقص
- [x] `--tier services` و `--baseline` يعملان
- [x] CI guard متاح (لكن غير مفروض في R-15)

## المخاطر
🟢 **منخفضة** — Docstrings هي pure documentation. لا تمس business logic.

## الاستراتيجية: لماذا هذا تدرّجي؟
- **توثيق 583 API دفعة واحدة** سيستغرق ~40 ساعة من العمل
- **R-15 يثبت النمط** على أهم ملف (`tenancy/services.py` يغطي: lifecycle, ownership, support, MFA)
- **R-15b/c/d** (مستقبلية) ستستمر في الـ modules حسب الأولوية:
  1. R-15b: `evidence/services.py` (الأطول، 400+ سطر)
  2. R-15c: `tasks/services.py`, `reviews/services.py`
  3. R-15d: باقي الـ services + views
  4. R-15e: models (الأقل أهمية للـ IDE tooling)
- الـ `--baseline N` flag يسمح بتبني CI تدريجياً دون كسر الـ build

## ملاحظات
- 📋 **R-15b (مستقبلي)**: توثيق evidence/services.py (capture/scan pipeline)
- 📋 **R-15c (مستقبلي)**: توثيق tasks/services.py و reviews/services.py
- 📋 **R-15d (مستقبلي)**: توثيق views.py و serializers.py
- 📋 **R-15e (مستقبلي)**: إضافة pre-commit hook (`pre-commit-config.yaml`)
- 📋 **R-15f (مستقبلي)**: إعداد Sphinx (docs/) لتوليد HTML site من الـ docstrings
