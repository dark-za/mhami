# LEGAL-06: Document Versioning

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** Legal documents need explicit versioning. The current `LegalAcceptance` model (in LEGAL-01) records `(user, document_type, version)`, but there is no `LegalDocument` model with `effective_date`, `supersedes_version`, and re-acceptance enforcement on update.

**Evidence gathered:**

```bash
Test-Path backend\apps\compliance\models.py
# Expected: missing LegalDocument

Select-String -Path backend\apps\compliance -Pattern "class LegalDocument" -Recurse
# Expected: 0
```

### Impact

| Dimension | Impact |
|---|---|
| Compliance | A user can be bound to a stale document. |
| Operational | No machine-readable version chain. |
| Legal | Cannot prove a user accepted the current copy. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `LegalDocument` model | missing | yes |
| `effective_date` enforcement | missing | yes |
| `supersedes_version` chain | missing | yes |
| Re-acceptance on update | missing | yes |

---

## 3. Goal Statement

> Within **1 week**, add `LegalDocument` model, enforce `effective_date`, chain `supersedes_version`, and require re-acceptance on update.

### Acceptance Criteria

1. **AC-1:** `LegalDocument(document_type, version, content_en, content_ar, effective_date, supersedes_version, published_by)` exists.
2. **AC-2:** The middleware (or view) checks the user's most recent `LegalAcceptance` matches the current `effective_date`.
3. **AC-3:** A re-acceptance is required when a new `LegalDocument` is published.
4. **AC-4:** The `LegalDocument` chain is queryable: `supersedes_version` links versions.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A user re-acceptance is missed | Low | Medium | Frontend surfaces a banner; middleware blocks state-changing calls |
| Document drift | Low | Medium | Single source of truth; content hash in audit |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Add `LegalDocument` model | Backend | not-started |
| 2 | Add middleware check | Backend | not-started |
| 3 | Frontend banner | Frontend | not-started |
| 4 | Add tests | Backend | not-started |
| 5 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-01_PDPL_DOCUMENTS](..) — accepts the docs
- [upgrads/04_BACKEND_HARDENING/BE-06_MFA_ENFORCEMENT](../04_BACKEND_HARDENING/BE-06_MFA_ENFORCEMENT/00_DISCOVERY.md) — middleware pattern
