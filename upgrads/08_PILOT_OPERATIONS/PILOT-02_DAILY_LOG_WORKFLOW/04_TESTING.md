# PILOT-02: Test Strategy

> **Rule:** A daily log without a Charter is rejected. A daily log older than 24h cannot be edited without Platform Owner override.

## 1. Unit Tests

```bash
cd backend
pytest apps/pilot/tests/test_daily_log.py -v
# Expected: ≥ 4 passed
```

## 2. Integration Tests

```bash
cd backend
pytest apps/pilot/tests/ -v
# Expected: green
```

## 3. End-to-End Tests

```bash
cd frontend
npx playwright test tests/e2e/12_pilot_daily_log.spec.ts --reporter=line
# Expected: passed
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| Model exists | passed |
| Lock works | passed |
| Override requires Platform Owner | passed |
| E2E | passed |

## 5. Cross-links

- [upgrads/08_PILOT_OPERATIONS/PILOT-01_PILOT_CHARTER](..)
- [upgrads/08_PILOT_OPERATIONS/PILOT-03_WEEKLY_REPORT](..)
