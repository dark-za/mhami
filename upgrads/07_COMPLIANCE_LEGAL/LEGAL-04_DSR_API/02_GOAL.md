# LEGAL-04: Goal and Plan

## SMART Goal

> Within **1 week**, implement `DSRRequest` model, web form, email
> verification, DPO dashboard, and SLA tracking. All actions are audited.

## Acceptance Standards

### Standard 1: Rights covered

| Right | Action |
|---|---|
| Access | export subject's data |
| Rectification | mark fields for correction |
| Erasure | soft-delete + tombstone |
| Restriction | freeze processing |
| Portability | export in machine-readable format |
| Object | suspend processing for the purpose |

### Standard 2: Model

```python
class DSRRequest(models.Model):
    subject_email = models.EmailField()
    subject_user = models.ForeignKey("identity.User", null=True, blank=True, on_delete=models.SET_NULL)
    request_type = models.CharField(max_length=32)  # ACCESS, RECTIFICATION, ...
    status = models.CharField(max_length=32)  # pending_verification, verified, in_progress, completed, rejected
    notes = models.TextField(blank=True)
    sla_due_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey("identity.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_dsrs")
```

### Standard 3: SLA

- 30 days from `created_at`.
- A Celery reminder fires 7 days before due (`DSR_SLA_DUE`).

### Standard 4: Audit

Each DSR action is recorded:

- `DSR_REQUEST_CREATED`
- `DSR_VERIFIED`
- `DSR_IN_PROGRESS`
- `DSR_COMPLETED`
- `DSR_REJECTED`

### Standard 5: DPO dashboard

`GET /api/v1/compliance/dsr/` lists requests (DPO only). Filters: status, type, sla_due.

---

## Implementation Plan

### Day 1-2 — Model + API

- [ ] Add `DSRRequest` model.
- [ ] Add `POST /api/v1/compliance/dsr/`.
- [ ] Email verification.

### Day 3 — DPO dashboard

- [ ] `GET /api/v1/compliance/dsr/`.
- [ ] Frontend DPO page.

### Day 4 — SLA + tests

- [ ] Celery reminder.
- [ ] Tests.

### Day 5 — Docs

- [ ] Update `CHANGELOG.md`.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | Model + POST |
| CP-2 | Email verification |
| CP-3 | DPO dashboard |
| CP-4 | SLA reminder |
| CP-5 | Docs |

---

## Cancellation Criteria

- If identity verification cannot be done remotely → require in-person or video verification; do not skip.
- If erasure breaks referential integrity → use soft-delete + tombstone; document the cascade.
