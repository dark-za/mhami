# PILOT-02: Implementation Guide

## Step 1: Model

### 1.1 `backend/apps/pilot/models.py`

```python
class DailyLog(models.Model):
    pilot_program = models.ForeignKey(PilotProgram, on_delete=models.CASCADE, related_name="daily_logs")
    day = models.DateField()
    author = models.ForeignKey("identity.User", on_delete=models.PROTECT)
    observed_issues = models.TextField()
    actions_taken = models.TextField(blank=True)
    severity = models.CharField(max_length=16)
    attachments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    override_reason = models.TextField(blank=True)

    class Meta:
        unique_together = [("pilot_program", "day")]
        ordering = ["-day"]

    def lock(self, user, reason=""):
        if self.locked_at is not None:
            return
        self.locked_at = timezone.now()
        if reason:
            self.override_reason = reason
        self.save()
```

## Step 2: API

### 2.1 `backend/apps/pilot/api/serializers.py`

```python
class DailyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyLog
        fields = ["id", "pilot_program", "day", "author", "observed_issues", "actions_taken", "severity", "attachments", "created_at", "locked_at"]
```

### 2.2 `backend/apps/pilot/api/views.py`

```python
class DailyLogViewSet(viewsets.ModelViewSet):
    serializer_class = DailyLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DailyLog.objects.filter(pilot_program__company__memberships__user=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.locked_at and not self.request.user.is_staff:
            raise PermissionDenied("Locked")
        serializer.save()
```

## Step 3: Frontend

### 3.1 `frontend/src/pages/Pilot/DailyLog.tsx`

- List grouped by `day`.
- "New Entry" button → form with required fields.

## Step 4: Runbook

### 4.1 `docs/runbooks/pilot_daily_log.md`

```markdown
# Pilot Daily Log Runbook

## When to write
Every weekday by 18:00 local time.

## How to write
1. Open the daily log page.
2. Pick the day (default: today).
3. Fill observed issues, actions, severity.
4. Save.

## Editing
After 24h, edits require a Platform Owner override with a reason.
```

## Step 5: Weekly aggregation

- `WeeklyReport.aggregate()` queries `DailyLog` for the week and summarises severity counts.

## Step 6: Tests

```python
def test_daily_log_lock(make_user, make_company):
    user = make_user()
    co = make_company(owner=user, code="co")
    pilot = PilotProgram.objects.create(company=co, owner_user=user, period_start="2030-01-01", period_end="2030-12-31", environment="staging")
    log = DailyLog.objects.create(pilot_program=pilot, day="2030-01-02", author=user, observed_issues="x", severity="ok")
    log.lock()
    with pytest.raises(PermissionDenied):
        log.observed_issues = "y"
        log.save()
```
