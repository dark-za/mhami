# BE-04: Test Strategy

> **Rule:** every check is a real backend run.

## 1. Unit Tests

```bash
cd backend
pytest apps/audit/tests/test_audit_chain_tamper.py -v
# Expected: 2 passed
```

## 2. Integration Tests

```bash
cd backend
pytest apps/audit/tests/ -v
# Expected: green
```

## 3. End-to-End Tests

### 3.1 `delete()` raises

```bash
cd backend
python -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'; import django; django.setup(); from apps.audit.models import AuditEvent; from apps.identity.models import User; e = AuditEvent.objects.create(event='t', actor=User.objects.first()); e.delete()" 2>&1 | Select-String -Pattern "PermissionError"
# Expected: 1 match
```

### 3.2 Tamper detected

```bash
cd backend
pytest apps/audit/tests/test_audit_chain_tamper.py::test_verify_chain_detects_tampered_row -v
# Expected: passed
```

### 3.3 Release smoke

```bash
cd backend
pytest tests/test_release_smoke.py -v
# Expected: green
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| Tamper test | passed |
| delete() raises | confirmed |
| save() atomic | confirmed |
| Release smoke | green |
| H-08 race test | passed |

## 5. Cross-links

- [upgrads/02_HIGH_PRIORITY/H-08_AUDIT_RACE_CONDITION](../../02_HIGH_PRIORITY/H-08_AUDIT_RACE_CONDITION/00_DISCOVERY.md)
- [upgrads/06_QUALITY_ASSURANCE/QA-01_TEST_LAYERS](../06_QUALITY_ASSURANCE/QA-01_TEST_LAYERS/00_DISCOVERY.md) — release smoke
