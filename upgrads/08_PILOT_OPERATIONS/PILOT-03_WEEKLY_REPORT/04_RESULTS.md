# PILOT-03: Results Log

## 1. Completion Summary

| Item | Value |
|---|---|
| Start Date | YYYY-MM-DD |
| End Date | YYYY-MM-DD |
| Model | `WeeklyReport` |
| Aggregation | nightly |
| PDF | yes |
| Tests | ≥ 3 passed |

## 2. Verification

| Command | Result | Exit Code |
|---|---|---|
| `pytest apps/pilot/tests/test_weekly.py` | passed | 0 |

## 3. Git Changes

```
<commit-sha-1> PILOT-03: weekly report
  - Add WeeklyReport model
  - Add aggregation + PDF
  - Add distribution
  - Add tests
```

## 4. Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| Pilot Manager | _________ | _________ | Approved |
| Backend Lead | _________ | _________ | Approved |
