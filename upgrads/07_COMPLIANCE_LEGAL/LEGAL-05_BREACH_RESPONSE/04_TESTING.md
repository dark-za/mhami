# LEGAL-05: Test Strategy

> **Rule:** every breach is recorded; SDAIA window is enforced; status transitions are valid.

## 1. Unit Tests

```bash
cd backend
pytest apps/compliance/tests/test_breach.py -v
# Expected: ≥ 3 passed
```

## 2. Integration Tests

```bash
cd backend
pytest apps/compliance/tests/ -v
# Expected: green
```

## 3. End-to-End Tests

### 3.1 Notification window

```bash
cd backend
python manage.py shell -c "
from datetime import timedelta
from django.utils import timezone
from apps.compliance.models import BreachIncident
b = BreachIncident.objects.create(title='old', description='x', severity='CRITICAL')
b.detected_at = timezone.now() - timedelta(hours=80)
b.save()
from apps.compliance.tasks import breach_sdaia_window
breach_sdaia_window()
"
# Verify: BREACH_SDAIA_OVERDUE row written
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| Breach creation | passed |
| Severity required | passed |
| 72h reminder | passed |
| Status transitions | passed |

## 5. Cross-links

- [upgrads/09_DOCUMENTATION/DOC-03_RUNBOOK](../09_DOCUMENTATION/DOC-03_RUNBOOK/00_DISCOVERY.md)
- [upgrads/09_DOCUMENTATION/DOC-04_INCIDENT_RESPONSE](../09_DOCUMENTATION/DOC-04_INCIDENT_RESPONSE/00_DISCOVERY.md)
