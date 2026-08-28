# LEGAL-02: Goal and Plan

## SMART Goal

> Within **1 week**, write `docs/ROPA.md` covering every processing
> activity, add the `ProcessingActivity` model, expose a read-only
> API, and add a quarterly review reminder.

## Acceptance Standards

### Standard 1: ROPA structure

```markdown
# ROPA - Record of Processing Activities

## Activity 1: Company Registration
- **Name:** Company Registration
- **Purpose:** Onboarding new tenants
- **Controller:** Platform (acting as processor for the tenant)
- **Recipient:** Mhami Operations
- **Data categories:** Company name, code, contact info, owner credentials
- **Data subject categories:** Business owners
- **Recipients:** Internal only
- **Cross-border transfer:** No
- **Retention period:** Duration of contract + 90 days
- **Legal basis:** Contract performance, legitimate interest
- **Security measures:** Encryption at rest, TLS in transit, MFA
- **Last reviewed:** YYYY-MM-DD
```

### Standard 2: Model

```python
class ProcessingActivity(models.Model):
    name = models.CharField(max_length=200)
    purpose = models.TextField()
    legal_basis = models.CharField(max_length=200)
    data_categories = models.JSONField()
    recipients = models.JSONField()
    retention_days = models.IntegerField()
    cross_border = models.BooleanField(default=False)
    last_reviewed = models.DateField()
```

### Standard 3: API

`GET /api/v1/compliance/ropa/` is read-only, public (no auth required for transparency), returns all activities.

### Standard 4: Quarterly reminder

Celery beat task `quarterly_ropa_review` runs every 90 days and writes a reminder to the audit chain:

```
event="ROPA_REVIEW_DUE"
actor=null
context={"due_for": [...], "due_in_days": N}
```

### Standard 5: ≥10 activities

The ROPA must cover (at minimum): Company Registration, User Account, Authentication, MFA, Evidence Capture, AI Analysis (Shadow), Review Decision, Export, Backup, Audit Log.

---

## Implementation Plan

### Day 1-2 — ROPA + model

- [ ] Write `docs/ROPA.md`.
- [ ] Add `ProcessingActivity` model.
- [ ] Add a data migration that loads the ROPA from the markdown.

### Day 3 — API

- [ ] Add `GET /api/v1/compliance/ropa/`.
- [ ] Tests.

### Day 4 — Reminder

- [ ] Add `quarterly_ropa_review` Celery task.
- [ ] Wire into `CELERY_BEAT_SCHEDULE`.

### Day 5 — Docs

- [ ] Update `CHANGELOG.md`.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | ROPA file + model |
| CP-2 | API live |
| CP-3 | Reminder scheduled |
| CP-4 | Docs updated |

---

## Cancellation Criteria

- If a processing activity is missing → add it to the ROPA; do not skip.
- If a transfer is cross-border and the destination is not yet approved → flag the activity; do not silently ship.
