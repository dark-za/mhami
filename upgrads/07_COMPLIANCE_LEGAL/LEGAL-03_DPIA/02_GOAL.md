# LEGAL-03: Goal and Plan

## SMART Goal

> Within **2 weeks**, write `docs/DPIA.md` covering the 4 high-risk
> activities (face image, AI analysis, cloud transfer, backups),
> implement a structured risk register, and add an annual review.

## Acceptance Standards

### Standard 1: DPIA structure

Each activity has:

- **Description** (nature, scope, context, purpose)
- **Necessity assessment** (is the processing necessary)
- **Risk assessment** (for each data subject right)
- **Mitigation measures** (technical + organizational)
- **Consultation** (DPO + stakeholders + counsel)

### Standard 2: Activities covered

| # | Activity | Why high-risk |
|---|---|---|
| 1 | Face image capture | Sensitive biometric |
| 2 | AI analysis (external) | Cross-border transfer + automated decision support |
| 3 | Cloud hosting | Cross-border transfer |
| 4 | Backups | Cross-border transfer + retention |

### Standard 3: Model

```python
class DPIARisk(models.Model):
    activity = models.CharField(max_length=200)
    description = models.TextField()
    likelihood = models.CharField(max_length=16)  # low/medium/high
    impact = models.CharField(max_length=16)
    residual_likelihood = models.CharField(max_length=16)
    residual_impact = models.CharField(max_length=16)
    mitigation = models.TextField()
    mitigation_upgrade = models.CharField(max_length=64, blank=True)  # C-13, INFRA-05, ...
    owner = models.CharField(max_length=200)
    review_date = models.DateField()
```

### Standard 4: Annual reminder

Celery task `annual_dpia_review` runs every 365 days and writes a reminder.

### Standard 5: DPO sign-off

The DPIA's `effective_date` and `signed_by` are recorded; any change requires a new sign-off.

---

## Implementation Plan

### Week 1 — DPIA

- [ ] Draft `docs/DPIA.md` (4 activities, 5 sections each).
- [ ] DPO + Counsel review.

### Week 2 — Model + reminder

- [ ] Add `DPIARisk` model + data migration.
- [ ] Add annual reminder.
- [ ] Cross-link to existing upgrades (C-13, INFRA-03, INFRA-05, H-03).
- [ ] Update `CHANGELOG.md`.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | DPIA drafted |
| CP-2 | DPIA approved |
| CP-3 | Model + reminder |
| CP-4 | Cross-links |
| CP-5 | Docs updated |

---

## Cancellation Criteria

- If a mitigation is not actually implemented → link to the upgrade ticket; do not mark the risk "mitigated" without evidence.
