# PILOT-03: Weekly Report

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** A weekly report is needed to summarise daily logs and the pilot health. There is no `WeeklyReport` model, no aggregation logic, and no runbook entry.

**Evidence gathered:**

```bash
Select-String -Path backend -Pattern "WeeklyReport" -Recurse
# Expected: 0
```

### Impact

| Dimension | Impact |
|---|---|
| Operational | No week-over-week trend. |
| Decisions | Owner has no weekly summary for go/no-go. |
| Audit | No immutable weekly artefact. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `WeeklyReport` model | missing | yes |
| Aggregation logic | missing | yes |
| Export to PDF | missing | yes |
| Distribution list | missing | yes |

---

## 3. Goal Statement

> Within **3 days**, add a `WeeklyReport` model and an aggregation that consumes `DailyLog` rows, and produce a signed PDF.

### Acceptance Criteria

1. **AC-1:** `apps/pilot/models.py::WeeklyReport` exists.
2. **AC-2:** Aggregation runs nightly and produces a row per week.
3. **AC-3:** PDF is generated and stored as an audit row.
4. **AC-4:** Distribution list is configurable.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Aggregation misses a day | Medium | High | Use `created_at` range, idempotent |
| PDF contains secrets | Low | Critical | Sanitise fields before render |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `WeeklyReport` model | Backend | not-started |
| 2 | Build aggregation | Backend | not-started |
| 3 | Generate PDF | Backend | not-started |
| 4 | Distribution list | Pilot Manager | not-started |

---

## 6. References

- [upgrads/08_PILOT_OPERATIONS/PILOT-02_DAILY_LOG_WORKFLOW](..)
- [upgrads/08_PILOT_OPERATIONS/PILOT-06_OWNER_DECISION](..)
