# Comprehensive Development Plan for MHAMI Project
## Mhami Platform Evolution Plan (MPEP)

> **Issue:** 1.0.0
> **Release Date:** 2026-08-28
> **Approach:** Evidence-Driven Development
> **Scope:** Backend + Frontend + Infrastructure + Documentation + Compliance

---

## 1. Strategic Goal

Convert the MHAMI project from a platform with "components present" to a platform with **"components proven valid"**,
such that:

- Every feature is documented with dynamic tests, not merely the existence of code
- Every Critical/High defect is closed before moving to the next module
- Every frontend view is bound to an OpenAPI-generated API contract
- Every legal document is drafted by an authorized lawyer and registered in the system
- Every Pilot decision is backed by dated operational evidence

---

## 2. Folder Structure

```
upgrads/
├── 00_PLAN_INDEX.md                    # This file
├── 01_CRITICAL_FIXES/                  # Critical fixes (launch blockers and severe vulnerabilities)
│   ├── C-01_BROWSER_ROUTER_NESTING/    # Fix nested Router
│   ├── C-02_PRODUCTION_SECRETS/        # Fix Compose secrets
│   ├── C-03_IDOR_WEEKLYSHIFT/          # Fix IDOR in WeeklyShift
│   ├── C-04_CSRF_TOKEN/                # Fix CSRF in the frontend
│   ├── C-05_PILOT_EVIDENCE/            # Create real Pilot Evidence
│   ├── C-06_OWNER_SIGNATURE/           # Create platform owner signature workflow
│   ├── C-07_EVIDENCE_BRANCH_IDOR/      # Enforce branch scope for evidence and discussions
│   ├── C-08_MEMBERSHIP_EXPIRY/          # Enforce active_until and revoke stale access
│   ├── C-09_BACKUP_API_CONTRACTS/       # Repair backup API/service contracts and authorization
│   ├── C-10_EXPORT_API_CONTRACTS/       # Repair export API/frontend contracts and minimization
│   ├── C-11_SCHEDULER_INTEGRITY/        # Schedule generation, overdue, cleanup, and failover
│   ├── C-12_TASK_TRANSFER_INVARIANTS/   # Lock and validate transfer state transitions
│   ├── C-13_FACE_PRIVACY_ENFORCEMENT/   # Replace client-controlled face flag
│   └── C-14_AUTH_BOOTSTRAP_TRUST/       # Remove demo authorization and gate the workspace
│
├── 02_HIGH_PRIORITY/                   # High-priority fixes
│   ├── H-01_REVIEW_DECISION_RBAC/      # Add required_roles
│   ├── H-02_REVIEW_POLICY_RBAC/        # Add required_roles
│   ├── H-03_REAL_AI_PROVIDER/          # Implement real OpenAI Provider
│   ├── H-04_LINUX_CONNECTOR/           # Implement Linux Docker connector
│   ├── H-05_BACKUP_ENCRYPTION/         # Implement Fernet encryption for backups
│   ├── H-06_BACKUP_POSTGRES_RESTORE/   # Implement restore to PostgreSQL
│   ├── H-07_TEST_FAILURES/             # Fix 5 pytest failures
│   └── H-08_AUDIT_RACE_CONDITION/      # Fix race in Audit chain
│
├── 03_FRONTEND_REBUILD/                # Frontend rebuild
│   ├── FE-01_ROUTER_ARCHITECTURE/      # Clean Router architecture
│   ├── FE-02_BILINGUAL_SYSTEM/         # i18n system + RTL/LTR
│   ├── FE-03_API_INTEGRATION/          # OpenAPI Types integration
│   ├── FE-04_WORKFLOW_SCREENS/         # P0/P1 screens
│   ├── FE-05_CSRF_INTEGRATION/         # CSRF integration in client
│   └── FE-06_E2E_TESTS/                # Playwright E2E
│
├── 04_BACKEND_HARDENING/               # Backend hardening
│   ├── BE-01_RBAC_AUDIT/               # Audit required_roles
│   ├── BE-02_SERIALIZER_VALIDATION/    # Strengthen cross-tenant validation
│   ├── BE-03_TENANT_CONTEXT_TEST/      # Tenant isolation tests
│   ├── BE-04_AUDIT_INTEGRITY/          # Audit chain review
│   ├── BE-05_LOGIN_FAILED_AUDIT/       # Log failed login attempts
│   └── BE-06_MFA_ENFORCEMENT/          # Enforce MFA for Admin/Owner
│
├── 05_INFRASTRUCTURE/                  # Infrastructure
│   ├── INFRA-01_PRODUCTION_COMPOSE/    # Hardened compose.prod.yml
│   ├── INFRA-02_CSP_HEADERS/           # Content-Security-Policy
│   ├── INFRA-03_BACKUP_EXTERNAL/       # Upload backups to S3
│   ├── INFRA-04_MONITORING/            # Prometheus/Grafana
│   └── INFRA-05_TLS_CERTBOT/           # Let's Encrypt
│
├── 06_QUALITY_ASSURANCE/               # Quality assurance
│   ├── QA-01_TEST_STRATEGY/            # Implement all test layers
│   ├── QA-02_COVERAGE_THRESHOLD/       # Mandatory coverage threshold
│   ├── QA-03_BROWSER_E2E/              # E2E Playwright
│   ├── QA-04_PERFORMANCE_TESTS/        # Locust/k6 load tests
│   └── QA-05_SECURITY_SCANNING/        # ZAP/Burp scans
│
├── 07_COMPLIANCE_LEGAL/                # Regulatory compliance
│   ├── LEGAL-01_PDPL_DOCUMENTS/        # Draft legal documents
│   ├── LEGAL-02_ROPA_REGISTER/         # Record of Processing Activities
│   ├── LEGAL-03_DPIA/                  # Data Protection Impact Assessment
│   ├── LEGAL-04_DSR_API/               # Data Subject Rights API
│   ├── LEGAL-05_BREACH_RESPONSE/       # Data breach response plan
│   └── LEGAL-06_TERMS_VERSIONING/      # Document versioning
│
├── 08_PILOT_OPERATIONS/                # Pilot operations
│   ├── PILOT-01_PILOT_CHARTER/         # Draft authentic Charter
│   ├── PILOT-02_DAILY_LOG_WORKFLOW/    # Daily workflow
│   ├── PILOT-03_WEEKLY_REPORT/         # Weekly reports
│   ├── PILOT-04_USABILITY_TESTS/       # Usability tests
│   ├── PILOT-05_CAPACITY_MEASUREMENT/  # Capacity measurements
│   └── PILOT-06_OWNER_DECISION/        # Owner decision
│
├── 09_DOCUMENTATION/                   # Documentation
│   ├── DOC-01_API_REFERENCE/           # Full OpenAPI reference
│   ├── DOC-02_USER_GUIDES/             # User guides
│   ├── DOC-03_RUNBOOK/                 # Operational runbooks
│   ├── DOC-04_INCIDENT_RESPONSE/       # Incident response
│   └── DOC-05_TROUBLESHOOTING/         # Troubleshooting
│
├── 10_PHASE13_PREP/                    # Phase 13 preparation
│   ├── PHASE13-01_RC_BUILD/            # Release Candidate
│   ├── PHASE13-02_LAUNCH_GATE/         # LAUNCH-GATE-03
│   ├── PHASE13-03_SUPPORT_ROTA/        # Support schedule
│   └── PHASE13-04_ROLLBACK_PLAN/       # Rollback plan
│
├── 11_TEMPLATES/                       # Templates
│   ├── AUDIT_REPORT_TEMPLATE.md
│   ├── INCIDENT_TEMPLATE.md
│   ├── PILOT_WEEKLY_TEMPLATE.md
│   ├── TEST_PLAN_TEMPLATE.md
│   └── ADR_TEMPLATE.md
│
└── 12_TRACKING/                        # Tracking
    ├── DASHBOARD.md                    # Tracking dashboard
    ├── BURNDOWN.md                     # Burndown chart
    ├── RISK_REGISTER.md                # Risk register
    └── DONE_LOG.md                     # Done log
```

