# Risk Register

> **Update:** weekly
> **Reference:** PHASE12_RELEASE_RISK_REGISTER (existing in docs/)

## Active Risks

> Before a risk can be marked accepted, deferred, or closed, record its
> mitigation, accountable owner, target date, residual likelihood/impact,
> approval, expiry, and immutable evidence link in the linked decision record.
> A status word or checkbox is not risk evidence.

| ID | Category | Risk | Likelihood | Impact | Owner | Status |
|---|---|---|---|---|---|---|
| RR-01 | Security | CSRF broken in the frontend (C-04) | Certain | Critical | Frontend Lead | Open |
| RR-02 | Security | IDOR in WeeklyShift (C-03) | Certain | Critical | Backend Lead | Open |
| RR-03 | Security | No login_failed recording (BE-05) | High | High | Backend Lead | Open |
| RR-04 | Operational | Production compose fails without secrets (C-02) | Certain | Critical | DevOps Lead | Open |
| RR-05 | Operational | BrowserRouter nested (C-01) | Certain | Critical | Frontend Lead | Open |
| RR-06 | Legal | Legal documents are placeholders (LEGAL-01) | Certain | Critical | Compliance Officer | Open |
| RR-07 | Compliance | PDPL readiness 1.0/10 | Certain | Critical | Compliance Officer | Open |
| RR-08 | Operational | Pilot evidence empty (C-05) | Certain | Critical | Pilot Manager | Open |
| RR-09 | Process | Owner signature empty (C-06) | Certain | High | Tech Lead | Open |
| RR-10 | Quality | 5 pytest failures Open (H-07) | High | High | QA Lead | Open |
| RR-11 | Quality | 9 mypy errors (H-07) | High | Medium | QA Lead | Open |
| RR-12 | Operational | No real AI provider (H-03) | Certain | Critical | AI Lead | Open |
| RR-13 | Operational | No Linux connector (H-04) | Certain | Critical | DevOps Lead | Open |
| RR-14 | Security | No backup encryption (H-05) | High | High | Backend Lead | Open |
| RR-15 | Operational | backup restore to SQLite only (H-06) | High | High | Backend Lead | Open |
| RR-16 | Operational | BACKUP_EXTERNAL_URI not used | Certain | Medium | Backend Lead | Open |
| RR-17 | Quality | Audit chain race condition (H-08) | Low | High | Backend Lead | Open |
| RR-18 | Compliance | No DSR API (LEGAL-04) | Certain | Critical | Compliance Officer | Open |
| RR-19 | Compliance | No ROPA (LEGAL-02) | Certain | High | Compliance Officer | Open |
| RR-20 | Compliance | No DPIA (LEGAL-03) | Certain | High | Compliance Officer | Open |
| RR-21 | Security | Evidence and issue branch IDOR (C-07) | Certain | Critical | Backend Lead | Open |
| RR-22 | Security | Expired memberships retain access (C-08) | Certain | Critical | Backend Lead | Open |
| RR-23 | Functional | Backup API contracts are broken (C-09) | Certain | Critical | Backend Lead | Open |
| RR-24 | Privacy | Export contracts and minimization are broken (C-10) | Certain | Critical | Backend Lead | Open |
| RR-25 | Operational | Scheduler jobs and recovery are incomplete (C-11) | Certain | Critical | Backend Lead | Open |
| RR-26 | Security | Transfer race and stale executor state (C-12) | High | High | Backend Lead | Open |
| RR-27 | Privacy | Client-controlled face privacy flag (C-13) | Certain | Critical | Security Lead | Open |
| RR-28 | Security | Demo bootstrap can misrepresent authenticated authorization (C-14) | High | High | Frontend Lead | Open |

## Closed Risks

| ID | Description | Date Closed | By |
|---|---|---|---|
| RR-04 | Production compose fails without secrets (C-02 + INFRA-01) | 2026-08-28 | DevOps Lead |
| RR-16 | BACKUP_EXTERNAL_URI not used (INFRA-03) | 2026-08-28 | Backend Lead |

## Heat Map

```
         Impact →
         Low   Medium   High    Critical
Likelihood ↓
Certain      -        -       -       1, 2, 5, 6, 7, 8, 12, 13, 18, 21, 22, 23, 24, 25, 27
High      -        -       3, 10, 14, 15, 19, 20, 26, 28
Low     -        -       17      -
Remote    -        -       -       -
```

(Numbers refer to RR-IDs above)

## General Mitigation Plan

### Critical Risks
- **Tracked in Gate A or Gate B according to the dependency table**
- Daily review
- Dedicated owner for each
- Strict "definition of done"

### High Risks
- **Tracked before the affected gate can advance**
- Weekly review
- Deep testing

### Medium Risks
- **Tracked before release candidate approval**
- Review every sprint
