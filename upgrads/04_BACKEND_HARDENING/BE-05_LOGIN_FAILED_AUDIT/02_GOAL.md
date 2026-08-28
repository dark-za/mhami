# BE-05: Goal and Plan

## SMART Goal

> Within **1 day**, add `record_login_failure(request, login_id, reason, company_id=None)` and call it on every authentication failure path. The `LoginFailuresHigh` alert is wired.

## Acceptance Standards

### Standard 1: Helper

```python
# apps/tenancy/services.py
import hashlib
from apps.audit.services import write_audit_event

def record_login_failure(request, login_id, reason, company_id=None):
    write_audit_event(
        event="LOGIN_FAILED",
        actor=None,
        context={
            "login_id_hash": hashlib.sha256((login_id or "").encode("utf-8")).hexdigest(),
            "company_code_hash": hashlib.sha256((request.POST.get("company_code", "") or "").encode("utf-8")).hexdigest(),
            "reason": reason,
            "ip": request.META.get("REMOTE_ADDR", ""),
            "ua": request.META.get("HTTP_USER_AGENT", ""),
        },
        company_id=company_id,
    )
```

### Standard 2: Auth backend integration

```python
# apps/tenancy/auth_backends.py
def authenticate(self, request, company_code=None, login_id=None, password=None, **kwargs):
    try:
        company = Company.objects.get(code=company_code)
    except Company.DoesNotExist:
        record_login_failure(request, login_id, "company_not_found")
        return None

    user = User.objects.filter(login_id=login_id).first()
    if not user or not user.check_password(password):
        record_login_failure(request, login_id, "invalid_credentials", company_id=company.id)
        return None

    if company.status in {CompanyStatus.SUSPENDED, ...}:
        record_login_failure(request, login_id, "company_unavailable", company_id=company.id)
        return None
    # ...
```

### Standard 3: Tests

| Test | Expected |
|---|---|
| `test_company_not_found_writes_audit` | 1 LOGIN_FAILED row |
| `test_invalid_password_writes_audit` | 1 LOGIN_FAILED row |
| `test_company_unavailable_writes_audit` | 1 LOGIN_FAILED row |
| `test_locked_account_writes_audit` | 1 LOGIN_FAILED row |
| `test_successful_login_does_not_write_audit` | 0 LOGIN_FAILED rows |

### Standard 4: INFRA-04 alert

`LoginFailuresHigh` fires when `rate(mhami_login_failures_total[5m]) > 5`.

---

## Implementation Plan

### Day 1

- [ ] Add `record_login_failure` helper.
- [ ] Wire into auth backend.
- [ ] Add tests.
- [ ] Confirm INFRA-04 alert.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | Helper exists |
| CP-2 | Auth backend calls it |
| CP-3 | Tests pass |
| CP-4 | Alert wired |
