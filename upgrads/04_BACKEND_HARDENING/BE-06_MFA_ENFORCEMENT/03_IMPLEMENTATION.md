# BE-06: Implementation Guide

## Step 1: Settings

### 1.1 `backend/config/settings/prod.py`

```python
MFA_ENFORCEMENT_ENABLED = True
```

### 1.2 `backend/config/settings/dev.py`

```python
MFA_ENFORCEMENT_ENABLED = os.environ.get("MFA_ENFORCEMENT_ENABLED", "False") == "True"
```

### 1.3 `backend/config/settings/test.py`

```python
MFA_ENFORCEMENT_ENABLED = True
```

**Verify:**
```bash
Select-String -Path backend\config\settings\prod.py -Pattern "MFA_ENFORCEMENT_ENABLED = True"
Select-String -Path backend\config\settings\dev.py -Pattern "MFA_ENFORCEMENT_ENABLED"
# Expected: 1 match each
```

## Step 2: Middleware

### 2.1 `backend/config/settings/base.py` — confirm registered

```python
MIDDLEWARE = [
    # ... existing ...
    "apps.identity.middleware.MFAEnforcementMiddleware",
]
```

### 2.2 `backend/apps/identity/middleware.py`

```python
from django.conf import settings
from django.http import JsonResponse


def is_state_changing(request) -> bool:
    return request.method in {"POST", "PUT", "PATCH", "DELETE"}


def has_owner_role(user, company_id) -> bool:
    if not company_id:
        return False
    from apps.organizations.models import CompanyMembership, CompanyRole
    return CompanyMembership.objects.filter(
        user=user, company_id=company_id, role=CompanyRole.OWNER, active=True,
    ).exists()


def has_verified_mfa(user) -> bool:
    return user.mfa_devices.filter(verified_at__isnull=False).exists()


class MFAEnforcementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "MFA_ENFORCEMENT_ENABLED", False):
            return self.get_response(request)
        if not request.user.is_authenticated:
            return self.get_response(request)
        if not is_state_changing(request):
            return self.get_response(request)
        is_privileged = request.user.is_staff or has_owner_role(
            request.user, request.session.get("company_id")
        )
        if not is_privileged:
            return self.get_response(request)
        if not has_verified_mfa(request.user):
            return JsonResponse(
                {"detail": "MFA enrollment required", "redirect": "/mfa/enroll"},
                status=403,
            )
        return self.get_response(request)
```

## Step 3: Tests

### 3.1 New file: `backend/apps/identity/tests/test_mfa_enforcement.py`

```python
"""MFA enforcement middleware."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def test_enrolled_user_can_post(make_user, make_company, force_login_company, settings):
    settings.MFA_ENFORCEMENT_ENABLED = True
    owner = make_user(login_id="own-1", is_staff=False)
    co = make_company(owner=owner, code="co-1")
    # Mark MFA as verified
    from apps.identity.models import MFADevice
    MFADevice.objects.create(user=owner, kind="totp", verified_at="2030-01-01T00:00:00Z")
    client = force_login_company(owner, co)
    res = client.post("/api/v1/tenancy/companies/me/", data={}, content_type="application/json")
    assert res.status_code in (200, 405)


def test_unenrolled_owner_cannot_post(make_user, make_company, make_membership, force_login_company, settings):
    settings.MFA_ENFORCEMENT_ENABLED = True
    owner = make_user(login_id="own-2", is_staff=False)
    co = make_company(owner=owner, code="co-2")
    make_membership(user=owner, company=co, role="owner", active=True)
    client = force_login_company(owner, co)
    res = client.post("/api/v1/tenancy/companies/me/", data={}, content_type="application/json")
    assert res.status_code == 403
    assert res.json()["detail"] == "MFA enrollment required"


def test_unenrolled_owner_can_get(make_user, make_company, make_membership, force_login_company, settings):
    settings.MFA_ENFORCEMENT_ENABLED = True
    owner = make_user(login_id="own-3", is_staff=False)
    co = make_company(owner=owner, code="co-3")
    make_membership(user=owner, company=co, role="owner", active=True)
    client = force_login_company(owner, co)
    res = client.get("/api/v1/tenancy/companies/me/")
    assert res.status_code == 200


def test_unenrolled_employee_can_post(make_user, make_company, make_membership, force_login_company, settings):
    settings.MFA_ENFORCEMENT_ENABLED = True
    employee = make_user(login_id="emp-1", is_staff=False)
    co = make_company(code="co-4")
    make_membership(user=employee, company=co, role="employee", active=True)
    client = force_login_company(employee, co)
    res = client.post("/api/v1/tenancy/companies/me/", data={}, content_type="application/json")
    # employee is not Owner / Staff → middleware allows
    assert res.status_code in (200, 405)


def test_staff_user_required_to_have_mfa(make_user, make_company, force_login_company, settings):
    settings.MFA_ENFORCEMENT_ENABLED = True
    staff = make_user(login_id="staff-1", is_staff=True)
    co = make_company(owner=staff, code="co-5")
    client = force_login_company(staff, co)
    res = client.post("/api/v1/tenancy/companies/me/", data={}, content_type="application/json")
    assert res.status_code == 403
```

**Verify:**
```bash
cd backend
pytest apps/identity/tests/test_mfa_enforcement.py -v
# Expected: 5 passed
```

## Step 4: Frontend redirect

`frontend/src/api/client.ts` (or equivalent):

```ts
if (response.status === 403 && data?.detail === "MFA enrollment required") {
  window.location.href = data.redirect ?? "/mfa/enroll";
}
```

## Step 5: Docs

1. Update `docs/SECURITY_AND_DATA_BASELINE.md`.
2. Update `CHANGELOG.md`.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Prod default | `grep "MFA_ENFORCEMENT_ENABLED = True" backend/config/settings/prod.py` | match |
| Dev default | `grep "MFA_ENFORCEMENT_ENABLED" backend/config/settings/dev.py` | match |
| Middleware registered | `grep "MFAEnforcementMiddleware" backend/config/settings/base.py` | match |
| Tests | `pytest apps/identity/tests/test_mfa_enforcement.py` | 5 passed |
| Frontend redirect | `grep "MFA enrollment required" frontend/src` | match |
