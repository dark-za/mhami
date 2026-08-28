# BE-02: Implementation Guide

> **Golden Rule:** every change is documented with a diff and a verification command. The helper is the single source of truth for cross-tenant reference validation.

## Step 1: Confirm the helper

### 1.1 File: `backend/apps/tenancy/access.py`

```python
def validate_company_reference(company, model, pk, field_name="id"):
    """Validate that a record with given pk belongs to the company.

    Raises PlatformPermissionException if not.
    """
    if not model.objects.filter(pk=pk, company=company).exists():
        raise PlatformPermissionException(
            f"Referenced {model.__name__} is outside the active company."
        )
```

**Verify:**
```bash
Select-String -Path backend\apps\tenancy\access.py -Pattern "def validate_company_reference"
# Expected: 1 match
```

---

## Step 2: Audit script

### 2.1 New file: `backend/scripts/ci/audit_serializer_validation.py`

```python
"""Audit every serializer that takes an external ID for validate_company_reference."""
from __future__ import annotations

import ast
import pathlib
import sys


def check_file(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text())
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Find ID fields
        id_fields: list[str] = []
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for tgt in stmt.targets:
                    if isinstance(tgt, ast.Name) and tgt.id.endswith("_id"):
                        id_fields.append(tgt.id)
        if not id_fields:
            continue
        # Find validate_<field> methods that call validate_company_reference
        for fname in id_fields:
            validate_method = f"validate_{fname}"
            found = False
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == validate_method:
                    src = ast.unparse(stmt)
                    if "validate_company_reference" in src:
                        found = True
            if not found:
                errors.append(f"{path}:{node.lineno} {node.name} missing {validate_method}")
    return errors


def main() -> int:
    errs: list[str] = []
    for f in pathlib.Path("apps").rglob("serializers.py"):
        errs.extend(check_file(f))
    if errs:
        for e in errs:
            print(f"MISSING: {e}")
        return 1
    print(f"OK: cross-tenant validation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Verify:**
```bash
cd backend
python scripts/ci/audit_serializer_validation.py
echo "Exit code: $LASTEXITCODE"
# Today: 1 (gaps). After all fixes: 0.
```

---

## Step 3: Add `validate_company_reference` to every serializer

### 3.1 Pattern

```python
# Before
class MyCreateSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    # ...

# After
class MyCreateSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._company = company

    def validate_branch_id(self, value):
        validate_company_reference(self._company, Branch, value)
        return value
```

### 3.2 Update the view

```python
class MyView(TenantAPIView):
    required_roles = (CompanyRole.OWNER,)
    def post(self, request):
        serializer = MyCreateSerializer(data=request.data, company=request.company)
        serializer.is_valid(raise_exception=True)
        # ...
```

### 3.3 Files to update

| File | Fields to validate |
|---|---|
| `apps/tasks/api/serializers.py` | `branch_id`, `user_id`, `template_id` |
| `apps/evidence/api/serializers.py` | `capture_id`, `task_id` |
| `apps/reviews/api/serializers.py` | `decision_id`, `policy_id` |
| `apps/exports/api/serializers.py` | `company_id` (cross-checks with `validate_company_reference`) |
| `apps/backups/api/serializers.py` | `restore_run_id` |
| `apps/tenancy/api/serializers.py` | `legal_document_version_id` |

---

## Step 4: Cross-tenant reference tests

### 4.1 New file: `backend/apps/tenancy/tests/test_validate_company_reference.py`

```python
"""Cross-tenant reference validation."""
from __future__ import annotations

import pytest

from apps.tenancy.access import validate_company_reference
from apps.tenancy.models import Company
from apps.organizations.models import Branch
from apps.identity.models import User

pytestmark = pytest.mark.django_db


def test_validate_company_reference_raises_on_foreign_tenant(make_company, make_branch, make_user):
    co_a = make_company(code="co-a")
    co_b = make_company(code="co-b")
    b_b = make_branch(company=co_b, code="b-b")
    with pytest.raises(Exception) as exc:
        validate_company_reference(co_a, Branch, b_b.id)
    assert "outside" in str(exc.value).lower()


def test_validate_company_reference_accepts_own_tenant(make_company, make_branch):
    co = make_company(code="co")
    b = make_branch(company=co, code="b")
    validate_company_reference(co, Branch, b.id)  # no exception
```

### 4.2 Per-serializer test pattern

For each (serializer, field, model), add a test:

```python
def test_<serializer>_<field>_rejects_foreign_tenant(make_company, force_login_company, ...):
    co_a = make_company(code="co-a")
    co_b = make_company(code="co-b")
    target = <Model>.objects.create(company=co_b, ...)
    owner = make_user(login_id="owner-a")
    co_a_with_owner = make_company(owner=owner, code="co-a-real")
    client = force_login_company(owner, co_a_with_owner)
    res = client.post(<url>, data={<field>: target.id}, format="json")
    assert res.status_code in (403, 404)
```

Aim for **≥20 such tests** across the 9 field/model pairs.

---

## Step 5: CI integration

Add to `.github/workflows/ci.yml`:

```yaml
  serializer-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - name: Audit serializer validation
        run: |
          cd backend
          pip install -r requirements.txt
          python scripts/ci/audit_serializer_validation.py
```

**Verify:**
```bash
Get-Content .github\workflows\ci.yml | Select-String -Pattern "serializer-audit"
# Expected: 1+ match
```

---

## Step 6: Threat model + docs

1. Update `docs/SECURITY_THREAT_MODEL.md` (A01 control).
2. Update `CHANGELOG.md` with a `BE-02` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Audit script exists | `Test-Path backend\scripts\ci\audit_serializer_validation.py` | True |
| Audit exits 0 | `python scripts/ci/audit_serializer_validation.py` | 0 |
| Cross-tenant tests | `pytest -k cross_tenant` | ≥ 20 passed |
| No regression | `pytest -m "not slow"` | green |
| Threat model | `grep validate_company_reference docs/SECURITY_THREAT_MODEL.md` | match |

---

## Rollback

```bash
git revert <be02-commit-sha>
cd backend
python scripts/ci/audit_serializer_validation.py
# Expected: non-zero (the audit will flag the reverted serializers)
```
