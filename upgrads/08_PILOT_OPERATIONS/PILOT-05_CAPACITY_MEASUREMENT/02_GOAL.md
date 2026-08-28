# PILOT-05: Goal and Plan

## SMART Goal

> Within **5 days**, measure the 3-branch / 30-employee pilot profile and publish a signed capacity report.

## Acceptance Standards

### Standard 1: Load profile

| Scenario | Target |
|---|---:|
| Concurrent users | 30 |
| Branches | 3 |
| Task reads / minute | 90 |
| Task writes / minute | 30 |
| Evidence uploads / hour | 30 |
| Duration | 60 minutes |

### Standard 2: Thresholds

- API p95 latency <= 500 ms.
- Error rate < 1%.
- CPU < 70% sustained.
- Memory < 75% sustained.
- Queue depth < 100.

### Standard 3: Evidence

- Synthetic data only.
- Run ID, commit SHA, environment, and timestamp are recorded.
- Raw metrics retained; report contains aggregate values.

---

## Implementation Plan

### Day 1 — Profile

- [ ] Define scenarios and thresholds.

### Days 2-3 — Instrumentation

- [ ] Add dashboard and labels.

### Days 4-5 — Run and report

- [ ] Execute isolated load test.
- [ ] Publish and sign report.

---

## Cancellation Criteria

- Abort if any request targets production or if error rate causes data corruption.
