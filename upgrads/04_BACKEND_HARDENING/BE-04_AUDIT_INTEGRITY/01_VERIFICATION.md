# BE-04: Verification Commands

## Phase 1: Pre-Fix

```bash
# 1. Count AuditEvent writers
Select-String -Path backend/apps -Pattern "AuditEvent\.objects\.create" -Recurse | Measure-Object | Select-Object -ExpandProperty Count

# 2. Find deletes
Select-String -Path backend/apps -Pattern "AuditEvent\.objects\.delete" -Recurse
# Expected today: 0 (delete is forbidden) — confirm

# 3. Find updates
Select-String -Path backend/apps -Pattern "AuditEvent\.objects\.update" -Recurse
# Expected today: 0 — confirm
```

## Phase 2: Post-Fix

```bash
# 1. AuditEvent.save() wraps in transaction
Select-String -Path backend/apps/audit/models.py -Pattern "transaction\.atomic|select_for_update"
# Expected: 2+ matches

# 2. AuditEvent.delete() raises
cd backend
python -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'; import django; django.setup(); from apps.audit.models import AuditEvent; from apps.identity.models import User; u = User.objects.first(); e = AuditEvent.objects.create(event='test', actor=u); e.delete()" 2>&1 | Select-String -Pattern "PermissionError"
# Expected: 1 match

# 3. verify_integrity detects tampering
cd backend
pytest apps/audit/tests/test_audit_chain_hardening.py -v
# Expected: passed

# 4. Release smoke
cd backend
python -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'; import django; django.setup(); from apps.audit.services import verify_chain; print(verify_chain())"
# Expected: True
```

## Phase 3: Regression

```bash
cd backend
pytest apps/audit/tests/ -v
# Expected: green
pytest -m "not slow" -q
# Expected: green
```