---

## 3. Execution Methodology per Discipline

Every development module (upgrade) follows this pattern:

### Phase 1: Discovery
- Collect evidence from the code
- Document the current state with `file:line`
- Identify the gap between current and target

### Phase 2: Planning
- Draft the Goal statement
- Design the Acceptance criteria
- Estimate effort

### Phase 3: Implementation
- Write code with incremental checks
- Unit tests first
- Integration tests second
- Code review

### Phase 4: Verification
- Run tests in an isolated environment
- Record results in `DONE_LOG.md`
- Issue `AUDIT_REPORT`

### Phase 5: Sign-off
- Independent review
- Update `RISK_REGISTER.md`
- Update `DASHBOARD.md`

---

## 4. Global Acceptance Criteria

Each upgrade must prove:

1. **Dynamic tests** (not just mocks)
2. **CI green** on the same commit
3. **Reproducible evidence** in `DONE_LOG.md`
4. **Related documentation updated**
5. **Audit log** for the decision
6. **No regression** in existing features
7. **Immutable evidence**: commit SHA, CI run URL, artifact digest, environment, and redacted output
8. **Independent review** for P0/P1 changes; Security and Privacy approval where data, AI, backup, connector, or schema changes are involved
9. **Negative tests** that prove unauthorized, expired, malformed, and failure paths are rejected safely

---

## 5. Stop Conditions (Gates)

