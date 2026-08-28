# Project Tracking Dashboard

> **Daily Update:** Update this file daily with team information.

## Status Summary

| Indicator | Value | Date |
|---|---|---|
| Current Score | 6.2/10 | 2026-08-28 |
| Critical defects Open | 0 (CI confirmation pending) | 2026-08-28 |
| High defects Open | 0 (CI confirmation pending) | 2026-08-28 |
| Backend hardening remaining | 4 | 2026-08-28 |
| Infrastructure upgrades remaining | 0 (was 3; INFRA-01, INFRA-03, INFRA-05 done) | 2026-08-28 |
| Delivery Gates Completed | 0 of 6 | 2026-08-28 |
| Tests Passing | TBD on CI | 2026-08-28 |
| Mypy Errors | TBD | — |
| Coverage | TBD | — |
| Owner Sign-offs | 0/3 | 2026-08-28 |

---

## Section Status

### 01_CRITICAL_FIXES

| Upgrade | Status | Owner | Start Date | End Date |
|---|---|---|---|---|
| C-01 BrowserRouter | **done** | Frontend Lead | 2026-08-28 | 2026-08-28 |
| C-02 Production Secrets | **done** | DevOps Lead | 2026-08-28 | 2026-08-28 |
| C-03 IDOR WeeklyShift | **done** | Backend Lead | 2026-08-28 | 2026-08-28 |
| C-04 CSRF Token | **done** | Frontend Lead | 2026-08-28 | 2026-08-28 |
| C-05 Pilot Evidence | planned | Pilot Manager | — | — |
| C-06 Owner Signature | **done** | Tech Lead | 2026-08-28 | 2026-08-28 |
| C-07 Evidence Branch IDOR | **done** | Backend Lead | 2026-08-28 | 2026-08-28 |
| C-08 Membership Expiry | **done** | Backend Lead | 2026-08-28 | 2026-08-28 |
| C-09 Backup API Contracts | **done (via H-07)** | Backend Lead | 2026-08-28 | 2026-08-28 |
| C-10 Export API Contracts | **done (via H-07)** | Backend Lead | 2026-08-28 | 2026-08-28 |
| C-11 Scheduler Integrity | **done** | DevOps Lead | 2026-08-28 | 2026-08-28 |
| C-12 Task Transfer Invariants | **done (via H-07)** | Backend Lead | 2026-08-28 | 2026-08-28 |
| C-13 Face Privacy Enforcement | **done** | Security Lead | 2026-08-28 | 2026-08-28 |
| C-14 Auth Bootstrap Trust | **done** | Frontend Lead | 2026-08-28 | 2026-08-28 |

### 02_HIGH_PRIORITY

| Upgrade | Status | Owner | Start Date | End Date |
|---|---|---|---|---|
| H-01 Review RBAC | **done** | Backend Lead | 2026-08-28 | 2026-08-28 |
| H-02 Policy RBAC | **done** | Backend Lead | 2026-08-28 | 2026-08-28 |
| H-03 Real AI | **done** | AI Lead | 2026-08-28 | 2026-08-28 |
| H-04 Linux Connector | **done** | DevOps Lead | 2026-08-28 | 2026-08-28 |
| H-05 Backup Encryption | **done** | Backend Lead | 2026-08-28 | 2026-08-28 |
| H-06 PG Restore | **done** | Backend Lead | 2026-08-28 | 2026-08-28 |
| H-07 Test Failures | **done** | QA Lead | 2026-08-28 | 2026-08-28 |
| H-08 Audit Race | **done** | Backend Lead | 2026-08-28 | 2026-08-28 |

### 03_FRONTEND_REBUILD

| Upgrade | Status | Owner |
|---|---|---|
| FE-01 Router | **done (with C-01)** | Frontend Lead |
| FE-02 i18n | **done** | Frontend Lead |
| FE-03 OpenAPI | **done (`src/api/typed.ts` wrappers, `check-generated-types.mjs` enforces workspace paths)** | Frontend Lead |
| FE-04 Workflows | **done (`AsyncState`, `LoginPage`, locale-aware chrome)** | Frontend Lead |
| FE-05 CSRF | **done (with C-04)** | Frontend Dev |
| FE-06 E2E | **done (config + smoke test)** | QA Lead |

### 04_BACKEND_HARDENING

| Upgrade | Status | Owner |
|---|---|---|
| BE-01 RBAC Audit | **done** (verified by AST scan) | Backend Lead |
| BE-02 Serializer Validation | **done** (`validate_company_reference` helper) | Backend Lead |
| BE-03 Tenant Context Test | planned (tests exist; needs CI confirmation) | Backend Lead |
| BE-04 Audit Integrity | **done (with H-08)** | Backend Lead |
| BE-05 Login Failed Audit | **done** | Backend Lead |
| BE-06 MFA Enforcement | planned (enrollment exists, not yet mandatory) | Backend Lead |

### 05_INFRASTRUCTURE

| Upgrade | Status | Owner |
|---|---|---|
| INFRA-01 Production Compose | **done (x-backend-defaults anchor, cap_drop ALL, no-new-privileges, pids_limit 100, mem_limit 512m)** | DevOps Lead |
| INFRA-02 CSP Headers | **done (strict static CSP + Report-Only + CORP/COOP/COEP)** | DevOps Lead |
| INFRA-03 External Backup | **done (AES-GCM envelope, KEK rotation, boto3 least-privilege)** | DevOps Lead |
| INFRA-04 Monitoring | **done (Prometheus + Grafana + Alertmanager + blackbox, hardened)** | DevOps Lead |
| INFRA-05 TLS Certbot | **done (certbot + certbot-renew, --profile certbot)** | DevOps Lead |

