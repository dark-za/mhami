# PILOT-03: Implementation Guide

## Step 1: Model

```python
class WeeklyReport(models.Model):
    pilot_program = models.ForeignKey(PilotProgram, on_delete=models.CASCADE, related_name="weekly_reports")
    week_start = models.DateField()
    week_end = models.DateField()
    summary = models.TextField()
    severity_counts = models.JSONField(default=dict)
    pdf_audit_id = models.UUIDField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("pilot_program", "week_start")]
        ordering = ["-week_start"]
```

## Step 2: Aggregation

```python
# backend/apps/pilot/reports/weekly.py
def build_weekly(pilot, week_start):
    week_end = week_start + timedelta(days=6)
    logs = pilot.daily_logs.filter(day__gte=week_start, day__lte=week_end)
    counts = {"ok": 0, "minor": 0, "major": 0, "blocker": 0}
    summary = []
    for log in logs:
        counts[log.severity] = counts.get(log.severity, 0) + 1
        summary.append(f"{log.day}: {log.observed_issues}")
    return WeeklyReport.objects.update_or_create(
        pilot_program=pilot, week_start=week_start,
        defaults={"week_end": week_end, "summary": "\n".join(summary), "severity_counts": counts},
    )
```

## Step 3: PDF render

```python
# backend/apps/pilot/reports/pdf.py
def render_weekly_pdf(report):
    pdf_bytes = render_to_pdf("pilot/weekly.html", {"report": report})
    audit = write_audit_event(event="PILOT_WEEKLY_PDF", context={"week_start": str(report.week_start), "size": len(pdf_bytes)})
    upload_to_evidence(audit.id, "weekly.pdf", pdf_bytes)
    report.pdf_audit_id = audit.id
    report.save()
```

## Step 4: Distribution

- `pilot.distribution_list` (CSV) → Celery task `deliver_weekly_report` sends email.

## Step 5: Tests

```python
def test_weekly_aggregation(make_user, make_company):
    user = make_user()
    co = make_company(owner=user, code="co")
    pilot = PilotProgram.objects.create(company=co, owner_user=user, period_start="2030-01-01", period_end="2030-12-31", environment="staging")
    DailyLog.objects.create(pilot_program=pilot, day="2030-01-02", author=user, observed_issues="x", severity="minor")
    DailyLog.objects.create(pilot_program=pilot, day="2030-01-03", author=user, observed_issues="y", severity="ok")
    rep, _ = build_weekly(pilot, date(2030, 1, 1))
    assert rep.severity_counts == {"ok": 1, "minor": 1, "major": 0, "blocker": 0}
```
