# R-12: Tenant-aware QuerySet موحّد

> **Status:** ✅ Completed + R-12b Extended (2026-08-28) — `TenantQuerySet` + `TenantManager` مُنشَأ، **26 من 27** models تبنّت النمط (96%)، 1 view مُحدَّث. 86/91 tests passing.

## الهدف
توحيد كتابة `filter(company=..., branch__in=...)` المتكررة (102 مرة في الكود) عبر `TenantQuerySet` و `TenantManager` يكشفان `.for_company()` و `.for_company_and_branches()`.

## الوضع قبل
- ✅ `BranchQuerySet.visible_to(user)` موجود في `organizations/querysets.py` لكنه محدود
- ❌ 102 occurrences من `.filter(company=...)` في الكود
- ❌ كل view/service يُعيد كتابة `company=context.company, branch_id__in=context.branch_ids` يدوياً

## التغيير النهائي

### 1. `apps/platform_core/querysets.py` (جديد، 81 سطر)
```python
# filepath: backend/apps/platform_core/querysets.py

class TenantQuerySet(models.QuerySet):
    def for_company(self, company: "Company | UUID") -> "TenantQuerySet":
        if hasattr(company, "id"):
            return self.filter(company_id=company.id)
        return self.filter(company_id=company)

    def for_company_and_branches(
        self,
        company: "Company | UUID",
        branch_ids: "list[UUID | str] | None",
    ) -> "TenantQuerySet":
        if hasattr(company, "id"):
            company_id = company.id
        else:
            company_id = company
        if not branch_ids:
            return self.filter(company_id=company_id)
        return self.filter(company_id=company_id, branch_id__in=branch_ids)

    def for_active_company(self, company: "Company") -> "TenantQuerySet":
        from apps.tenancy.models import CompanyStatus
        return self.for_company(company).filter(
            company__status__in=(CompanyStatus.TRIAL, CompanyStatus.ACTIVE),
        )


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    """Default manager that exposes TenantQuerySet methods."""
```

### 2. Models تبنّت النمط (6 models)
| Model | File |
|---|---|
| `CaptureSession` | `apps/evidence/models.py` |
| `EvidenceItem` | `apps/evidence/models.py` |
| `TaskIssueReport` | `apps/evidence/models.py` |
| `TaskDiscussionMessage` | `apps/evidence/models.py` |
| `TaskTemplate` | `apps/tasks/models.py` |
| `TaskInstance` | `apps/tasks/models.py` |

كل واحد يحصل على `objects = TenantManager()` كـ default manager. الـ `models.Manager()` الافتراضي لـ Django يُستبدل بدون كسر backward compatibility (الـ API موحّد).

### 3. Views مُحدَّثة (1 view)
```python
# filepath: backend/apps/tasks/api/views.py:141
# قبل
instances = TaskInstance.objects.filter(
    company=context.company,
    branch_id__in=context.branch_ids,
).select_related("template", "branch", "assigned_user")

# بعد
instances = TaskInstance.objects.for_company_and_branches(
    context.company, context.branch_ids,
).select_related("template", "branch", "assigned_user")
```

### 4. `EvidenceTaskView.get` يستخدم `.for_company()` على 4 querysets
```python
# filepath: backend/apps/evidence/api/views.py:78-81
evidence = EvidenceItem.objects.for_company(company).filter(task_instance=task).order_by("sequence_number")
issues = TaskIssueReport.objects.for_company(company).filter(task_instance=task).order_by("created_at")
messages = TaskDiscussionMessage.objects.for_company(company).filter(task_instance=task).order_by("created_at")
sessions = CaptureSession.objects.for_company(company).filter(task_instance=task).order_by("created_at")
```

## ما لم يُحدَّث (ومبرر ذلك)
- **102 occurrence** متبقية من `.filter(company=...)` — كل واحدة تتطلب callsite review يدوي
- **Models بلا company FK مباشر** (`TaskTransferRequest` عبر `task_instance__company`): تستلزم منطق مختلف
- **services.py** (مستوى service): أغلب الـ queries تستخدم `company=...` كـ filter مع instance مُحمَّل سابقاً
- **views في modules أخرى** (tenancy, organizations, reviews, ai_gateway, etc.): migration إضافي خارج نطاق R-12

## الأثر الفعلي
| المقياس | قبل | بعد | الفرق |
|---|---|---|---|
| `apps/platform_core/querysets.py` | غير موجود | 81 سطر | ⭐ جديد |
| Models مع `TenantManager` | 0 | 6 | +6 |
| Views يستخدم `.for_company*()` | 0 | 2 (EvidenceTaskView, TaskInstancesView) | +2 |
| Tests passing | 86 | 86 | 0 |
| regressions | — | — | 0 |
| ruff | All checks passed | All checks passed | 0 |
| mypy | Success | Success | 0 |

## التحقق
```bash
$env:DJANGO_SETTINGS_MODULE="config.settings.test"
cd backend
python -m pytest apps/evidence/ apps/tasks/ -q    # 14 passed, 1 pre-existing failure
python -m pytest apps/ tests/ -q                   # 86 passed, 5 pre-existing failures
python -m ruff check apps/                          # All checks passed!
python -m mypy apps/platform_core/querysets.py apps/evidence/models.py apps/tasks/models.py
# Success: no issues found in 3 source files
```

## معايير القبول
- [x] `TenantQuerySet` و `TenantManager` معرّفان في `platform_core/querysets.py`
- [x] 6 models تبنّت `TenantManager`
- [x] 2 views يستخدمان `.for_company*()`
- [x] لا regressions
- [x] mypy و ruff نظيفان

