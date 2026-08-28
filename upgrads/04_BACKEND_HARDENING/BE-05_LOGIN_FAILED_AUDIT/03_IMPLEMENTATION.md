# BE-05: Implementation Guide

## Step 1: Helper

### 1.1 New file (or extend) `backend/apps/tenancy/services.py`

```python
import hashlib
from apps.audit.services import write_audit_event


def record_login_failure(request, login_id: str, reason: str, company_id=None) -> None:
    """Record a failed login attempt in the audit chain."""
    write_audit_event(
        event="LOGIN_FAILED",
        actor=None,
        company_id=company_id,
        context={
            "login_id_hash": hashlib.sha256((login_id or "").encode("utf-8")).hexdigest(),
            "company_code_hash": hashlib.sha256(
                (request.POST.get("company_code", "") or "").encode("utf-8")
            ).hexdigest(),
            "reason": reason,
            "ip": request.META.get("REMOTE_ADDR", ""),
            "ua": request.META.get("HTTP_USER_AGENT", ""),
        },
    )
```

## Step 2: Wire into auth backend

### 2.1 File: `backend/apps/tenancy/auth_backends.py`

```python
def authenticate(self, request, company_code=None, login_id=None, password=None, **kwargs):
    from apps.tenancy.services import record_login_failure
    from apps.tenancy.models import Company, CompanyStatus

    try:
        company = Company.objects.get(code=company_code)
    except Company.DoesNotExist:
        record_login_failure(request, login_id, "company_not_found")
        return None

    user = User.objects.filter(login_id=login_id).first()
    if not user or not user.check_password(password):
        record_login_failure(request, login_id, "invalid_credentials", company_id=company.id)
        return None

    if company.status in {CompanyStatus.SUSPENDED, CompanyStatus.TRIAL_EXPIRED}:
        record_login_failure(request, login_id, "company_unavailable", company_id=company.id)
        return None

    if user.is_locked_out():
        record_login_failure(request, login_id, "locked_account", company_id=company.id)
        return None
    # ...
```

## Step 3: Tests

### 3.1 New file: `backend/apps/tenancy/tests/test_login_failure_audit.py`

```python
"""Failed login attempts are recorded in the audit chain."""
from __future__ import annotations

import pytest

from apps.audit.models import AuditEvent
from apps.tenancy.services import record_login_failure

pytestmark = pytest.mark.django_db


class _Req:
    def __init__(self, company_code="", ip="127.0.0.1", ua="agent"):
        self.POST = {"company_code": company_code}
        self.META = {"REMOTE_ADDR": ip, "HTTP_USER_AGENT": ua}


def test_company_not_found():
    req = _Req(company_code="missing")
    record_login_failure(req, "alice", "company_not_found")
    e = AuditEvent.objects.filter(event="LOGIN_FAILED", context__reason="company_not_found").first()
    assert e is not None
    assert e.context["login_id_hash"]  # hashed, not plaintext


def test_invalid_password(make_company):
    co = make_company(code="co")
    req = _Req(company_code="co")
    record_login_failure(req, "alice", "invalid_credentials", company_id=co.id)
    e = AuditEvent.objects.filter(event="LOGIN_FAILED", context__reason="invalid_credentials").first()
    assert e is not None


def test_company_unavailable(make_company):
    co = make_company(code="co", status="suspended")
    req = _Req(company_code="co")
    record_login_failure(req, "alice", "company_unavailable", company_id=co.id)
    e = AuditEvent.objects.filter(event="LOGIN_FAILED", context__reason="company_unavailable").first()
    assert e is not None


def test_locked_account():
    req = _Req()
    record_login_failure(req, "alice", "locked_account")
    e = AuditEvent.objects.filter(event="LOGIN_FAILED", context__reason="locked_account").first()
    assert e is not None


def test_no_plaintext_password():
    req = _Req()
    record_login_failure(req, "alice", "invalid_credentials")
    e = AuditEvent.objects.get(event="LOGIN_FAILED")
    assert "password" not in str(e.context).lower()
```

**Verify:**
```bash
cd backend
pytest apps/tenancy/tests/test_login_failure_audit.py -v
# Expected: 5 passed
```

## Step 4: INFRA-04 alert

`infra/monitoring/prometheus/alerts/business.yml` already has `LoginFailuresHigh` (from INFRA-04). Confirm:

```bash
Select-String -Path infra/monitoring/prometheus/alerts/business.yml -Pattern "LoginFailuresHigh"
# Expected: 1 match
```

## Step 5: Docs

1. Update `CHANGELOG.md` with a `BE-05` entry.
2. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Helper exists | `grep "def record_login_failure" backend/apps/tenancy/services.py` | match |
| Auth backend calls it | `grep "record_login_failure" backend/apps/tenancy/auth_backends.py` | 3+ matches |
| Tests pass | `pytest apps/tenancy/tests/test_login_failure_audit.py` | 5 passed |
| No plaintext | test_no_plaintext_password | passed |
