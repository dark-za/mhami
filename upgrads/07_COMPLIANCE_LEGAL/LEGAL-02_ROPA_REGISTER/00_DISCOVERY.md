# LEGAL-02: Record of Processing Activities (ROPA)

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** PDPL requires a written Record of Processing Activities (ROPA) per controller. The current repository has no ROPA file, no `ProcessingActivity` model, and no API to expose the ROPA to data subjects.

**Evidence gathered:**

```bash
Test-Path docs\ROPA.md
# Expected today: False

Select-String -Path backend\apps -Pattern "ProcessingActivity" -Recurse
# Expected today: 0 matches
```

### Impact

| Dimension | Impact |
|---|---|
| Compliance | Gate-B (PDPL) requires a ROPA. |
| Transparency | Data subjects have the right to know what is processed. |
| Operational | The DPO cannot answer regulator queries without a ROPA. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `docs/ROPA.md` | missing | yes |
| `ProcessingActivity` model | missing | yes |
| API exposure | missing | yes |
| Quarterly review | missing | yes |

---

## 3. Goal Statement

> Within **1 week**, write `docs/ROPA.md` covering every processing activity, add the `ProcessingActivity` model, expose a read-only API, and add a quarterly review reminder.

### Acceptance Criteria

1. **AC-1:** `docs/ROPA.md` exists with ≥10 processing activities.
2. **AC-2:** `apps/compliance/models.py::ProcessingActivity` exists.
3. **AC-3:** `GET /api/v1/compliance/ropa/` returns the ROPA (read-only, public).
4. **AC-4:** A quarterly Celery beat task reminds the DPO to review.
5. **AC-5:** Each activity has: name, purpose, legal basis, data categories, recipients, retention, cross-border, last reviewed.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| ROPA drifts from the actual processing | Medium | High | A test loads the ROPA and asserts every endpoint has a matching activity |
| Cross-border transfers not declared | Low | High | The model has a `cross_border` boolean; alert if True |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Write `docs/ROPA.md` | DPO | not-started |
| 2 | Add `ProcessingActivity` model | Backend | not-started |
| 3 | Add `GET /api/v1/compliance/ropa/` | Backend | not-started |
| 4 | Add Celery beat reminder | Backend | not-started |
| 5 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-01_PDPL_DOCUMENTS](..) — referenced by Privacy Notice
- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-03_DPIA](..) — feeds the DPIA
- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-04_DSR_API](..) — DSR is the data-subject-facing API