## المخاطر
🟡 **متوسطة** (تم احتواؤها) — إضافة `objects = TenantManager()` على model موجود قد يكشف bugs في queries بدون scope. الـ 6 models التي اخترناها تم اختبارها في `evidence/tests/test_api.py` و `tasks/tests/test_api.py` (tenant isolation tests). 5 pre-existing failures لا علاقة لها بـ R-12.

## ملاحظات
- 📋 **R-12b (مستقبلي)**: تبنّي `TenantManager` للـ models المتبقية في `reviews`, `ai_gateway`, `connector_control`, `exports`, `backups`, `notifications`, `pilot`, `tenancy`, `organizations`
- 📋 **R-12c (مستقبلي)**: ترحيل الـ 102 occurrence من `.filter(company=...)` إلى `.for_company*()` على دفعات
- 📋 **R-12d (مستقبلي)**: إضافة `.for_company_and_role(company, role)` و `.for_branch(branch_id)` helpers
- ✅ الـ `TenantManager` متوافق 100% مع `models.Manager` — لا حاجة لتعديل الـ legacy code

## R-12b: Extended Adoption (2026-08-28)

### الهدف
توسيع تبني `TenantManager` للـ models المتبقية التي تحوي `company` FK.

### النتيجة
| Module | Models Adopted |
|---|---|
| `tasks/` | `TaskInstance` (R-12), `TaskSchedule` (R-12b) |
| `evidence/` | `CaptureSession`, `EvidenceItem`, `TaskIssueReport`, `TaskDiscussionMessage` (R-12) |
| `reviews/` | `ReviewPolicySetting`, `ReviewDecision` (R-12b) |
| `ai_gateway/` | `AIProviderConfig`, `AIAnalysisCriterion`, `AIAnalysisRun` (R-12b) |
| `backups/` | `BackupPolicy`, `BackupRun`, `RestoreRun` (R-12b) |
| `exports/` | `ExportBoundaryPolicy`, `ExportRequest` (R-12b) |
| `connector_control/` | `TenantConnectorEnrollment` (R-12b) |
| `notifications/` | `Notification` (R-12b) |
| `pilot/` | `PilotProgram` (R-12b) |
| `tenancy/` | `LegalAcceptance`, `SupportAuthorization` (R-12b) |
| `organizations/` | `JobRole`, `CompanyMembership`, `UserBranchMembership`, `WeeklyShift` (R-12b) |

**الإجمالي:** 26 من 27 company-scoped models تبنّت `TenantManager` (96%).
**الـ model الوحيد المتبقي:** `Branch` (يحتفظ بـ `BranchQuerySet.visible_to()` المخصص).

### الأثر الفعلي
| المقياس | قبل R-12b | بعد R-12b | الفرق |
|---|---|---|---|
| Models مع `TenantManager` | 6 (R-12) | 26 (R-12+R-12b) | **+20** |
| Coverage of company-scoped models | 22% | **96%** | +74% |
| Tests passing | 86 | 86 | 0 |
| regressions | — | — | 0 |
| ruff | All checks passed | All checks passed | 0 |

### التحقق
```bash
$env:DJANGO_SETTINGS_MODULE="config.settings.test"
cd backend
python -m pytest apps/ tests/ -q    # 86 passed, 5 pre-existing failures (لا تغيير)
python -m ruff check apps/          # All checks passed!
python -c "
import ast
from pathlib import Path
remaining = []
for p in Path('apps').rglob('models.py'):
    if 'migrations' in str(p): continue
    for node in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
        if isinstance(node, ast.ClassDef) and any(
            (isinstance(b, ast.Name) and b.id == 'Model') for b in node.bases
        ):
            body = ast.unparse(node)
            if 'company' in body and 'TenantManager' not in body:
                remaining.append(f'{p}:{node.lineno} - {node.name}')
print(f'Remaining: {len(remaining)}')
"
# Remaining: 1 (Branch only)
```

### معايير القبول
- [x] 20 model إضافي تبنّت `TenantManager` في R-12b
- [x] 26/27 models now have `TenantManager` (96%)
- [x] لا regressions في الـ tests
- [x] ruff نظيف

### الاستراتيجية لـ `Branch` (المتبقي الوحيد)
`Branch` يحتفظ بـ `BranchQuerySet` المخصص في `organizations/querysets.py` مع `visible_to(user)` للـ role-based filtering. الـ `TenantManager` و `BranchQuerySet` متعاكسان (الأول يضيف `.for_company()`، الثاني يضيف `.visible_to(user)`).

**الحل المستقبلي (R-12c):** دمج الـ QuerySets عبر composition:
```python
class BranchQuerySet(TenantQuerySet):
    def visible_to(self, user):
        if user.is_staff:
            return self
        return self.filter(company__memberships__user=user, ...)
```

ثم `Branch.objects = BranchManager.from_queryset(BranchQuerySet)()`. هذا يدمج كلا الـ APIs في manager واحد.

### ملاحظات
- 📋 **R-12c (مستقبلي)**: ترحيل الـ 102 occurrence من `.filter(company=...)` إلى `.for_company*()` على دفعات + دمج `BranchQuerySet` مع `TenantQuerySet`
- 📋 **R-12d (مستقبلي)**: إضافة `.for_company_and_role(company, role)` و `.for_branch(branch_id)` helpers
