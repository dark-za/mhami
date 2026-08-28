# PILOT-01: Test Strategy

> **Rule:** a pilot cannot enter "active" without a signed Charter; the signature is auditable.

## 1. Unit Tests

```bash
cd backend
pytest apps/pilot/tests/test_charter.py -v
# Expected: ≥ 3 passed
```

## 2. Integration Tests

```bash
cd backend
pytest apps/pilot/tests/ -v
# Expected: green
```

## 3. End-to-End Tests

### 3.1 Web flow

```bash
cd frontend
npx playwright test tests/e2e/11_pilot_charter.spec.ts --reporter=line
# Expected: passed
```

### 3.2 Signature audit

```bash
cd backend
pytest apps/pilot/tests/test_charter_signature.py -v
# Expected: passed
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| Charter model | passed |
| Signature creates audit row | passed |
| Active state requires signed | passed |
| E2E flow | passed |

## 5. Cross-links

- [upgrads/01_CRITICAL_FIXES/C-06_OWNER_SIGNATURE](../../01_CRITICAL_FIXES/C-06_OWNER_SIGNATURE/00_DISCOVERY.md)
- [upgrads/08_PILOT_OPERATIONS/PILOT-06_OWNER_DECISION](..) — exit decision
