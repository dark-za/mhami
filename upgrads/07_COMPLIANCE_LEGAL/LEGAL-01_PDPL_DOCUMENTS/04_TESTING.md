# LEGAL-01: Test Strategy

> **Rule:** every acceptance is recorded in the audit chain; re-acceptance on new version is required.

## 1. Unit Tests

```bash
cd backend
pytest apps/compliance/tests/test_legal_acceptance.py -v
# Expected: 3 passed
```

## 2. Integration Tests

```bash
cd backend
pytest apps/compliance/tests/ -v
# Expected: green
```

## 3. End-to-End Tests

### 3.1 User must accept before pilot

```bash
cd backend
pytest apps/compliance/tests/test_legal_gate.py -v
# Expected: passed
```

### 3.2 Document versioning

```bash
cd backend
pytest apps/compliance/tests/test_legal_versioning.py -v
# Expected: passed
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| Acceptance creates audit row | passed |
| Acceptance is unique per version | passed |
| Re-acceptance on new version | passed |
| Gate (no pilot without acceptance) | passed |
| Versioning | passed |

## 5. Cross-links

- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-02_ROPA_REGISTER](..) — ROPA referenced by Privacy Notice
- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-06_TERMS_VERSIONING](..) — versioning logic
- [upgrads/08_PILOT_OPERATIONS/PILOT-01_PILOT_CHARTER](../08_PILOT_OPERATIONS/PILOT-01_PILOT_CHARTER/00_DISCOVERY.md) — gate
