# LEGAL-05: Implementation Guide

## Step 1: `docs/BREACH_RESPONSE.md`

```markdown
# Data Breach Response Plan

> **Effective Date:** YYYY-MM-DD
> **Owner:** DPO
> **Review:** Annual

## Definition

A **data breach** is any incident leading to:
- Unauthorized access to personal data
- Loss or alteration of personal data
- Disclosure of personal data
- Failure of confidentiality, integrity, or availability

## Severity levels

| Level | Name | Threshold |
|---|---|---|
| P0 | Critical | > 1000 data subjects |
| P1 | High | 100 - 1000 data subjects |
| P2 | Medium | < 100 data subjects |

## Response timeline

| Time | Action | Owner |
|---|---|---|
| 0 - 1 hour | Containment + notify CISO | Incident Commander |
| 1 - 24 hours | Investigation + impact assessment | Security Lead + DPO |
| 24 - 72 hours | Notify SDAIA (P0/P1) | Legal Counsel |
| 72 hours - 7 days | Notify data subjects | Communications |
| 7 - 30 days | Root cause analysis + improvements | Tech Lead |

## Response team

- **Incident Commander** — drives the response
- **Security Lead** — investigation + containment
- **DPO** — data subject + SDAIA liaison
- **Legal Counsel** — legal review
- **Communications** — external comms
- **Platform Owner** — final decision authority

## Notification templates

### SDAIA notification

> (template drafted by Legal Counsel; reviewed annually)

### Data subject notification

> (template drafted by Legal Counsel; reviewed annually)

## Runbooks

- [docs/runbooks/11_BREACH_DETECTED.md](../runbooks/11_BREACH_DETECTED.md)
- [docs/INCIDENT_RESPONSE.md](../INCIDENT_RESPONSE.md) (post-mortem template)
```

## Step 2: Model

### 2.1 `backend/apps/compliance/models.py`

```python
class BreachIncident(models.Model):
    SEVERITY = [("CRITICAL", "P0"), ("HIGH", "P1"), ("MEDIUM", "P2")]
    STATUS = [
        ("detected", "Detected"),
        ("contained", "Contained"),
        ("investigating", "Investigating"),
        ("notified", "Notified"),
        ("closed", "Closed"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=16, choices=SEVERITY)
    status = models.CharField(max_length=16, choices=STATUS, default="detected")
    affected_subjects_count = models.IntegerField(default=0)
    detected_at = models.DateTimeField(auto_now_add=True)
    contained_at = models.DateTimeField(null=True, blank=True)
    sdaia_notified_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey("identity.User", on_delete=models.SET_NULL, null=True)
```

## Step 3: Notification reminder

### 3.1 `backend/apps/compliance/tasks.py`

```python
@shared_task
def breach_sdaia_window():
    cutoff = timezone.now() - timedelta(hours=72)
    overdue = BreachIncident.objects.filter(
        severity__in=["CRITICAL", "HIGH"],
        sdaia_notified_at__isnull=True,
        detected_at__lte=cutoff,
    )
    for inc in overdue:
        write_audit_event(
            event="BREACH_SDAIA_OVERDUE",
            actor=None,
            context={"breach_id": str(inc.id), "severity": inc.severity},
        )
```

### 3.2 `CELERY_BEAT_SCHEDULE`

```python
"breach-sdaia-window": {
    "task": "apps.compliance.tasks.breach_sdaia_window",
    "schedule": 60 * 60,  # hourly
},
```

## Step 4: Tests

### 4.1 `backend/apps/compliance/tests/test_breach.py`

```python
import pytest
from apps.compliance.models import BreachIncident
from apps.audit.models import AuditEvent

pytestmark = pytest.mark.django_db


def test_breach_creation(make_user):
    u = make_user(login_id="ic")
    b = BreachIncident.objects.create(
        title="Sample breach", description="...", severity="HIGH", assigned_to=u
    )
    assert b.status == "detected"


def test_severity_required():
    from django.core.exceptions import ValidationError
    with pytest.raises(Exception):
        BreachIncident.objects.create(title="X", description="Y", severity="")


def test_sdaia_overdue_alert(make_user):
    from datetime import timedelta
    from django.utils import timezone
    u = make_user(login_id="ic-2")
    b = BreachIncident.objects.create(
        title="Old breach", description="...", severity="CRITICAL", assigned_to=u
    )
    b.detected_at = timezone.now() - timedelta(hours=80)
    b.save()
    from apps.compliance.tasks import breach_sdaia_window
    breach_sdaia_window()
    assert AuditEvent.objects.filter(event="BREACH_SDAIA_OVERDUE").count() == 1
```

## Step 5: Docs

1. Cross-link to `docs/runbooks/11_BREACH_DETECTED.md` (created in DOC-03).
2. Update `CHANGELOG.md` with a `LEGAL-05` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Document | `Test-Path docs\BREACH_RESPONSE.md` | True |
| ≥3 severity | `grep "Critical\|High\|Medium" docs/BREACH_RESPONSE.md` | ≥ 3 |
| Model | `grep "class BreachIncident" backend/apps/compliance/models.py` | match |
| Tests | `pytest apps/compliance/tests/test_breach.py` | passed |
| Runbook link | `grep "BREACH_RESPONSE" docs/runbooks/11_BREACH_DETECTED.md` | match |
