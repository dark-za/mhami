# Section 10: Phase 13 Preparation (Production Readiness)

## List of Fixes

| # | Title | Priority | Duration |
|---|---|---|---|
| PHASE13-01 | Release Candidate Build | P0 | 1 week |
| PHASE13-02 | LAUNCH-GATE-03 | P0 | 1 week |
| PHASE13-03 | Support Rota | P0 | 3 days |
| PHASE13-04 | Rollback Plan | P0 | 3 days |

## PHASE13-01: Release Candidate (Detail)

### What must be done
- [ ] All C-*, H-*, FE-*, BE-*, INFRA-*, QA-* complete
- [ ] All LEGAL-* complete
- [ ] Pilot evidence complete
- [ ] Owner sign-off
- [ ] Production compose tested in staging
- [ ] All 280+ tests passing
- [ ] Coverage ≥ 85%
- [ ] ZAP scan without high
- [ ] Load test passes
- [ ] Security review approved

### Release Branch
```bash
git checkout -b release/1.0.0
git tag v1.0.0-rc1
docker build -t mhami/api:1.0.0-rc1 ./backend
docker build -t mhami/frontend:1.0.0-rc1 ./frontend
```

### Smoke Tests
```bash
# 5 minutes, tests 10 critical endpoints
tests/smoke/production_smoke.sh
```

## PHASE13-02: LAUNCH-GATE-03 (Detail)

### Inputs
- [ ] Pilot exit approved by a binding owner decision
- [ ] Release candidate built from immutable image digests
- [ ] Security review passed with no unaccepted Critical/High findings
- [ ] Legal and Privacy review passed
- [ ] Owner sign-off linked to the evidence packet

### Deliverables
- Launch go/no-go decision
- Rollout schedule
- Communication plan
- Success metrics
- Rollback triggers

### Process
1. Tech Lead reviews RC
2. Security reviews security review
3. Legal reviews compliance review
4. Pilot Manager reviews pilot results
5. **Platform Owner decides** (Launch / Defer / No-Go)
6. **If Launch** → rollout plan

## PHASE13-03: Support Rota (Detail)

### Structure
- 24/7 support team
- 3 levels: L1 (frontend), L2 (backend), L3 (architect)
- Weekly on-call rotation
- PagerDuty / Opsgenie

### Schedule
```
docs/support/
├── ROTA.md                    # weekly table
├── ESCALATION.md              # when and how
├── PLAYBOOKS/
│   ├── LOGIN_ISSUE.md
│   ├── TASK_ISSUE.md
│   ├── EVIDENCE_ISSUE.md
│   ├── REVIEW_ISSUE.md
│   └── BILLING_ISSUE.md
├── SHIFTS/
│   ├── L1_DAY_SHIFT.md
│   ├── L1_NIGHT_SHIFT.md
│   └── L2_L3.md
└── METRICS.md                 # support KPIs
```

### KPIs
- First response time (FRT)
- Mean time to resolution (MTTR)
- Customer satisfaction (CSAT)
- Ticket volume
- Escalation rate

## PHASE13-04: Rollback Plan (Detail)

### Triggers
- Error rate > 1% sustained 5 min
- p99 latency > 2s sustained 5 min
- Security incident detected
- Critical functionality broken
- Data integrity issue

### Process
1. **Detect** (alert)
2. **Confirm** (L2 on-call)
3. **Decide** (rollback or fix-forward)
4. **Execute** using the topology-specific tested runbook
5. **Verify** (smoke tests)
6. **Communicate** (status page + customers)
7. **Post-mortem**

### Rollback Tests
- Before Launch: Test rollback in staging
- After Launch: every month, drill

### Backward Compatibility
- Database migrations use an expand/contract plan; rollback does not assume
  every migration is reversible.
- API versioning (v1, v2)
- Feature flags for gradual rollout

Do not combine Kubernetes and Compose commands in one operational procedure.
Compose rollback uses an immutable image tag/digest and versioned Compose
configuration; it must never use `down -v`. Kubernetes rollback requires an
explicit namespace, deployment, and digest.
