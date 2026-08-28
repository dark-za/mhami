# LEGAL-03: Implementation Guide

## Step 1: `docs/DPIA.md`

> Skeleton below; the actual risk text is written by DPO + Counsel.

```markdown
# DPIA - Data Protection Impact Assessment

> **Effective Date:** YYYY-MM-DD
> **Signed By:** <DPO name>
> **Next Review:** YYYY-MM-DD

## Activity 1: Face image capture

### Description
The platform captures images of work environments that may include faces
of employees. The client (browser) sends an informational `face_detected`
flag; the server treats the flag as **informational only** and relies on
server-side face detection + blur.

### Necessity
Required to prove task completion (e.g. "shelves stocked"). Without an
image, the tenant cannot evidence the work.

### Risk
- **Likelihood:** medium (faces may be present)
- **Impact:** high (biometric data is sensitive)
- **Residual likelihood:** low (server-side blur)
- **Residual impact:** medium (false negative leaks a face)

### Mitigation
- Server-side face detection (C-13) — server-authoritative, not client-controlled.
- Audit chain logs every blur decision.
- Per-tenant policy on face-blur.
- Linked upgrade: C-13_FACE_PRIVACY_ENFORCEMENT.

### Consultation
DPO, Counsel, Tech Lead, Platform Owner.

## Activity 2: AI analysis (external provider)

### Description
The AI Gateway forwards a hashed prompt to an external provider. The
response is shadow-only: no autonomous decision.

### Necessity
Provides additional context for the human Monitor's decision.

### Risk
- **Likelihood:** medium (cross-border transfer to provider)
- **Impact:** medium (data minimization, anonymization reduce exposure)
- **Residual likelihood:** low
- **Residual impact:** low

### Mitigation
- Anonymization before transfer.
- Owner opt-in only.
- Provider DPA.
- Audit chain logs every call.
- Linked upgrade: H-03_REAL_AI_PROVIDER.

### Consultation
DPO, Counsel, Security Lead, Tech Lead, Platform Owner.

## Activity 3: Cloud hosting (cross-border)

### Description
The platform hosts data in a region. If the region is outside Saudi
Arabia, a cross-border transfer occurs.

### Necessity
Required for performance and cost reasons.

### Risk
- **Likelihood:** high (region outside KSA)
- **Impact:** medium
- **Residual likelihood:** medium
- **Residual impact:** low

### Mitigation
- Approved cloud region (per Cloud Computing Regulatory Framework).
- Encryption at rest + in transit.
- Audit chain.
- Linked upgrade: INFRA-01_HARDENED_COMPOSE.

### Consultation
DPO, Counsel, Security Lead, Platform Owner.

## Activity 4: Backups

### Description
Backups are written to S3 with envelope encryption.

### Necessity
Disaster recovery.

### Risk
- **Likelihood:** medium (off-host storage)
- **Impact:** high (full DB + media)
- **Residual likelihood:** low (envelope encryption)
- **Residual impact:** low (key rotation)

### Mitigation
- Envelope encryption with KEK rotation.
- Restore drill (weekly).
- Linked upgrade: INFRA-03_BACKUP_S3_UPLOAD.

### Consultation
DPO, Counsel, Security Lead.
```

## Step 2: Model

### 2.1 `backend/apps/compliance/models.py`

```python
class DPIARisk(models.Model):
    activity = models.CharField(max_length=200)
    description = models.TextField()
    likelihood = models.CharField(max_length=16)
    impact = models.CharField(max_length=16)
    residual_likelihood = models.CharField(max_length=16)
    residual_impact = models.CharField(max_length=16)
    mitigation = models.TextField()
    mitigation_upgrade = models.CharField(max_length=64, blank=True)
    owner = models.CharField(max_length=200)
    review_date = models.DateField()
```

## Step 3: Annual reminder

### 3.1 `backend/apps/compliance/tasks.py`

```python
@shared_task
def annual_dpia_review():
    from apps.audit.services import write_audit_event
    write_audit_event(
        event="DPIA_REVIEW_DUE",
        actor=None,
        context={"due_in_days": 30, "owner": "DPO"},
    )
```

### 3.2 `CELERY_BEAT_SCHEDULE`

```python
"annual-dpia-review": {
    "task": "apps.compliance.tasks.annual_dpia_review",
    "schedule": 60 * 60 * 24 * 365,  # every 365 days
},
```

## Step 4: Docs

1. Update `docs/SECURITY_AND_DATA_BASELINE.md` (DPIA reference).
2. Update `CHANGELOG.md` with a `LEGAL-03` entry.
3. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| DPIA exists | `Test-Path docs\DPIA.md` | True |
| ≥4 activities | `grep "^## Activity" docs/DPIA.md` | ≥ 4 |
| Model | `grep "class DPIARisk" backend/apps/compliance/models.py` | match |
| Reminder | `grep DPIA_REVIEW_DUE` | match |
