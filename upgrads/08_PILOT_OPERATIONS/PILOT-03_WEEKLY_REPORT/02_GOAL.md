# PILOT-03: Goal and Plan

## SMART Goal

> Within **3 days**, add a `WeeklyReport` model, nightly aggregation, and signed PDF.

## Acceptance Standards

### Standard 1: Model

```python
class WeeklyReport(models.Model):
    pilot_program = models.ForeignKey(PilotProgram, on_delete=models.CASCADE, related_name="weekly_reports")
    week_start = models.DateField()
    week_end = models.DateField()
    summary = models.TextField()
    severity_counts = models.JSONField(default=dict)  # {"ok": 5, "minor": 1, ...}
    pdf_audit_id = models.UUIDField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("pilot_program", "week_start")]
        ordering = ["-week_start"]
```

### Standard 2: Aggregation

- Iterates `DailyLog` rows for `week_start` to `week_end`.
- Builds summary, severity counts.

### Standard 3: PDF

- Renders a clean PDF.
- Stores in evidence storage.
- Writes an audit row with file hash.

### Standard 4: Distribution

- Distribution list in `WeeklyReport.distribution` (CSV of emails).

---

## Implementation Plan

### Day 1 — Model

- [ ] Add `WeeklyReport` model.
- [ ] Add aggregation function.

### Day 2 — PDF

- [ ] Add PDF render.
- [ ] Add audit row.

### Day 3 — Distribution

- [ ] Add distribution list.
- [ ] Runbook.

---

## Cancellation Criteria

- A weekly report missing a `DailyLog` row is flagged in the summary.
