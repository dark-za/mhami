# PILOT-03: Test Strategy

> **Rule:** A weekly report is generated nightly, is signed, and contains no secrets.

## 1. Unit Tests

```bash
cd backend
pytest apps/pilot/tests/test_weekly.py -v
# Expected: ≥ 3 passed
```

## 2. Integration Tests

```bash
cd backend
pytest apps/pilot/tests/ -v
# Expected: green
```

## 3. PDF Sanity Test

```bash
cd backend
pytest apps/pilot/tests/test_weekly_pdf.py -v
# Expected: passed (file size > 0, no PII leaks)
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| Aggregation | passed |
| PDF rendered | passed |
| Distribution list | passed |
| No secrets in PDF | passed |

## 5. Cross-links

- [upgrads/08_PILOT_OPERATIONS/PILOT-02_DAILY_LOG_WORKFLOW](..)
- [upgrads/08_PILOT_OPERATIONS/PILOT-06_OWNER_DECISION](..)
