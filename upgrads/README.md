# Mhami Upgrades Plan
## Comprehensive Development Plan for MHAMI Project

> **Issue:** 1.0.0
> **Date:** 2026-08-28
> **Goal:** Move the project from "components present" to "components proven valid"

---

## Quick Start

1. **Read:** [00_PLAN_INDEX.md](./00_PLAN_INDEX.md) - Main index
2. **Explore:** Folders 01-10 based on the section you are working on
3. **Track:** [12_TRACKING/DASHBOARD.md](./12_TRACKING/DASHBOARD.md) - Tracking dashboard
4. **Log:** [12_TRACKING/DONE_LOG.md](./12_TRACKING/DONE_LOG.md) upon completion

---

## Folder Structure

```
upgrads/
├── 00_PLAN_INDEX.md                 # Main index
├── 01_CRITICAL_FIXES/               # Critical fixes (14)
├── 02_HIGH_PRIORITY/                # High-priority fixes (8)
├── 03_FRONTEND_REBUILD/             # Frontend rebuild (6)
├── 04_BACKEND_HARDENING/            # Backend hardening (6)
├── 05_INFRASTRUCTURE/               # Infrastructure (5)
├── 06_QUALITY_ASSURANCE/            # Quality assurance (5)
├── 07_COMPLIANCE_LEGAL/             # Regulatory compliance (6)
├── 08_PILOT_OPERATIONS/             # Pilot operations (6)
├── 09_DOCUMENTATION/                # Documentation (5)
├── 10_PHASE13_PREP/                 # Production preparation (4)
├── 11_TEMPLATES/                    # Templates (5)
└── 12_TRACKING/                     # Tracking (6)
```

**Scope:** 65 delivery upgrades, plus templates and tracking artifacts.

---

## Priorities

### Gate A: Security and functional baseline
- [ ] C-01..C-04 and C-07..C-14
- [ ] H-01, H-02, H-07, H-08
- [ ] No real AI, connector, or pilot data during this gate

### Gate B: Privacy and operating baseline
- [ ] Legal document lifecycle, ROPA, DPIA, DSR, retention and purge
- [ ] Encrypted external backups and a production-equivalent restore drill
- [ ] Production Compose, TLS, CSP report-only, monitoring and alert routing

### Gate C: Controlled integrations
- [ ] Real AI provider and connector only with synthetic or documented anonymized data
- [ ] Security, privacy, egress, failure-mode, and kill-switch evidence

### Gate D/E: Product readiness and pilot
- [ ] Frontend workflows, OpenAPI contracts, E2E, load, migration, and release smoke tests
- [ ] A minimum three-week real pilot after legal and security authorization

---

## Indicators (KPIs)

| Indicator | Current | Target |
|---|---|---|
| Critical defects | 14 | 0 |
| High defects | 8 | 0 |
| Tests passing | 86/91 | 91/91 |
| Mypy errors | 9 | 0 |
| Coverage | TBD | ≥85% |
| PDPL compliance | 1.0/10 | Counsel-approved controls and evidence; not a self-score |
| Owner sign-offs | 0/3 | 3/3 |

---

## Stop Conditions (Gates)

| Gate | Condition | Action |
|---|---|---|
| G1 | Open Critical defect | Freeze the affected release path; remediate and retest |
| G2 | Any baseline, contract, migration, or critical E2E test fails | Do not advance the affected gate |
| G3 | Change to approved documents without ADR | Reject the change |
| G4 | Missing owner signature on exit criterion | Do not proceed to the next phase |
| G5 | P0 vulnerability in security scan | Freeze the affected release path pending remediation and retest |
| G6 | Privacy, isolation, or operating baseline not approved | No real-user pilot, AI egress, or connector enrollment |
| G7 | External restore drill, RPO, or RTO absent | No release candidate or production promotion |
| G8 | Any baseline, contract, migration, or critical E2E test fails | Do not advance the affected gate |

---

## Roles

| Role | Responsibilities |
|---|---|
| Tech Lead | Architecture, ADRs, Overall |
| Backend Lead | BE-*, H-*, C-*, BE-01..06 |
| Frontend Lead | FE-*, C-01, C-04, FE-05 |
| DevOps Lead | INFRA-*, C-02, H-04 |
| Security Lead | Security, C-03, H-08, BE-05 |
| QA Lead | QA-*, H-07, FE-06 |
| Compliance Officer | LEGAL-* |
| Pilot Manager | PILOT-*, C-05 |
| Platform Owner | C-06, PHASE13-02 |

---

## Schedule Timeline

The schedule is gate-driven, not a promise that every item can fit into a fixed
two-week sprint. It requires named staffing and approved parallel work before
any duration can be committed.

| Gate | Indicative duration | Tasks |
|---|---:|---|
| A | Weeks 0-4 | C-01..C-04, C-07..C-14, RBAC, contracts, baseline tests |
| B | Weeks 4-9 | LEGAL-*, INFRA-*, H-05/H-06, privacy and restore evidence |
| C | Weeks 9-12 | H-03/H-04 in controlled synthetic-data shadow mode only |
| D | Weeks 12-17 | FE-*, QA-*, migrations, load, security, and release smoke |
| E | Weeks 17-21+ | Authorized pilot, at least three weekly reports, independent review |
| F | Weeks 21-24+ | Phase 13 evidence and launch gate |

**Planning range:** 24-32 weeks, subject to team capacity, legal review, and pilot observation duration.

---

## Approach

Every upgrade follows:

1. **Discovery** (00_DISCOVERY.md) - Discovery
2. **Verification** (01_VERIFICATION.md) - Verification commands
3. **Goal** (02_GOAL.md) - Goal and standards
4. **Implementation** (03_IMPLEMENTATION.md) - Implementation guide
5. **Testing** (04_TESTING.md) - Test strategy
6. **Results** (04_RESULTS.md) - Recording results

---

## References

- [PROJECT_CHARTER.md](../docs/PROJECT_CHARTER.md)
- [REQUIREMENTS_BASELINE.md](../docs/REQUIREMENTS_BASELINE.md)
- [ARCHITECTURE_BASELINE.md](../docs/ARCHITECTURE_BASELINE.md)
- [DELIVERY_ROADMAP.md](../docs/DELIVERY_ROADMAP.md)
- [PHASE12_EXIT_DOSSIER.md](../docs/PHASE12_EXIT_DOSSIER.md)
- [SECURITY_THREAT_MODEL.md](../docs/SECURITY_THREAT_MODEL.md)
- [TEST_STRATEGY.md](../docs/TEST_STRATEGY.md)

---

## Important Note

> This plan is based on an independent adversarial audit. The tracked launch blockers include 14 critical items and 8 high-priority items; the register remains open to newly evidenced findings.
> **The project cannot be considered production-ready until all Critical and High defects are closed.**

---

**Prepared by the Core Development Team**
**Confidentiality Level:** Internal
**Next:** Open [00_PLAN_INDEX.md](./00_PLAN_INDEX.md)
