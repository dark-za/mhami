# LEGAL-03: Data Protection Impact Assessment (DPIA)

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** PDPL requires a Data Protection Impact Assessment (DPIA) for high-risk processing activities. The platform has face-blur, AI analysis, and cross-border transfer as high-risk candidates. There is no DPIA document and no model.

**Evidence gathered:**

```bash
Test-Path docs\DPIA.md
# Expected: False

Select-String -Path backend\apps -Pattern "DPIA" -Recurse
# Expected: 0 matches
```

### Impact

| Dimension | Impact |
|---|---|
| Compliance | Gate-B (PDPL) requires a DPIA for high-risk activities. |
| Risk | Without a DPIA, the platform cannot demonstrate it has assessed the risk. |
| Legal | SDAIA can require a DPIA before processing. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `docs/DPIA.md` | missing | yes |
| DPIA model | missing | yes |
| Risk register | inline | structured |
| Mitigation tracking | missing | yes |
| Annual review | missing | yes |

---

## 3. Goal Statement

> Within **2 weeks**, write `docs/DPIA.md` covering the 4 high-risk activities (face image, AI analysis, cloud transfer, backups), implement a structured risk register, and add an annual review.

### Acceptance Criteria

1. **AC-1:** `docs/DPIA.md` exists with description, necessity, risk, mitigation, consultation for each of the 4 activities.
2. **AC-2:** `apps/compliance/models.py::DPIARisk` exists.
3. **AC-3:** Each risk has: activity, likelihood, impact, residual_likelihood, residual_impact, mitigation, owner, review_date.
4. **AC-4:** The DPIA is reviewed annually (Celery reminder).
5. **AC-5:** DPO sign-off is recorded in the audit chain.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A risk is under-rated | Medium | High | Cross-review by Tech Lead + DPO + Counsel |
| Mitigation not actually implemented | Medium | High | Each mitigation is linked to an upgrade (e.g. C-13, INFRA-05) |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Write `docs/DPIA.md` | DPO + Counsel | not-started |
| 2 | Add `DPIARisk` model | Backend | not-started |
| 3 | Add Celery annual reminder | Backend | not-started |
| 4 | Cross-link to existing upgrades | Backend | not-started |
| 5 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-02_ROPA_REGISTER](..) — ROPA
- [upgrads/01_CRITICAL_FIXES/C-13_FACE_PRIVACY_ENFORCEMENT](../../01_CRITICAL_FIXES/C-13_FACE_PRIVACY_ENFORCEMENT/00_DISCOVERY.md) — face privacy upgrade
- [upgrads/05_INFRASTRUCTURE/INFRA-03_BACKUP_S3_UPLOAD](../05_INFRASTRUCTURE/INFRA-03_BACKUP_S3_UPLOAD/00_DISCOVERY.md) — backup encryption
