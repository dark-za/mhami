# BE-05: Results Log

## 1. Completion Summary

| Item | Value |
|---|---|
| Start Date | YYYY-MM-DD |
| End Date | YYYY-MM-DD |
| Number of Commits | N |
| Helper exists | yes |
| Auth backend calls it | 4 paths |
| Tests | 5 passed |
| INFRA-04 alert | wired |
| No plaintext | confirmed |

## 2. Verification

| Command | Result | Exit Code |
|---|---|---|
| `pytest apps/tenancy/tests/test_login_failure_audit.py` | 5 passed | 0 |
| `pytest -m "not slow"` | green | 0 |

## 3. Git Changes

```
<commit-sha-1> BE-05: log failed login attempts
  - Add record_login_failure in apps/tenancy/services.py
  - Wire into auth_backends.py (4 paths)
  - Add apps/tenancy/tests/test_login_failure_audit.py
  - Confirm INFRA-04 LoginFailuresHigh alert
```

## 4. Before/After

### `apps/tenancy/services.py`

```diff
+ def record_login_failure(request, login_id, reason, company_id=None) -> None:
+     write_audit_event(
+         event="LOGIN_FAILED",
+         actor=None,
+         company_id=company_id,
+         context={...}
+     )
```

### `apps/tenancy/auth_backends.py`

```diff
+ from apps.tenancy.services import record_login_failure
  def authenticate(self, request, ...):
      try:
          company = Company.objects.get(...)
      except Company.DoesNotExist:
+         record_login_failure(request, login_id, "company_not_found")
          return None
      # ...
```

## 5. Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _________ | _________ | Complete |
| Backend Lead | _________ | _________ | Approved |
| Security Reviewer | _________ | _________ | Verified |
| Tech Lead | _________ | _________ | Approved |
