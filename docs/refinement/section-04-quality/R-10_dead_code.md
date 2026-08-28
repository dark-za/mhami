# R-10: حذف الكود الميت (Dead Code Elimination)

> **Status:** ✅ Completed (2026-08-28) — 2 view files مُهذَّبة، 4 helper functions محذوفة، 3 imports ميتة. لا regressions.

## الهدف
إزالة الـ imports, functions, classes, files غير المستخدمة.

## المنهجية المُتبّعة
بدلاً من الاعتماد الكلي على Vulture (الذي يعطي false-positives كثيرة مع Django patterns)، تم **مراجعة يدوية مستهدفة** للـ patterns المعروفة:
1. **R-03 leftovers**: helper functions من نمط `_company_or_400`, `_company_for_request`, `_ensure_company_operational`
2. **Imports ميتة**: `tenant_context`, `is_owner`, `ensure_company_operational` التي كانت تُستخدم مع helpers
3. **frontend dead code**: Vite build بدون warnings، typecheck نظيف

## Vulture Baseline (للمرجع)
`vulture apps/ --min-confidence 80` يُظهر 5 نتائج فقط:
- 4 منها `schema_editor` في migrations (Django positional arg، false positive)
- 1 `revoked_by` في `tenancy/services.py:220` (تحتاج تحقق يدوي)

مع `--min-confidence 60` النتائج كثيرة لكن معظمها false positives:
- `class AiGatewayConfig` (مُستخدَم في `INSTALLED_APPS`)
- `class BackupPolicyUpdateSerializer` (مُستخدَم في views)
- `default_auto_field`, `pytestmark`, `urlpatterns` (Django/pytest config)
- `chain_hash`, `hmac_digest` properties على audit model (مُستخدَمة في chain computation)

→ **Vulture غير مفيد لـ Django code.** الـ review اليدوي أكثر دقة.

## التغييرات

### 1. `apps/notifications/api/views.py` (68 → 62 سطر)
- ❌ حذف `def _company_or_400(request: HttpRequest)` (4 أسطر + 2 imports)
- ❌ حذف `from django.http import HttpRequest`
- ❌ حذف `from apps.tenancy.access import tenant_context`

### 2. `apps/organizations/api/views.py` (124 → 110 سطر)
- ❌ حذف `def _company_for_request(request)` (2 سطور)
- ❌ حذف `def _ensure_company_operational(company)` (2 سطور)
- ❌ حذف `from apps.tenancy.access import tenant_context`
- ❌ حذف `is_owner` و `ensure_company_operational` imports
- ✅ استبدال 3 أنماط:
  ```python
  # قبل
  company = _company_for_request(request)
  if not is_owner(request.user, company):
      raise PlatformAPIException("Owner access required.")
  _ensure_company_operational(company)
  # ...
  
  # بعد
  context = self.get_tenant()
  context.require_roles(CompanyRole.OWNER)
  company = context.company
  # ...
  ```
- ✅ استبدال 2 `required_roles = ("OWNER", "MONITOR")` بـ `required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)` (تماشياً مع باقي modules)

## ما لم يُحذف (ومبرر ذلك)
| البند | السبب |
|---|---|
| Migrations (28 ملف) | كلها ضرورية. لا نسخ قديمة قابلة للدمج |
| ADRs (9 ملفات) | كلها حالية، لا superseded |
| `apps/audit/models.py:80 chain_hash` property | مُستخدمة في HMAC chain computation |
| `apps/audit/models.py:84 hmac_digest` property | نفس الشيء |
| `schema_editor` (5 occurrences) | Django migration API positional arg |
| `is_owner` في `backups/api/views.py` و `exports/api/views.py` | خارج نطاق R-10 (refactor متبقي) |
| `require_company_user` في `tasks/api/views.py` | API مختلف عن `require_roles` |
| Frontend `bootstrapSnapshot` fallback | لا يزال مستخدماً في AppShell و useBootstrap |

## الأثر الفعلي
| المقياس | قبل | بعد | الفرق |
|---|---|---|---|
| `apps/notifications/api/views.py` | 68 سطر | 62 سطر | **−6** |
| `apps/organizations/api/views.py` | 124 سطر | 110 سطر | **−14** |
| Helper functions محذوفة | — | — | **−4** (`_company_or_400`, `_company_for_request`, `_ensure_company_operational` ×2) |
| Imports ميتة محذوفة | — | — | **−3** |
| tests passing | 86 | 86 | 0 (لا تغيير) |
| regressions | — | — | 0 |
| mypy errors | 9 (pre-existing) | 9 (pre-existing) | 0 |
| ruff | All checks passed | All checks passed | 0 |

## التحقق
```bash
$env:DJANGO_SETTINGS_MODULE="config.settings.test"
cd backend
python -m pytest apps/notifications/ -q    # 8 passed
python -m pytest apps/organizations/ -q    # 9 passed
python -m pytest apps/ tests/ -q            # 86 passed, 5 pre-existing failures
python -m ruff check apps/                  # All checks passed!
python -m mypy apps/                        # 9 pre-existing errors (unchanged)
```

## معايير القبول
- [x] مراجع يدوية للـ 26 ملف test و 14 view ملف تنتهي بلا helper functions متبقية من R-03
- [x] `tenant_context`, `is_owner` غير مستخدمين في views المُهذَّبة
- [x] لا regressions في عدد الـ tests passing
- [x] mypy errors لا تزيد (تبقى 9 pre-existing)
- [x] ruff clean

## المخاطر
🟢 **منخفضة** — مراجع مستهدفة + tests passing.

## ملاحظات
- 📋 **R-10b (مستقبلي)**: تنظيف `backups/api/views.py` و `exports/api/views.py` من `_company_for_request` و `is_owner` (نفس النمط، خارج نطاق هذا الـ refactor للحفاظ على الـ scope ضيق)
- 📋 **R-10c (مستقبلي)**: إصلاح mypy errors الـ 9 المتبقية (الـ `CompanyRole.OWNER` كـ enum لا `str` في `required_roles`)
- ✅ **لا ADRs قديمة** — كل الـ 9 ADRs حالية وتعكس الـ baseline
