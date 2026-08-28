# LEGAL-04: Test Strategy

> **Rule:** every DSR is recorded in the audit chain; SLA is enforced; DPO-only access.

## 1. Unit Tests

```bash
cd backend
pytest apps/compliance/tests/test_dsr.py -v
# Expected: ≥ 3 passed
```

## 2. Integration Tests

```bash
cd backend
pytest apps/compliance/tests/ -v
# Expected: green
```

## 3. End-to-End Tests

### 3.1 Web form submission

```bash
cd frontend
npx playwright test tests/e2e/09_dsr.spec.ts --reporter=line
# Expected: passed
```

### 3.2 SLA reminder

```bash
cd backend
python manage.py shell -c "from apps.compliance.tasks import dsr_sla_due; dsr_sla_due()"
# Verify: a DSR_SLA_DUE row is written for any due request
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| DSRRequest creation | passed |
| SLA = 30 days | passed |
| DPO-only list | passed |
| Audit row | passed |
| E2E form | passed |

## 5. Cross-links

- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-02_ROPA_REGISTER](..) — what data
- [upgrads/07_COMPLIANCE_LEGAL/LEGAL-05_BREACH_RESPONSE](..) — escalation
