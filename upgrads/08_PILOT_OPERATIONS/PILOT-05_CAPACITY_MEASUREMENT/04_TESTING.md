# PILOT-05: Test Strategy

> **Rule:** Capacity measurements are isolated, synthetic, repeatable, and compared to explicit thresholds.

## 1. Configuration Test

```bash
python -c "import yaml; d=yaml.safe_load(open('infra/monitoring/pilot-capacity.yml')); assert d['pilot_capacity']['thresholds']['api_p95_ms'] == 500"
# Expected: exit 0
```

## 2. Load Test

```bash
k6 run --env BASE_URL=http://pilot-staging scripts/pilot-load.js
# Expected: thresholds pass
```

## 3. Report Review

```bash
Select-String -Path docs\pilot-evidence\05_CAPACITY_REPORT.md -Pattern "Run ID|p95|Error rate|CPU|Memory"
# Expected: 5+ matches
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| Synthetic dataset | passed |
| Load profile | passed |
| Threshold comparison | passed |
| No production traffic | passed |
