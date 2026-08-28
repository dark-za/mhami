# PILOT-05: Capacity Measurement

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The pilot needs measured capacity and reliability evidence under its target load. Existing infrastructure metrics are not tied to pilot scenarios, thresholds, or a repeatable load protocol.

**Evidence gathered:**

```bash
Get-ChildItem infra\monitoring -Recurse
# Expected: generic dashboards, no pilot baseline
```

### Impact

| Dimension | Impact |
|---|---|
| Reliability | Capacity limits remain unknown. |
| Cost | Scaling decisions lack evidence. |
| Pilot exit | No objective performance gate. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| Baseline metrics | generic | pilot-specific |
| Load profile | missing | documented |
| Thresholds | missing | approved SLOs |
| Capacity report | missing | signed evidence |

---

## 3. Goal Statement

> Within **5 days**, measure the pilot target profile of 3 branches and 30 employees, record latency/error/resource baselines, and publish a capacity report.

### Acceptance Criteria

1. **AC-1:** Load profile and test data are documented.
2. **AC-2:** p50/p95 latency, error rate, CPU, memory, and queue depth are captured.
3. **AC-3:** Thresholds and observed values are compared.
4. **AC-4:** No production customer data is used.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Load test reaches production | Low | Critical | Isolated environment and explicit endpoint allowlist |
| Synthetic data resembles PII | Low | High | Generated IDs and data review |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Define load profile | SRE | not-started |
| 2 | Instrument pilot metrics | Backend | not-started |
| 3 | Run measurements | SRE | not-started |
| 4 | Publish report | SRE | not-started |
