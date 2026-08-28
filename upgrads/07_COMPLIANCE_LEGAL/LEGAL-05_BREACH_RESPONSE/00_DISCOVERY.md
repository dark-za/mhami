# LEGAL-05: Data Breach Response Plan

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** PDPL requires a documented data breach response plan with severity levels, response timelines, and the response team. The repository has no `docs/BREACH_RESPONSE.md` and no incident model.

**Evidence gathered:**

```bash
Test-Path docs\BREACH_RESPONSE.md
# Expected: False

Select-String -Path backend\apps -Pattern "BreachIncident|breach" -Recurse
# Expected: 0 matches
```

### Impact

| Dimension | Impact |
|---|---|
| Compliance | Gate-B (PDPL) requires a breach plan. |
| Operational | On-call has no playbook. |
| Legal | SDAIA notification must happen within 72h. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `docs/BREACH_RESPONSE.md` | missing | yes |
| `BreachIncident` model | missing | yes |
| Severity matrix | missing | yes |
| Notification templates | missing | yes |
| Runbook | missing | yes |

---

## 3. Goal Statement

> Within **1 week**, write `docs/BREACH_RESPONSE.md`, implement `BreachIncident` model, add severity levels, notification templates, and link to runbooks (DOC-03).

### Acceptance Criteria

1. **AC-1:** `docs/BREACH_RESPONSE.md` exists with definition, severity, response, team.
2. **AC-2:** `apps/compliance/models.py::BreachIncident` exists.
3. **AC-3:** Severity levels: Critical (>1000 subjects), High (100-1000), Medium (<100).
4. **AC-4:** Notification templates for SDAIA + data subjects.
5. **AC-5:** Cross-link to runbook (DOC-03) and incident response (DOC-04).
6. **AC-6:** Tests cover: incident creation, escalation, audit row.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Notification lag | Medium | High | Automated template + Celery reminder |
| Under-reporting | Medium | High | Severity matrix is mandatory; the on-call cannot close without filling it |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Write `docs/BREACH_RESPONSE.md` | DPO + Counsel | not-started |
| 2 | Add `BreachIncident` model | Backend | not-started |
| 3 | Add notification templates | Backend | not-started |
| 4 | Cross-link to runbooks | Tech Writer | not-started |
| 5 | Add tests | Backend | not-started |
| 6 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-04_DSR_API](..) — DSR can trigger a breach
- [upgrads/09_DOCUMENTATION/DOC-03_RUNBOOK](../09_DOCUMENTATION/DOC-03_RUNBOOK/00_DISCOVERY.md) — `11_BREACH_DETECTED.md`
- [upgrads/09_DOCUMENTATION/DOC-04_INCIDENT_RESPONSE](../09_DOCUMENTATION/DOC-04_INCIDENT_RESPONSE/00_DISCOVERY.md) — post-mortem template