| Gate | Condition | Action |
|---|---|---|
| G1 | Open Critical defect | Freeze all work; immediate remediation |
| G2 | Any baseline, contract, migration, or critical E2E test fails | Freeze the affected gate until remediation and retest |
| G3 | Change to approved documents without ADR | Reject the change |
| G4 | Missing owner signature on exit criterion | Do not proceed to next phase |
| G5 | P0 vulnerability in security scan | Freeze for 48 hours |
| G6 | Privacy, isolation, or operating baseline not approved | No real-user pilot, AI egress, or connector enrollment |
| G7 | External restore drill, RPO, or RTO absent | No release candidate or production promotion |
| G8 | Any baseline, contract, migration, or critical E2E test fails | Do not advance the affected gate |
| G9 | Risk acceptance lacks an accountable owner, expiry, and evidence link | Reject the acceptance |

---

## 6. Roles and Responsibilities

| Role | Responsibilities |
|---|---|
| **Tech Lead** | Architecture review, ADR approval |
| **Backend Lead** | Implement BE-* upgrades |
| **Frontend Lead** | Implement FE-* upgrades |
| **Security Lead** | Implement SECURITY-* upgrades, reviews |
| **QA Lead** | Implement QA-* upgrades, run pipelines |
| **DevOps Lead** | Implement INFRA-* upgrades |
| **Compliance Officer** | Implement LEGAL-* upgrades |
| **Pilot Manager** | Implement PILOT-* upgrades |
| **Owner** | Sign off on exit decisions |

---

## 7. Gate-Driven Delivery Order

| Gate | Indicative duration | Entry condition | Required work | Exit condition |
|---|---:|---|---|---|
| A: Baseline safety | Weeks 0-4 | Plan approved and named owners | C-01..C-04, C-07..C-14, H-01/H-02/H-07/H-08, tenant and contract tests | Zero known Critical/High baseline findings; PostgreSQL isolation and concurrency evidence |
| B: Privacy and operations | Weeks 4-9 | Gate A approved | LEGAL-*, INFRA-*, H-05/H-06, retention, external backup, restore, monitoring, CSP report-only | Legal/Security approval; RPO/RTO restore drill; no unapproved egress |
| C: Controlled integrations | Weeks 9-12 | Gate B approved | H-03/H-04 using synthetic or documented anonymized data only | Egress, identity, replay, failure-mode, and kill-switch evidence |
| D: Product and quality | Weeks 12-17 | Gate C approved | FE-*, QA-*, migration, load, scan, and release smoke work | CI green, contract tests, critical E2E, and rollback drill pass |
| E: Real pilot | Weeks 17-21+ | Gate D plus Legal/Security pilot authorization | PILOT-* and production-like observation | At least three actual-data weekly reports and independent exit review |
| F: Phase 13 | Weeks 21-24+ | Signed Phase 12 GO | PHASE13-* | Launch gate decision with complete evidence packet |

The planning range is 24-32 weeks. Dates become commitments only after team capacity and required external legal review are confirmed.

---

## 8. Success Metrics (KPIs)

| Indicator | Goal | Measurement |
|---|---|---|
| Critical defects | 0 | Approved finding register plus CI/security evidence |
| High defects | 0 | Approved finding register plus CI/security evidence |
| Pytest failures | 0 | `pytest --tb=short` |
| mypy errors | 0 | `mypy apps/` |
| Frontend E2E pass | 100% | `npx playwright test` |
| Coverage (backend) | ≥85% | `pytest --cov=apps` |
| Coverage (frontend) | ≥70% | `vitest --coverage` |
| PDPL readiness | Counsel-approved controls | ROPA + DPIA + DSR + approved legal texts + evidence |
| Pilot weekly reports | ≥3 | Pilot dashboard |
| Owner sign-offs | 3/3 | DASHBOARD.md |

---

## 9. Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Resistance to change | Medium | High | Change mgmt + documentation |
| Skills gap | Medium | Medium | Training + external help |
| Schedule pressure | High | High | Prioritization, MVP |
| Requirement changes | Medium | High | Change control |
| New security vulnerability | Low | High | Daily security scanning |
| Unapproved personal-data egress | Medium | Critical | Gate B approval, egress controls, and audit evidence |
| Restore drill fails or misses RPO/RTO | Medium | Critical | Gate B restore drill and recurring recovery exercise |

---

## 10. How to start now

For each upgrade:
1. Open the file `XX_NAME/00_DISCOVERY.md`
2. Read the discovery that was performed
3. Run the commands in `XX_NAME/01_VERIFICATION.md`
4. Review `XX_NAME/02_GOAL.md`
5. Start with `XX_NAME/03_IMPLEMENTATION.md`
6. Test with `XX_NAME/04_TESTING.md`
7. Record in `DONE_LOG.md`

---

## 11. References

- [PROJECT_CHARTER.md](../docs/PROJECT_CHARTER.md)
- [REQUIREMENTS_BASELINE.md](../docs/REQUIREMENTS_BASELINE.md)
- [ARCHITECTURE_BASELINE.md](../docs/ARCHITECTURE_BASELINE.md)
- [DELIVERY_ROADMAP.md](../docs/DELIVERY_ROADMAP.md)
- [PHASE12_EXIT_DOSSIER.md](../docs/PHASE12_EXIT_DOSSIER.md)

---

**Prepared by the Core Development Team**
**Confidentiality Level:** Internal
