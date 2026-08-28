# LEGAL-01: Goal and Plan

## SMART Goal

> Within **4 weeks**, draft all 7 PDPL documents in EN + AR, get
> counsel approval, and wire the acceptance flow + audit.

## Acceptance Standards

### Standard 1: Document set

| # | Document | EN | AR |
|---|---|---|---|
| 1 | Terms of Use | `01_TERMS_OF_USE/v1.0.md` | `01_TERMS_OF_USE/v1.0.ar.md` |
| 2 | Privacy Notice | `02_PRIVACY_NOTICE/v1.0.md` | `02_PRIVACY_NOTICE/v1.0.ar.md` |
| 3 | Data Processing Terms | `03_DATA_PROCESSING_TERMS/v1.0.md` | `03_DATA_PROCESSING_TERMS/v1.0.ar.md` |
| 4 | AI Data Transfer Notice | `04_AI_TRANSFER_NOTICE/v1.0.md` | `04_AI_TRANSFER_NOTICE/v1.0.ar.md` |
| 5 | Employee Privacy Acknowledgement | `05_EMPLOYEE_PRIVACY/v1.0.md` | `05_EMPLOYEE_PRIVACY/v1.0.ar.md` |
| 6 | Retention & Deletion Policy | `06_RETENTION_DELETION/v1.0.md` | `06_RETENTION_DELETION/v1.0.ar.md` |
| 7 | Support Access Authorization Terms | `07_SUPPORT_ACCESS/v1.0.md` | `07_SUPPORT_ACCESS/v1.0.ar.md` |

Each `v1.0.md` ends with:

```markdown
## Counsel Approval

- **Counsel:** <name>, <bar number>
- **Date:** YYYY-MM-DD
- **Signature:** <hash or reference>
```

### Standard 2: Acceptance flow

`POST /api/v1/compliance/legal-accept/` records the acceptance in the audit chain:

```json
{
  "document_type": "TERMS_OF_USE",
  "version": "1.0",
  "language": "en"
}
```

The view returns 201 + an audit row with `event="LEGAL_ACCEPTANCE"`.

### Standard 3: Re-acceptance

When a document is updated, the user must re-accept. The acceptance is per `(user, company, document_type, version)`.

### Standard 4: Cross-link to ROPA

`docs/legal/02_PRIVACY_NOTICE/v1.0.md` references the ROPA (LEGAL-02).

### Standard 5: CHANGELOG

`CHANGELOG.md` records the counsel sign-off date.

---

## Implementation Plan

### Week 1-3 — Drafting (counsel)

- [ ] Engage counsel.
- [ ] Draft all 7 documents in EN.
- [ ] Translate to AR.

### Week 4 — Approval + wiring

- [ ] Counsel approval (signature).
- [ ] Implement `LegalAcceptance` view + audit.
- [ ] Implement re-acceptance logic.
- [ ] Update `docs/legal/README.md`.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | 7 documents drafted |
| CP-2 | 7 documents approved |
| CP-3 | Acceptance flow live |
| CP-4 | Re-acceptance works |
| CP-5 | CHANGELOG updated |

---

## Cancellation Criteria

- If counsel delays → ship the drafts as `DRAFT` versions; do not publish as `v1.0` without approval.
- If translation blocks AR → keep the EN version, mark AR as "pending translation" in the README.
