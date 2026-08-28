# LEGAL-02: Implementation Guide

## Step 1: ROPA file

### 1.1 New file: `docs/ROPA.md`

```markdown
# ROPA - Record of Processing Activities

> **Controller:** Mhami Operations
> **Last reviewed:** YYYY-MM-DD
> **Next review:** YYYY-MM-DD

## Activity 1: Company Registration

- **Name:** Company Registration
- **Purpose:** Onboarding new tenants
- **Controller:** Platform
- **Recipient:** Mhami Operations
- **Data categories:** Company name, code, contact info, owner credentials
- **Data subject categories:** Business owners
- **Recipients:** Internal only
- **Cross-border transfer:** No
- **Retention period:** Duration of contract + 90 days
- **Legal basis:** Contract performance, legitimate interest
- **Security measures:** Encryption at rest, TLS in transit, MFA
- **Last reviewed:** YYYY-MM-DD

## Activity 2: User Account

- **Name:** User Account
- **Purpose:** Authenticating users
- **Controller:** Platform
- **Recipient:** Mhami Operations
- **Data categories:** login_id, display_name, password_hash, MFA secret
- **Data subject categories:** Owners, Monitors, Supervisors, Employees
- **Recipients:** Internal only
- **Cross-border transfer:** No
- **Retention period:** Active + 30 days after deletion
- **Legal basis:** Contract performance
- **Security measures:** Argon2 hash, MFA, audit chain
- **Last reviewed:** YYYY-MM-DD

## Activity 3: Authentication

- **Name:** Authentication
- **Purpose:** Sign-in, session management
- **Controller:** Platform
- **Recipient:** Mhami Operations
- **Data categories:** session cookie, IP, user agent
- **Data subject categories:** All authenticated users
- **Recipients:** Internal only
- **Cross-border transfer:** No
- **Retention period:** 30 days
- **Legal basis:** Contract performance, legitimate interest (fraud prevention)
- **Security measures:** CSRF token, HttpOnly cookies
- **Last reviewed:** YYYY-MM-DD

## Activity 4: MFA

- **Name:** MFA
- **Purpose:** Second-factor authentication
- **Controller:** Platform
- **Recipient:** Mhami Operations
- **Data categories:** TOTP secret, recovery codes (hashed)
- **Data subject categories:** Privileged users (Owner, Staff)
- **Recipients:** Internal only
- **Cross-border transfer:** No
- **Retention period:** Active + 30 days
- **Legal basis:** Contract performance, legitimate interest
- **Security measures:** Argon2 for recovery codes
- **Last reviewed:** YYYY-MM-DD

## Activity 5: Evidence Capture

- **Name:** Evidence Capture
- **Purpose:** Recording work completion
- **Controller:** Tenant (per company)
- **Recipient:** Tenant + Mhami Operations
- **Data categories:** image bytes, hash, capture metadata
- **Data subject categories:** Employees (image subjects)
- **Recipients:** Tenant, Mhami Operations
- **Cross-border transfer:** No
- **Retention period:** Per tenant policy
- **Legal basis:** Contract performance, legitimate interest
- **Security measures:** HMAC signature, face-blur by default
- **Last reviewed:** YYYY-MM-DD

## Activity 6: AI Analysis (Shadow)

- **Name:** AI Analysis (Shadow Mode)
- **Purpose:** AI assistance, no autonomous decision
- **Controller:** Platform
- **Recipient:** Mhami Operations, AI provider
- **Data categories:** image hash, prompt, response
- **Data subject categories:** Employees
- **Recipients:** AI provider (anonymized)
- **Cross-border transfer:** Yes (provider region)
- **Retention period:** 30 days
- **Legal basis:** Contract performance, consent
- **Security measures:** Anonymization, audit chain
- **Last reviewed:** YYYY-MM-DD

## Activity 7: Review Decision

- **Name:** Review Decision
- **Purpose:** Quality monitoring
- **Controller:** Tenant
- **Recipient:** Tenant
- **Data categories:** decision text, approver id
- **Data subject categories:** Employees
- **Recipients:** Internal only
- **Cross-border transfer:** No
- **Retention period:** 1 year
- **Legal basis:** Contract performance
- **Security measures:** Audit chain
- **Last reviewed:** YYYY-MM-DD

## Activity 8: Export

- **Name:** Export
- **Purpose:** Data export to tenant
- **Controller:** Tenant
- **Recipient:** Tenant
- **Data categories:** per export
- **Data subject categories:** per export
- **Recipients:** Tenant only
- **Cross-border transfer:** No
- **Retention period:** 30 days
- **Legal basis:** Contract performance
- **Security measures:** Signed URL, audit chain
- **Last reviewed:** YYYY-MM-DD

## Activity 9: Backup

- **Name:** Backup
- **Purpose:** Disaster recovery
- **Controller:** Platform
- **Recipient:** Mhami Operations
- **Data categories:** full DB + media
- **Data subject categories:** all
- **Recipients:** Mhami Operations + S3 (encrypted)
- **Cross-border transfer:** Depends on region
- **Retention period:** 30 / 90 / 365 days
- **Legal basis:** Legitimate interest
- **Security measures:** Envelope encryption, SSE-KMS
- **Last reviewed:** YYYY-MM-DD

## Activity 10: Audit Log

- **Name:** Audit Log
- **Purpose:** Tamper-evident record
- **Controller:** Platform
- **Recipient:** Mhami Operations + DPO
- **Data categories:** event, actor, context
- **Data subject categories:** all
- **Recipients:** Internal only
- **Cross-border transfer:** No
- **Retention period:** 7 years
- **Legal basis:** Legal obligation
- **Security measures:** HMAC chain, append-only
- **Last reviewed:** YYYY-MM-DD
```

