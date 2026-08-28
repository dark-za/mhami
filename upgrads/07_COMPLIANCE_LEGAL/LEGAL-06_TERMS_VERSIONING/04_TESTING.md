# LEGAL-06: Test Strategy

> **Rule:** every user must have accepted the current `effective_date` version of every legal document; otherwise state-changing calls are blocked.

## 1. Unit Tests

```bash
cd backend
pytest apps/compliance/tests/test_versioning.py -v
# Expected: passed
```

## 2. Integration Tests

```bash
cd backend
pytest apps/compliance/tests/ -v
# Expected: green
```

## 3. End-to-End Tests

### 3.1 Frontend banner

After a new `LegalDocument` is published, the frontend shows a banner and redirects to `/legal`.

```bash
cd frontend
npx playwright test tests/e2e/10_legal_reaccept.spec.ts --reporter=line
# Expected: passed
```

### 3.2 Middleware blocks state-changing

```bash
cd backend
pytest apps/compliance/tests/test_legal_middleware_blocks.py -v
# Expected: passed
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| Re-acceptance on new version | passed |
| Middleware allows after acceptance | passed |
| Supersedes chain | queryable |
| Content hash stable | passed |

## 5. Cross-links

- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-01_PDPL_DOCUMENTS](..)
- [upgrads/04_BACKEND_HARDENING/BE-06_MFA_ENFORCEMENT](../04_BACKEND_HARDENING/BE-06_MFA_ENFORCEMENT/00_DISCOVERY.md) — middleware pattern
