# LEGAL-02: Test Strategy

> **Rule:** every processing activity is in the ROPA; the API exposes them; the quarterly reminder fires.

## 1. Unit Tests

```bash
cd backend
pytest apps/compliance/tests/test_ropa.py -v
# Expected: ≥ 3 passed
```

## 2. Integration Tests

```bash
cd backend
pytest apps/compliance/tests/ -v
# Expected: green
```

## 3. End-to-End Tests

### 3.1 Public ROPA endpoint

```bash
curl -fsS http://localhost:8000/api/v1/compliance/ropa/ | jq '.results | length'
# Expected: ≥ 10
```

### 3.2 Quarterly reminder

```bash
cd backend
python manage.py shell -c "from apps.compliance.tasks import quarterly_ropa_review; quarterly_ropa_review()"
# Verify: a ROPA_REVIEW_DUE row is written if any activity is due
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| ≥ 10 activities in ROPA | passed |
| API returns ≥ 10 | passed |
| Quarterly reminder | passed |
| Cross-border flag | recorded |

## 5. Cross-links

- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-01_PDPL_DOCUMENTS](..) — Privacy Notice references ROPA
- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-03_DPIA](..) — DPIA references ROPA
- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-04_DSR_API](..) — DSR
