# PILOT-02: Goal and Plan

## SMART Goal

> Within **3 days**, add a `DailyLog` model, web UI, runbook entry, and weekly aggregation.

## Acceptance Standards

### Standard 1: Model

```python
class DailyLog(models.Model):
    pilot_program = models.ForeignKey(PilotProgram, on_delete=models.CASCADE, related_name="daily_logs")
    day = models.DateField()
    author = models.ForeignKey("identity.User", on_delete=models.PROTECT)
    observed_issues = models.TextField()
    actions_taken = models.TextField(blank=True)
    severity = models.CharField(max_length=16)  # ok, minor, major, blocker
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    override_reason = models.TextField(blank=True)

    class Meta:
        unique_together = [("pilot_program", "day")]
        ordering = ["-day"]
```

### Standard 2: Immutability

- A `DailyLog` is **locked 24h** after `created_at`; edits require a `Platform Owner` override.

### Standard 3: Web UI

- **List:** current week, grouped by day.
- **Create:** form with required fields.

### Standard 4: Runbook

`docs/runbooks/pilot_daily_log.md` describes the workflow with screenshots.

---

## Implementation Plan

### Day 1 — Model

- [ ] Add `DailyLog` model.
- [ ] Add immutability check.

### Day 2 — UI

- [ ] Build list and create form.
- [ ] Wire to API.

### Day 3 — Runbook & aggregation

- [ ] Add runbook.
- [ ] Wire to weekly report.

---

## Cancellation Criteria

- A daily log without a signed Charter cannot be written.
