# Section 4: Backend Hardening

## List of Fixes

| # | Title | Priority | Duration |
|---|---|---|---|
| BE-01 | Audit required_roles on every view | P0 | 1 week |
| BE-02 | Strengthen cross-tenant validation | P0 | 1 week |
| BE-03 | Comprehensive tenant isolation tests | P0 | 1 week |
| BE-04 | Audit chain review | P1 | 3 days |
| BE-05 | Log failed login attempts | P1 | 1 day |
| BE-06 | Enforce MFA for Admin/Owner | P1 | 1 week |

## BE-01: Audit required_roles (Detail)

### Discovery
Every `TenantAPIView` must declare `required_roles`.

### Scripts
```bash
# scripts/audit_required_roles.py
import os
import ast
import sys

def check_view(path):
    with open(path) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "TenantAPIView":
                    has_roles = any(
                        isinstance(t, ast.Assign)
                        and any(
                            isinstance(tg, ast.Name) and tg.id == "required_roles"
                            for tg in t.targets
                        )
                        for t in node.body
                    )
                    if not has_roles:
                        print(f"❌ {path}:{node.lineno} {node.name} missing required_roles")
                        return False
    return True

for root, dirs, files in os.walk("apps"):
    for f in files:
        if f == "views.py":
            check_view(os.path.join(root, f))
```

### Required Fixes
- `apps/reviews/api/views.py::ReviewDecisionCreateView` — add `(OWNER, MONITOR)`
- `apps/reviews/api/views.py::ReviewPolicyView` — add `(OWNER,)`
- `apps/evidence/api/views.py::EvidenceTaskView` — add `(OWNER, MONITOR, EMPLOYEE)`
- `apps/evidence/api/views.py::IssueMessagesView` — add `(OWNER, MONITOR, EMPLOYEE)`
- remaining views

## BE-02: Hardening Serializer Validation (Detail)

### General Pattern
Every serializer that takes external IDs must verify ownership.

### Helper
```python
# apps/tenancy/access.py
def validate_company_reference(company, model, pk, field_name="id"):
    """Validate that a record with given pk belongs to the company.

    Raises PlatformPermissionException if not.
    """
    if not model.objects.filter(pk=pk, company=company).exists():
        raise PlatformPermissionException(
            f"Referenced {model.__name__} is outside the active company."
        )
```

### Serializer pattern
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

## BE-03: Tenant Isolation Test Suite (Detail)

### Structure
```python
# backend/tests/test_tenant_isolation.py
import pytest
from django.test import Client

from apps.tenancy.models import Company
# ... other imports

@pytest.mark.django_db
class TestTenantIsolation:
    """Cross-tenant access attempts must fail with 403."""

    def test_company_a_cannot_read_company_b_tasks(self):
        # Setup
        client_a, _ = setup_company_with_user("a")
        _, company_b, _ = setup_company_with_user("b")
        # Action
        response = client_a.get(f"/api/v1/tasks/?company_id={company_b.id}")
        # Assert
        assert response.status_code in [403, 404]

    # ... 50+ more tests
```

## BE-04: Audit Chain Review (Detail)

### Checklist
- [ ] Every `record_audit_event` uses `select_for_update` inside transaction
- [ ] `previous_hash` uses `id` instead of `timestamp`
- [ ] `verify_integrity` tests the full chain
- [ ] No `update` on AuditEvent outside transaction
- [ ] `delete` is restricted by rule

## BE-05: Record Login Failures (Detail)

### Fix in `apps/tenancy/auth_backends.py`
```python
def authenticate(self, request, company_code=None, login_id=None, password=None, **kwargs):
    try:
        company = Company.objects.get(code=company_code)
    except Company.DoesNotExist:
        # ✅ Record the failed attempt
        record_login_failure(request, login_id, "company_not_found")
        return None

    user = User.objects.filter(login_id=login_id).first()
    if not user or not user.check_password(password):
        # ✅ Record
        record_login_failure(request, login_id, "invalid_credentials", company_id=company.id)
        return None

    if company.status in {CompanyStatus.SUSPENDED, ...}:
        record_login_failure(request, login_id, "company_unavailable")
        return None
    # ...
```

### New Audit event
```python
LOGIN_FAILED = "LOGIN_FAILED"
# metadata: {"login_id_hash": sha256, "company_code_hash": sha256, "reason": str, "ip": str}
```

## BE-06: MFA Enforcement (Detail)

### Status
- Currently: MFA is optional
- Target: mandatory for Platform Admin + Owner

### Fix
```python
# apps/identity/middleware.py
class MFAEnforcementMiddleware:
    def __call__(self, request):
        if request.user.is_authenticated:
            user = request.user
            if user.is_staff or has_owner_role(user, request.session.get("company_id")):
                if not has_verified_mfa(user):
                    if not request.path.startswith("/api/v1/auth/mfa"):
                        return JsonResponse({"detail": "MFA enrollment required"}, status=403)
        return self.get_response(request)
```

### UI flow
- After login, if user is staff/owner and no MFA → redirect to /mfa/enroll
- After enrollment, redirect to dashboard
