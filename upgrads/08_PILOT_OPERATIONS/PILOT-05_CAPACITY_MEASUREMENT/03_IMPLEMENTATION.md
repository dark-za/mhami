# PILOT-05: Implementation Guide

## Step 1: Metrics configuration

Create `infra/monitoring/pilot-capacity.yml`:

```yaml
pilot_capacity:
  labels:
    - pilot_id
    - scenario
  thresholds:
    api_p95_ms: 500
    error_rate_percent: 1
    cpu_percent: 70
    memory_percent: 75
    queue_depth: 100
```

## Step 2: Load profile

```yaml
# pilot-load.yml
base_url: http://pilot-staging
users: 30
branches: 3
duration: 60m
scenarios:
  - name: task_read
    rate_per_minute: 90
  - name: task_write
    rate_per_minute: 30
  - name: evidence_upload
    rate_per_hour: 30
```

## Step 3: Test execution

1. Provision an isolated staging-equivalent environment.
2. Generate synthetic companies, branches, users, tasks, and evidence.
3. Run the load profile with an allowlisted base URL.
4. Capture application and infrastructure metrics.
5. Destroy generated data after retention approval.

## Step 4: Report

Create `docs/pilot-evidence/05_CAPACITY_REPORT.md`:

```markdown
# Pilot Capacity Report

| Run ID | Commit SHA | Environment | UTC |
|---|---|---|---|
| | | | |

| Metric | Threshold | Observed | Result |
|---|---:|---:|---|
| API p95 (ms) | 500 | | |
| Error rate (%) | 1 | | |
| CPU (%) | 70 | | |
| Memory (%) | 75 | | |
| Queue depth | 100 | | |
```

## Step 5: Tests

```bash
# Config parses and thresholds are present
python -c "import yaml; d=yaml.safe_load(open('infra/monitoring/pilot-capacity.yml')); assert 'thresholds' in d['pilot_capacity']"
```