## Step 2: Model + data migration

### 2.1 `backend/apps/compliance/models.py`

```python
class ProcessingActivity(models.Model):
    name = models.CharField(max_length=200)
    purpose = models.TextField()
    controller = models.CharField(max_length=200)
    recipient = models.CharField(max_length=200)
    data_categories = models.JSONField()
    data_subject_categories = models.JSONField()
    recipients = models.JSONField()
    cross_border = models.BooleanField(default=False)
    retention_period = models.CharField(max_length=200)
    legal_basis = models.CharField(max_length=200)
    security_measures = models.TextField()
    last_reviewed = models.DateField()
```

### 2.2 Data migration

```bash
cd backend
python manage.py makemigrations compliance
python manage.py migrate
python manage.py loaddata compliance/fixtures/ropa.json
# OR
python manage.py load_ropa_from_markdown  # custom command
```

## Step 3: API

### 3.1 `backend/apps/compliance/api/views.py`

```python
class ROPAView(generics.ListAPIView):
    queryset = ProcessingActivity.objects.all()
    serializer_class = ProcessingActivitySerializer
    permission_classes = [AllowAny]  # public for transparency
```

### 3.2 Tests

```python
def test_ropa_endpoint_returns_activities(api_client):
    res = api_client.get("/api/v1/compliance/ropa/")
    assert res.status_code == 200
    assert len(res.json()["results"]) >= 10
```

## Step 4: Quarterly reminder

### 4.1 `backend/apps/compliance/tasks.py`

```python
from celery import shared_task
from datetime import datetime, timedelta
from apps.audit.services import write_audit_event

@shared_task
def quarterly_ropa_review():
    today = datetime.utcnow().date()
    due_in_days = 30
    due = []
    for a in ProcessingActivity.objects.all():
        if (today - a.last_reviewed).days >= 90 - due_in_days:
            due.append(a.name)
    if due:
        write_audit_event(
            event="ROPA_REVIEW_DUE",
            actor=None,
            context={"due_for": due, "due_in_days": due_in_days},
        )
```

### 4.2 `config/celery.py`

```python
app.conf.beat_schedule = {
    "quarterly-ropa-review": {
        "task": "apps.compliance.tasks.quarterly_ropa_review",
        "schedule": 60 * 60 * 24 * 90,  # every 90 days
    },
}
```

## Step 5: Docs

1. Update `docs/SECURITY_AND_DATA_BASELINE.md` (ROPA reference).
2. Update `CHANGELOG.md` with a `LEGAL-02` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| ROPA file | `Test-Path docs\ROPA.md` | True |
| ≥10 activities | `Select-String -Path docs\ROPA.md -Pattern "^## Activity"` | ≥ 10 |
| Model | `grep "class ProcessingActivity" backend/apps/compliance/models.py` | match |
| API | `curl /api/v1/compliance/ropa/` | 200, ≥ 10 |
| Reminder | `grep ROPA_REVIEW_DUE` | match |
