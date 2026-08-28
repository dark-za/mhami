# LEGAL-01: PDPL Legal Documents

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** `docs/legal/README.md:3` is a placeholder: *"These files must be drafted and reviewed by qualified legal counsel before use."* The platform cannot launch without drafted and approved legal documents covering Terms of Use, Privacy Notice, Data Processing Terms, AI Data Transfer Notice, Employee Privacy Acknowledgement, Retention Policy, and Support Access Terms.

**Evidence gathered:**

```bash
Get-ChildItem docs\legal -Recurse -Filter "*.md"
# Expected today: README.md + 08_TEMPLATES only
```

### Impact

| Dimension | Impact |
|---|---|
| Compliance | PDPL / Gate-B require drafted, counsel-approved documents. |
| Operational | No acceptance flow → no audit of who accepted what. |
| Legal | Cannot launch without counsel sign-off. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Drafted documents | 0 of 7 | 7 of 7 (drafted) |
| Counsel-approved | 0 of 7 | 7 of 7 (approved) |
| Bilingual (en + ar) | 0 | 7 |
| Acceptance flow | missing | yes |
| Audit of acceptance | missing | yes |

---

## 3. Goal Statement

> Within **4 weeks** (parallel to legal counsel), draft all 7 PDPL documents in EN + AR, get counsel approval, and wire the acceptance flow + audit.

### Acceptance Criteria

1. **AC-1:** `docs/legal/01_TERMS_OF_USE/v1.0.md` (en + ar) exists, drafted and counsel-approved.
2. **AC-2:** Same for `02_PRIVACY_NOTICE`, `03_DATA_PROCESSING_TERMS`, `04_AI_TRANSFER_NOTICE`, `05_EMPLOYEE_PRIVACY`, `06_RETENTION_DELETION`, `07_SUPPORT_ACCESS`.
3. **AC-3:** `LegalAcceptance` is recorded in the audit chain on every acceptance.
4. **AC-4:** Re-acceptance is required when a document is updated.
5. **AC-5:** The CHANGELOG.md entry records the counsel sign-off.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Counsel delays | High | High | Parallelise drafts; track in `RISK_REGISTER.md` |
| Translation lag | Medium | High | Use bilingual template; counsel reviews both |
| Document drift | Medium | Medium | Single source of truth per document; `effective_date` enforcement |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Engage legal counsel | Platform Owner | not-started |
| 2 | Draft Terms of Use (en + ar) | Counsel | not-started |
| 3 | Draft Privacy Notice (en + ar) | Counsel | not-started |
| 4 | Draft Data Processing Terms (en + ar) | Counsel | not-started |
| 5 | Draft AI Data Transfer Notice (en + ar) | Counsel | not-started |
| 6 | Draft Employee Privacy Acknowledgement (en + ar) | Counsel | not-started |
| 7 | Draft Retention & Deletion Policy (en + ar) | Counsel | not-started |
| 8 | Draft Support Access Authorization Terms (en + ar) | Counsel | not-started |
| 9 | Counsel approval | Counsel | not-started |
| 10 | Wire `LegalAcceptance` flow | Backend | not-started |
| 11 | Re-acceptance on update | Backend | not-started |
| 12 | Update `docs/legal/README.md` | Tech Writer | not-started |
| 13 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [docs/legal/README.md](../../../docs/legal/README.md)
- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-02_ROPA_REGISTER](..) — feeds the Privacy Notice
- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-06_TERMS_VERSIONING](..) — re-acceptance logic
- [upgrads/08_PILOT_OPERATIONS/PILOT-01_PILOT_CHARTER](../08_PILOT_OPERATIONS/PILOT-01_PILOT_CHARTER/00_DISCOVERY.md) — acceptance required before pilot
