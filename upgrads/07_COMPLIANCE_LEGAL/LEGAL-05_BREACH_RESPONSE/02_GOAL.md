# LEGAL-05: Goal and Plan

## SMART Goal

> Within **1 week**, write `docs/BREACH_RESPONSE.md`, implement
> `BreachIncident` model, add severity levels, notification templates,
> and link to runbooks (DOC-03).

## Acceptance Standards

### Standard 1: Document structure

```markdown
# Data Breach Response Plan

## Definition
A data breach is any incident leading to unauthorized access, loss,
alteration, or disclosure of personal data, or a failure of
confidentiality, integrity, or availability.

## Severity levels
- **Critical (P0):** > 1000 data subjects
- **High (P1):** 100 - 1000 data subjects
- **Medium (P2):** < 100 data subjects

## Response timeline
- **0-1 hour:** Containment + notify CISO
- **1-24 hours:** Investigation + impact assessment
- **24-72 hours:** Notify SDAIA (if P0/P1)
- **72 hours-7 days:** Notify data subjects
- **7-30 days:** Root cause analysis + improvements

## Response team
- Incident Commander
- Security Lead
- DPO
- Legal Counsel
- Communications
- Platform Owner

## Notification templates
### SDAIA template
> <drafted by counsel>

### Data subject template
> <drafted by counsel>
```

### Standard 2: Model

```python
class BreachIncident(models.Model):
    SEVERITY = [("CRITICAL", "P0"), ("HIGH", "P1"), ("MEDIUM", "P2")]
    STATUS = [("detected", "Detected"), ("contained", "Contained"), ("investigating", "Investigating"), ("notified", "Notified"), ("closed", "Closed")]
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

### Standard 3: Tests

| Test | Expected |
|---|---|
| `test_breach_creation` | 1 row + audit |
| `test_severity_required` | 400 if missing |
| `test_sdaia_notification_window` | alert if not notified within 72h of detection |
| `test_status_transitions` | detected → contained → investigating → notified → closed |

---

## Implementation Plan

### Day 1 — Document

- [ ] Write `docs/BREACH_RESPONSE.md` with counsel.

### Day 2-3 — Model + API

- [ ] Add `BreachIncident` model.
- [ ] Add API.

### Day 4 — Notification + tests

- [ ] SDAIA + data subject templates.
- [ ] Celery reminder at 72h.
- [ ] Tests.

### Day 5 — Docs

- [ ] Cross-link to runbooks.
- [ ] Update `CHANGELOG.md`.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | Document drafted |
| CP-2 | Model + API |
| CP-3 | Templates |
| CP-4 | 72h reminder |
| CP-5 | Runbook linked |
| CP-6 | Docs updated |

---

## Cancellation Criteria

- If counsel delays the templates → keep an internal placeholder; do not delay the model.
