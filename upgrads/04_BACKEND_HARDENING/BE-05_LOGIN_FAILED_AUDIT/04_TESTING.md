# BE-05: Test Strategy

> **Rule:** every failure path writes an audit row; no plaintext password is stored.

## 1. Unit Tests

```bash
cd backend
pytest apps/tenancy/tests/test_login_failure_audit.py -v
# Expected: 5 passed
```

## 2. Integration Tests

### 2.1 End-to-end failure path

```bash
cd backend
pytest apps/tenancy/tests/test_auth_backends.py -v
# Expected: each failure path writes 1 LOGIN_FAILED row
```

### 2.2 No regression

```bash
cd backend
pytest -m "not slow" -q
# Expected: green
```

## 3. End-to-End Tests

### 3.1 Brute-force scenario

```bash
cd backend
for i in $(seq 1 20); do
  python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'
import django; django.setup()
from apps.tenancy.services import record_login_failure
class R:
  POST = {'company_code': 'co'}
  META = {'REMOTE_ADDR': '1.2.3.4', 'HTTP_USER_AGENT': 'curl'}
record_login_failure(R, 'alice', 'invalid_credentials')
"
done

# Verify count
python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'
import django; django.setup()
from apps.audit.models import AuditEvent
print(AuditEvent.objects.filter(event='LOGIN_FAILED').count())
"
# Expected: 20
```

## 4. Success Criteria

| Test | Count | Expected Result |
|---|---|---|
| `test_company_not_found` | 1 | passed |
| `test_invalid_password` | 1 | passed |
| `test_company_unavailable` | 1 | passed |
| `test_locked_account` | 1 | passed |
| `test_no_plaintext_password` | 1 | passed |
| E2E brute-force | 20 | 20 rows |
| No regression | N | green |

## 5. Cross-links

- [upgrads/04_BACKEND_HARDENING/BE-04_AUDIT_INTEGRITY](..)
- [upgrads/05_INFRASTRUCTURE/INFRA-04_PROMETHEUS_GRAFANA](../05_INFRASTRUCTURE/INFRA-04_PROMETHEUS_GRAFANA/00_DISCOVERY.md) — alert
