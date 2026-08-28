# LEGAL-04: Data Subject Rights API (DSR)

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** PDPL grants data subjects six rights: Access, Rectification, Erasure, Restriction, Portability, Object. The platform exposes no DSR API and no DPO-facing workflow.

**Evidence gathered:**

```bash
Test-Path backend\apps\compliance\api\views.py
# Expected: missing or empty

Select-String -Path backend\apps -Pattern "DSR|data.?subject.?right" -Recurse
# Expected: 0 matches
```

### Impact

| Dimension | Impact |
|---|---|
| Compliance | Gate-B (PDPL) requires a DSR workflow. |
| Legal | Data subjects can complain to SDAIA. |
| Operational | DPO has no tooling. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `DSRRequest` model | missing | yes |
| Web form for data subjects | missing | yes |
| Email verification | missing | yes |
| DPO dashboard | missing | yes |
| SLA: 30 days | missing | yes |
| Audit | missing | yes |

---

## 3. Goal Statement

> Within **1 week**, implement `DSRRequest` model, web form, email verification, DPO dashboard, and SLA tracking. All actions are audited.

### Acceptance Criteria

1. **AC-1:** `apps/compliance/models.py::DSRRequest` exists with type, status, subject_email, sla_due_at, etc.
2. **AC-2:** `POST /api/v1/compliance/dsr/` accepts a request; sends an email verification.
3. **AC-3:** `GET /api/v1/compliance/dsr/` (DPO only) lists requests.
4. **AC-4:** SLA is 30 days; a Celery reminder fires 7 days before due.
5. **AC-5:** Each action is recorded in the audit chain.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Identity verification bypass | Medium | High | Email + tenant confirmation + manual DPO approval |
| Erasure breaks referential integrity | Medium | High | Soft-delete + tombstone rows; reverse cascade is documented |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `DSRRequest` model | Backend | not-started |
| 2 | Add web form | Frontend | not-started |
| 3 | Add email verification | Backend | not-started |
| 4 | Add DPO dashboard | Frontend | not-started |
| 5 | Add SLA reminder | Backend | not-started |
| 6 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-02_ROPA_REGISTER](..) — what data
- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-05_BREACH_RESPONSE](..) — escalation
- [upgrads/08_PILOT_OPERATIONS/PILOT-01_PILOT_CHARTER](../08_PILOT_OPERATIONS/PILOT-01_PILOT_CHARTER/00_DISCOVERY.md)