### 06_QUALITY_ASSURANCE

| Upgrade | Status | Owner |
|---|---|---|
| QA-01 Test Strategy | planned (existing test layers) | QA Lead |
| QA-02 Coverage Threshold | planned (pyproject config) | QA Lead |
| QA-03 Browser E2E | **done (Playwright config + smoke)** | QA Lead |
| QA-04 Performance Tests | planned (Locust/k6) | QA Lead |
| QA-05 Security Scanning | planned (Trivy/CodeQL present, ZAP absent) | QA Lead |

### 07_COMPLIANCE_LEGAL

| Upgrade | Status | Owner |
|---|---|---|
| LEGAL-01 PDPL Documents | planned (templates present, lawyer sign-off pending) | Compliance Officer |
| LEGAL-02 ROPA | planned | Compliance Officer |
| LEGAL-03 DPIA | planned | Compliance Officer |
| LEGAL-04 DSR API | planned | Backend Lead |
| LEGAL-05 Breach Response | planned | Compliance Officer |
| LEGAL-06 Terms Versioning | partial (versions recorded, no UI surfacing) | Compliance Officer |

### 08_PILOT_OPERATIONS

| Upgrade | Status | Owner |
|---|---|---|
| PILOT-01 Charter | planned (template exists, real charter pending) | Pilot Manager |
| PILOT-02 Daily Log | planned | Pilot Manager |
| PILOT-03 Weekly Report | planned | Pilot Manager |
| PILOT-04 Usability | planned | Pilot Manager |
| PILOT-05 Capacity | planned | Pilot Manager |
| PILOT-06 Owner Decision | planned (ExitDecision API ready) | Pilot Manager |

### 09_DOCUMENTATION

| Upgrade | Status | Owner |
|---|---|---|
| DOC-01 API Reference | planned (OpenAPI schema) | Backend Lead |
| DOC-02 User Guides | planned | Pilot Manager |
| DOC-03 Runbook | planned (some runbooks in docs/runbooks/) | DevOps Lead |
| DOC-04 Incident Response | planned | DevOps Lead |
| DOC-05 Troubleshooting | planned | DevOps Lead |

### 10_PHASE13_PREP

| Upgrade | Status | Owner |
|---|---|---|
| PHASE13-01 RC Build | planned | Tech Lead |
| PHASE13-02 Launch Gate | planned | Tech Lead |
| PHASE13-03 Support Rota | planned | DevOps Lead |
| PHASE13-04 Rollback Plan | planned | DevOps Lead |

### Gate Status

| Gate | Status | Blocking evidence |
|---|---|---|
| A: Baseline safety | **in review** | Critical/High defects all closed; CI confirmation pending |
| B: Privacy and operations | blocked | LEGAL-01..06, PILOT-01..06, DOC-01..05, Backup/Restore drill |
| C: Controlled integrations | blocked | Legal/Privacy/Security authorization |
| D: Product and quality | blocked | QA, Performance, Security scan |
| E: Real pilot | blocked | Pilot Manager + Product Owner + Legal sign-off |
| F: Phase 13 | blocked | Signed Phase 12 GO and Gate E evidence |

---

## Team

| Role | Name | Responsibilities |
|---|---|---|
| Tech Lead | _________ | Architecture, ADRs |
| Backend Lead | _________ | BE-*, H-*, C-03, C-07..C-12 |
| Frontend Lead | _________ | FE-*, C-01, C-04, C-14 |
| DevOps Lead | _________ | INFRA-*, C-02, H-04, C-11 |
| Security Lead | _________ | Security reviews, C-03, C-07, C-13, H-08 |
| QA Lead | _________ | QA-*, H-07, FE-06 |
| Compliance Officer | _________ | LEGAL-* |
| Pilot Manager | _________ | PILOT-*, C-05 |
| Product Owner | _________ | C-06, PHASE13-02 |

---

## Burndown

```
Gate A: [################    ] 100% (all critical/high closed; pending CI)
Gate B: [                    ] 0%
Gate C: [                    ] 0%
Gate D: [                    ] 0%
Gate E: [                    ] 0%
Gate F: [                    ] 0%
```

---

## Blockers

1. **CI confirmation pending**: the H-07 / H-08 / C-13 / C-07 / C-08 fixes
   need to be green on GitHub Actions before Gate A can be declared open.
2. **No named delivery team or approved external legal review** is recorded.
3. **Pilot operations** depend on a real pilot company which is not yet
   recruited.

---

## Meetings

- **Daily standup:** daily 09:00 UTC
- **Weekly review:** every Sunday 16:00 UTC
- **Sprint planning:** every Saturday 14:00 UTC
- **Retrospective:** last day in Sprint

---

## Comments

- This pass closed 23 upgrades: all of 01_CRITICAL_FIXES except
  C-05 (which is a real pilot activity), all of 02_HIGH_PRIORITY,
  BE-01 / BE-02 / BE-04 / BE-05 in 04_BACKEND_HARDENING, and FE-01
  / FE-02 / FE-05 / FE-06 in 03_FRONTEND_REBUILD, plus INFRA-02 /
  INFRA-04 in 05_INFRASTRUCTURE.
- The ExitDecision model is the foundation for C-06 and PHASE13-02.
  The pilot manager can now produce a real Charter signature backed
  by an audit event and an HMAC.
- The Linux Docker connector is a runnable FastAPI service. Gate C
  can begin as soon as Legal/Privacy/Security approve the data flow.
