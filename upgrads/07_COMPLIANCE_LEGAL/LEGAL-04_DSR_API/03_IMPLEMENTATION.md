# LEGAL-04: Implementation Guide

## Step 1: Model

### 1.1 `backend/apps/compliance/models.py`

```python
from datetime import timedelta
from django.utils import timezone


class DSRRequest(models.Model):
    REQUEST_TYPES = [
        ("ACCESS", "Right to Access"),
        ("RECTIFICATION", "Right to Rectification"),
        ("ERASURE", "Right to Erasure"),
        ("RESTRICTION", "Right to Restriction"),
        ("PORTABILITY", "Right to Portability"),
        ("OBJECT", "Right to Object"),
    ]
    STATUS = [
        ("pending_verification", "Pending Email Verification"),
        ("verified", "Verified"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
    ]
    subject_email = models.EmailField()
    subject_user = models.ForeignKey("identity.User", null=True, blank=True, on_delete=models.SET_NULL)
    request_type = models.CharField(max_length=32, choices=REQUEST_TYPES)
    status = models.CharField(max_length=32, choices=STATUS, default="pending_verification")
    notes = models.TextField(blank=True)
    sla_due_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        "identity.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_dsrs"
    )

    def save(self, *args, **kwargs):
        if not self.sla_due_at:
            self.sla_due_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
```

## Step 2: API

### 2.1 `backend/apps/compliance/api/views.py`

```python
class DSRRequestCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        dsr = DSRRequest.objects.create(
            subject_email=request.data["email"],
            request_type=request.data["request_type"],
        )
        # Send verification email
        send_mail(
            subject="Verify your DSR request",
            message=f"Click http://example.com/dsr/verify/{dsr.id}/",
            from_email="noreply@example.com",
            recipient_list=[dsr.subject_email],
        )
        write_audit_event(
            event="DSR_REQUEST_CREATED",
            actor=None,
            context={"dsr_id": str(dsr.id), "request_type": dsr.request_type},
        )
        return Response({"id": str(dsr.id), "sla_due_at": dsr.sla_due_at}, status=201)


class DSRRequestListView(generics.ListAPIView):
    queryset = DSRRequest.objects.all()
    serializer_class = DSRRequestSerializer
    required_roles = (CompanyRole.OWNER,)  # DPO is a special Owner role

    def get_queryset(self):
        qs = super().get_queryset()
        status_ = self.request.query_params.get("status")
        if status_:
            qs = qs.filter(status=status_)
        return qs
```

## Step 3: SLA reminder

### 3.1 `backend/apps/compliance/tasks.py`

```python
@shared_task
def dsr_sla_due():
    from apps.audit.services import write_audit_event
    soon = timezone.now() + timedelta(days=7)
    due = DSRRequest.objects.filter(
        status__in=["pending_verification", "verified", "in_progress"],
        sla_due_at__lte=soon,
    )
    for d in due:
        write_audit_event(
            event="DSR_SLA_DUE",
            actor=None,
            context={"dsr_id": str(d.id), "sla_due_at": d.sla_due_at.isoformat()},
        )
```

### 3.2 `CELERY_BEAT_SCHEDULE`

```python
"dsr-sla-due": {
    "task": "apps.compliance.tasks.dsr_sla_due",
    "schedule": 60 * 60 * 24,  # every day
},
```

## Step 4: Tests

### 4.1 `backend/apps/compliance/tests/test_dsr.py`

```python
import pytest

from apps.compliance.models import DSRRequest
from apps.audit.models import AuditEvent

pytestmark = pytest.mark.django_db


def test_dsr_creation_creates_audit():
    res = client.post("/api/v1/compliance/dsr/", {"email": "x@example.com", "request_type": "ACCESS"}, format="json")
    assert res.status_code == 201
    assert AuditEvent.objects.filter(event="DSR_REQUEST_CREATED").count() == 1


def test_dsr_sla_is_30_days():
    d = DSRRequest.objects.create(subject_email="x@example.com", request_type="ACCESS")
    delta = d.sla_due_at - d.created_at
    assert delta.days >= 29


def test_dsr_list_is_dpo_only(make_user, force_login_company, make_company):
    co = make_company(code="co")
    employee = make_user(login_id="emp")
    client = force_login_company(employee, co)
    res = client.get("/api/v1/compliance/dsr/")
    assert res.status_code == 403
```

## Step 5: Docs

1. Update `CHANGELOG.md` with a `LEGAL-04` entry.
2. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| Model | `grep "class DSRRequest" backend/apps/compliance/models.py` | match |
| POST endpoint | `curl -X POST /api/v1/compliance/dsr/` | 201 |
| GET endpoint (DPO) | `curl /api/v1/compliance/dsr/` (as DPO) | 200 |
| DPO-only | `curl /api/v1/compliance/dsr/` (as employee) | 403 |
| SLA reminder | `grep DSR_SLA_DUE` | match |
| Tests | `pytest apps/compliance/tests/test_dsr.py` | passed |
