# PILOT-02: Daily Log Workflow

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The pilot operations team needs a daily log that captures who observed what, when, and what action (if any) followed. There is no model, no UI, and no runbook entry for daily logs in the repository.

**Evidence gathered:**

```bash
Select-String -Path backend -Pattern "DailyLog|PilotLog" -Recurse
# Expected: 0
```

### Impact

| Dimension | Impact |
|---|---|
| Operational | No daily log means no week-over-week trend. |
| Legal | No signed daily log for incident escalation. |
| Pilot decisions | Decisions are made without observation data. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `DailyLog` model | missing | yes |
| Daily log UI | missing | yes |
| Runbook entry | missing | yes |
| Weekly report aggregation | missing | yes |

---

## 3. Goal Statement

> Within **3 days**, add a `DailyLog` model with required fields, a web UI to write/read daily logs, and a runbook entry so the Pilot Manager can record daily observations.

### Acceptance Criteria

1. **AC-1:** `apps/pilot/models.py::DailyLog` exists.
2. **AC-2:** Fields: pilot_program, day, author, observed_issues, actions_taken, severity, attachments.
3. **AC-3:** Web UI: list view + create form.
4. **AC-4:** Logs feed the weekly report (PILOT-03).

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Log is edited after 24h | Medium | High | Immutable after 24h, with override by Platform Owner |
| Log is not linked to a Charter | High | Critical | ForeignKey + non-nullable |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `DailyLog` model | Backend | not-started |
| 2 | Build web UI | Frontend | not-started |
| 3 | Add runbook entry | Pilot Manager | not-started |
| 4 | Wire weekly aggregation | Backend | not-started |

---

## 6. References

- [upgrads/08_PILOT_OPERATIONS/PILOT-01_PILOT_CHARTER](..)
- [upgrads/08_PILOT_OPERATIONS/PILOT-03_WEEKLY_REPORT](..)
