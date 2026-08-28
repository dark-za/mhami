# Security Threat Model

## Status and scope

**Status:** Phase 3a baseline complete; review at every material architecture or
dependency change. **Decision authority:** Security owner, with the release
owner accountable for accepting residual risk.

This register covers the V1 browser client, Django API, PostgreSQL, Redis/Celery,
private media, tenant connectors, AI providers, exports, backups, and the
single-host deployment. Likelihood and impact use Low/Medium/High/Critical.
Residual risk is the risk remaining after the listed controls. A release
decision of **Go** means the control is required and its verification must pass;
**Conditional** requires a documented owner acceptance before production.

## Threat register

| ID / threat | Likelihood | Impact | Preventive and detective controls | Owner | Verification | Residual risk | Release decision |
|---|---|---|---|---|---|---|---|
| TM-01 Cross-company object/IDOR access | Medium | Critical | Resolve objects through the active company; serializer and service tenant checks; deny missing company context | Backend owner | Tenant isolation API tests and negative cross-company tests | Low | Go if tests pass |
| TM-02 Cross-branch authorization escape | Medium | High | Branch memberships; owner/monitor all-branch rule; branch checks before capture and media access | Identity owner | Branch-scope service/API tests | Low | Go if tests pass |
| TM-03 Account takeover, credential stuffing, session theft | High | Critical | Django password hashing; secure/HTTP-only session cookies; CSRF; rate limiting at edge; short-lived capture tokens; incident revocation runbook | Identity owner | Staging login abuse test; cookie/header inspection; incident drill | Medium | Conditional on production rate limiting |
| TM-04 MFA recovery or privileged-account abuse | Medium | Critical | MFA required for administrators and owners; individual identities; support authorization grants expire and are audited | Identity owner | MFA/recovery test and support-grant audit assertions | Medium | Conditional on MFA enforcement in deployment |
| TM-05 Trial self-registration abuse and company-code enumeration | High | Medium | Registration automation controls; generic lookup responses; company code is not treated as a secret; monitoring and throttling | Product/security owner | Registration abuse and response-equivalence tests | Medium | Conditional on edge throttling |
| TM-06 Malformed, multi-extension, or decompression-bomb upload | High | High | Strict single extension and MIME/signature agreement; byte limit; Pillow verification; source-pixel limit; quarantine before processing | Evidence owner | Focused upload tests for polyglots, malformed images, oversized dimensions, and cleanup | Low | Go if focused tests pass |
| TM-07 Quarantine/private-media residue after processing failure | Medium | High | Transactional processing; `finally` cleanup for quarantine and partial derivatives; private storage outside web root | Evidence owner | Inject failures at decode, derivative, database, and audit steps; assert no residue | Low | Go if cleanup tests pass |
| TM-08 Duplicate evidence, gallery replay, face privacy, unauthorized media retrieval | Medium | High | One-use expiring capture session; branch-scoped perceptual hash; face blur derivative; no public media URLs; access checks | Evidence owner | Capture reuse, duplicate branch-scope, face derivative, and media IDOR tests | Low | Go |
| TM-09 AI prompt injection or unsafe image content | High | High | Treat media as untrusted; derivative-only AI input; structured output validation; human approval for consequential action; no direct disciplinary automation | AI owner | Adversarial fixture tests and provider contract tests | Medium | Conditional on AI gateway gates |
| TM-10 AI provider outage, invalid output, or data-transfer violation | Medium | High | Async jobs; timeout/retry policy; provider credentials isolated; versioned tenant transfer acceptance; reject invalid schema | AI owner | Provider outage/invalid-output tests and acceptance audit review | Medium | Conditional on staging outage test |
| TM-11 Connector enrollment compromise or network isolation failure | Medium | Critical | Authenticated/versioned enrollment; least privilege; health checks; revocation; private endpoint boundary; update review | Connector owner | Enrollment, revocation, offline, and network-boundary tests | Medium | Conditional on connector staging evidence |
| TM-12 Export leakage or support-access abuse | Medium | Critical | Tenant-scoped exports; private/expiring artifacts; explicit support authorization; access and download audits | Platform owner | Export isolation and support authorization API tests | Low | Go if tests pass |
| TM-13 Audit tampering or repudiation | Medium | High | Append-only model; SHA-256 previous-event chain; per-event HMAC; migration backfill; chain verification and alerting | Security/platform owner | Tamper field/chain/HMAC tests and migration verification | Low | Go if verification is scheduled |
| TM-14 Legal-policy acceptance gap | Medium | High | Versioned terms, privacy, and AI-transfer notices; owner acceptance required after material change; employee acknowledgement | Compliance owner | Acceptance reconciliation and blocked-action tests | Medium | Conditional on current versions |
| TM-15 Database or Redis compromise/failure | Medium | Critical | Least-privileged service accounts; tenant scoping; health checks; transaction boundaries; encrypted/retained backups; restore isolation | Operations owner | Failure injection, backup integrity, and isolated restore tests | Medium | Conditional on production restore evidence |
| TM-16 Private storage or queue failure | Medium | High | Storage outside public root; quarantine/private separation; retryable asynchronous jobs; cleanup task and health endpoint | Operations owner | Storage outage and queue retry/cleanup test | Medium | Conditional on alerting |
| TM-17 Backup disclosure, corruption, or restore overwrite | Medium | Critical | Manifest and whole-archive hashes; tamper rejection; tenant-scoped selection; restore only to isolated database; restricted backup destination | Operations owner | Backup tamper and restore tests; access review | Medium | Conditional on encrypted second destination |
| TM-18 Deployment/configuration or secret leakage | Medium | Critical | No secrets in Git/images/logs/frontend; production secret checks; migration review; staging smoke tests; pinned dependencies | Release owner | CI secret/dependency scan and deployment checklist | Low | Go if release gates pass |
| TM-19 Single-server or regional availability failure | Medium | High | Documented RTO/RPO; tested backups and restore runbook; health monitoring; rollback procedure; capacity alerts | Operations owner | Restore and resilience drill | High until redundant host | Conditional; owner acceptance required |

## Release gate

Production release is blocked when any Go row fails verification, when a
Conditional prerequisite lacks written owner acceptance, or when a new
architecture/dependency change has not been threat-modeled. Residual risks,
exceptions, and compensating controls are recorded in the release risk
register and reviewed at least quarterly and after every security incident.
