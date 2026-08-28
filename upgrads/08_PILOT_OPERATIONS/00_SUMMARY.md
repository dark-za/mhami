# Section 8: Pilot Operations

## List of Fixes

| # | Title | Priority | Duration |
|---|---|---|---|
| PILOT-01 | Draft authentic Charter | P0 | 3 days |
| PILOT-02 | Daily Log workflow | P0 | 1 week |
| PILOT-03 | Weekly Reports | P0 | 2 weeks (ongoing) |
| PILOT-04 | Usability Tests | P0 | 1 week |
| PILOT-05 | Capacity Measurement | P0 | 1 week |
| PILOT-06 | Owner Decision | P0 | 1 day |

## PILOT-01: Charter (Detail)

### Real content
- Company ID and Pilot Program ID (linked to PilotProgram DB record)
- Owner account ID (linked to User.id)
- Observation period (start/end UTC)
- Test environment (staging-equivalent)
- 3 branches target
- 30 employees target
- AI provider / Shadow Mode only
- Owner authorization (signed)

### Authorization Attestation
- Owner account ID
- Owner role
- Decision: authorize / decline / withdraw
- Date/time UTC
- Signature or approved electronic-record reference
- Conditions or exclusions

### Process
1. Pilot Manager writes the draft
2. Legal approves the scope
3. Security approves the test environment
4. Platform Owner signs
5. Charter enters the implementation space

## PILOT-02: Daily Log Workflow (Detail)

### Tools
- Web form: `/pilot/daily-log`
- CLI: `python manage.py pilot_log --date=2026-01-15`
- API: `POST /api/v1/pilot/daily-logs/`

### Schema
```python
class PilotDailyLog(models.Model):
    pilot_program = models.ForeignKey(PilotProgram)
    log_date = models.DateField()
    duty_owner = models.ForeignKey(User)
    monitors = models.ManyToManyField(User, related_name="monitored_logs")
    start_of_day_checks = models.JSONField()  # P12-DAY-GATE-01..04
    events = models.JSONField()  # P12-EVT-*
    counts = models.JSONField()  # metrics
    end_of_day_review = models.JSONField()
    stop_markers = models.JSONField()
    reviewed_by = models.ForeignKey(User, null=True)
    reviewed_at = models.DateTimeField(null=True)
```

### Daily Workflow
1. **08:00** - Pilot Manager opens the daily log
2. **08:15** - Start-of-day gates (legal, devices, AI, STOPs)
3. **Every hour** - Record events
4. **17:00** - End-of-day review
5. **18:00** - Owner review

## PILOT-03: Weekly Reports (Detail)

### 16 Metrics (from docs/pilot-evidence/05)
- Active participants
- Task volume
- Evidence image volume
- Storage growth
- Camera failures
- Upload reliability
- Face-blur behavior
- Review workload
- Duplicate-risk signals
- AI run coverage
- AI agreement rate
- AI error analysis
- Auto-pass control (must be 0)
- Connector reliability
- Usability feedback
- Issue/change flow

### Sources
- DB queries
- Logs
- Celery monitoring
- Manual observations
- User feedback forms

### Sample Report
```python
# apps/pilot/services.py
def generate_weekly_report(pilot_program, week_start, week_end):
    return {
        "p12-met-01": count_active_participants(pilot_program, week_start, week_end),
        "p12-met-02": task_volume_metrics(pilot_program, week_start, week_end),
        "p12-met-03": evidence_volume_metrics(pilot_program, week_start, week_end),
        # ... 13 more
    }
```

## PILOT-04: Usability Tests (Detail)

### Methods
1. **Task completion observation** - 5 tasks, 3 employees, record
2. **SUS (System Usability Scale)** - 10-question survey
3. **NPS (Net Promoter Score)** - "Would you recommend the platform?"
4. **Heuristic evaluation** - usability expert
5. **A/B tests** - variants

### SUS Template
```
1. I think that I would like to use this system frequently.
   1  2  3  4  5  (1=Strongly disagree, 5=Strongly agree)

2. I found the system unnecessarily complex.
   ...

(10 questions)
```

### Scoring
- SUS > 68 = acceptable
- SUS > 80 = excellent
- NPS > 0 = good
- NPS > 50 = excellent

## PILOT-05: Capacity Measurement (Detail)

### Metrics
- **Storage/day:** bytes per branch per day
- **Image size:** avg KB per image (with/without blur)
- **Task throughput:** tasks/hour at peak
- **API response time:** p95, p99
- **DB connection saturation:** max active
- **Redis memory:** peak usage
- **Celery queue depth:** max waiting
- **Backup size:** full + incremental

### Tools
- Prometheus
- Grafana
- Celery Flower
- pg_stat_statements
- AWS CloudWatch (if applicable)

### Report
- Daily snapshot
- Weekly aggregation
- Trend lines
- Capacity recommendations (e.g., "upgrade to 2x CPU in Q2")

## PILOT-06: Owner Decision (Detail)

### Process
1. Pilot Manager collects all artifacts
2. Legal signs on compliance
3. Security signs on security review
4. **Platform Owner signs** on:
   - Pilot Charter (previously)
   - Final Decision (at the end)
5. **Decision types:**
   - APPROVED → Phase 13
   - CONDITIONAL → Phase 13 with conditions
   - REJECTED → return to pilot
   - DEFERRED → postpone

### Workflow Implementation
Covered in C-06 (Owner Signature workflow).

### Audit
Every decision is recorded in `AuditEvent`:
- `EXIT_DECISION_SIGNED`
- `EXIT_DECISION_REVOKED` (if any)
- linked to PilotProgram ID
- carries rationale + metadata
