# BE-02: Goal and Plan

## SMART Goal

> Within **1 week**, every serializer that takes an external ID
> (`branch_id`, `user_id`, `template_id`, `policy_id`, `decision_id`,
> `capture_id`, …) calls `validate_company_reference(company, Model, value)`
> and the platform raises `PlatformPermissionException` on a foreign-tenant
> reference. Add **≥20 cross-tenant reference tests**, all green in CI.

## Detailed Acceptance Standards

### Standard 1: The helper

```python
# apps/tenancy/access.py
def validate_company_reference(company, model, pk, field_name="id"):
    """Validate that a record with given pk belongs to the company."""
    if not model.objects.filter(pk=pk, company=company).exists():
        raise PlatformPermissionException(
            f"Referenced {model.__name__} is outside the active company."
        )
```

### Standard 2: Serializer pattern

```python
class MyCreateSerializer(serializers.Serializer):
    related_id = serializers.UUIDField()

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._company = company

    def validate_related_id(self, value):
        validate_company_reference(self._company, RelatedModel, value)
        return value
```

The view passes `company=company` to the serializer. The serializer stores it in `self._company` for the per-field validators.

### Standard 3: Audit script

`backend/scripts/ci/audit_serializer_validation.py` walks every `serializers.py` under `apps/`, finds classes that declare an `id` field of type `PrimaryKeyRelatedField` or `UUIDField`, and asserts that the class has a `__init__` that takes `company` and a `validate_<field>` that calls `validate_company_reference`.

### Standard 4: Test matrix

| Field | Model | Cross-tenant test |
|---|---|---|
| `branch_id` | `Branch` | 3 tests (cross-tenant, disabled, missing) |
| `user_id` | `User` | 3 tests |
| `template_id` | `TaskTemplate` | 3 tests |
| `policy_id` | `ReviewPolicy` | 2 tests |
| `decision_id` | `ReviewDecision` | 2 tests |
| `capture_id` | `CaptureSession` | 2 tests |
| `export_id` | `ExportRequest` | 2 tests |
| `backup_id` | `BackupRun` | 3 tests |
| **Total** | | **20** |

### Standard 5: Threat model

`docs/SECURITY_THREAT_MODEL.md` adds the helper to the A01 row.

---

## Detailed Implementation Plan

### Day 1 — Audit + inventory

- [ ] Implement `scripts/ci/audit_serializer_validation.py`.
- [ ] Run the audit; collect the gap list.
- [ ] Confirm `validate_company_reference` is in `apps/tenancy/access.py`.

### Day 2-3 — Add calls

- [ ] Walk every `serializers.py` and add `validate_<field>` + `__init__(company=...)`.
- [ ] Update the corresponding views to pass `company=company`.

### Day 4-5 — Tests + CI

- [ ] Write ≥20 cross-tenant reference tests.
- [ ] Add the audit script to the existing `backend` CI job.
- [ ] Update `docs/SECURITY_THREAT_MODEL.md` and `CHANGELOG.md`.

---

## Dependency Graph

```
helper exists (Day 1)
    ↓
audit script (Day 1)
    ↓
add validate_company_reference to every serializer (Day 2-3)
    ↓
audit script exits 0
    ↓
cross-tenant tests (Day 4)
    ↓
CI + docs (Day 5)
```

---

## Checkpoints

| CP | Condition | Owner |
|---|---|---|
| CP-1 | Audit script reports the gap | Backend |
| CP-2 | Every external-ID serializer calls the helper | Backend |
| CP-3 | ≥20 cross-tenant tests pass | Backend |
| CP-4 | Threat model updated | Security Lead |
| CP-5 | Docs + CHANGELOG updated | Tech Writer |

---

## Cancellation Criteria

- If a serializer legitimately accepts a cross-tenant reference → add `cross_tenant = True` and document; do not skip the helper.
