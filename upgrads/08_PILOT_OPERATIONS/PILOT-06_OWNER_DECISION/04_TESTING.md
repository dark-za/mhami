# PILOT-06: Test Strategy

> **Rule:** No pilot decision is valid without complete evidence, a Platform Owner actor, and an immutable UTC audit record.

## 1. Template Test

```bash
Test-Path docs\pilot-evidence\06_OWNER_DECISION.md
# Expected: True
```

## 2. Authorization Tests

```bash
cd backend
pytest apps/pilot/tests/test_owner_decision.py -v
# Expected: non-owner rejected, invalid option rejected, missing manifest rejected
```

## 3. State Tests

```bash
cd backend
pytest apps/pilot/tests/test_pilot_lifecycle.py -v
# Expected: stop closes pilot; continue/remediate preserve controls
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| All gates represented | passed |
| Evidence manifest required | passed |
| Owner-only signature | passed |
| Stop closure workflow | passed |
| Audit timestamp and hash | passed |
