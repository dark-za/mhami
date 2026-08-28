# Data Protection Impact Assessment (DPIA) — v1.0

## Status

**Living document, platform-side. Requires sign-off by the Data Protection Officer and Platform Owner before any real-user pilot, external AI transfer, or production promotion.**

This is the platform-side DPIA. The tenant company is the controller
and remains the primary subject of any tenant-specific DPIA it chooses
to maintain. This document records the platform's assessment of the
processing activities the platform performs on the controller's
behalf.

## Versioning

| Field | Value |
| --- | --- |
| Document type | Data Protection Impact Assessment |
| Document version | v1.0 |
| Effective date | _pending legal review_ |
| Approved by | _pending_ |
| Review cadence | Annual or on material change |

## 1. Description of the Processing

### Nature

- The platform is a multi-tenant web application that captures
  task evidence (camera images, numeric data, notes) for review by
  branch-scoped monitors and the company owner.
- A face-blur derivative is produced when a face is detected by
  the approved server-side detector; the original is held under
  stricter access controls.
- The platform offers a tenant-controlled AI provider for
  verification assistance. The provider is selected by the company
  owner; the platform never injects a default provider.
- The platform retains audit history for every operational action.

### Scope

- **Data subjects.** Tenant company owners, branch-scoped monitors,
  employees, and any third parties incidentally captured in
  evidence media.
- **Data categories.** Account data, organisation data, operational
  data, evidence media (raw and blurred), AI configuration,
  audit and security data, export artefacts.
- **Duration.** Active tenants retain data for the lifetime of the
  contract plus the 90-day read-only export window. Audit history
  is retained per the audit policy.

### Context

- The first internal pilot uses an organisation with three branches
  and approximately thirty employees in the food-service sector.
  Real-user pilot data and customer scope are still inventory-
  dependent.
- The deployment target is a self-hosted, single-region production
  host behind Cloudflare Tunnel. Backup contents are encrypted and
  transmitted to a second destination.

### Purpose

- The platform exists to make operational work auditable: who did
  what, when, with what evidence, and under whose authorisation.

## 2. Necessity Assessment

| Capability | Less-intrusive alternative considered | Why the alternative is not sufficient |
| --- | --- | --- |
| Camera evidence | Manual logs, third-party photo apps | Manual logs are not tenant-scoped, not auditable, and not branch-scoped. |
| Face blur | No capture of incidental third parties | Capture is the documented purpose; without it, evidence is unverifiable. |
| AI verification | Manual review only | Manual review alone is unscalable; AI is a verification aid, not an authority. |
| Audit log | Ad-hoc application logs | Ad-hoc logs are not tamper-evident or tenant-isolated. |

The processing is **proportionate** to the documented purpose. Each
identifier is the minimum required to attribute evidence, branch-
scope, and authorisation.

## 3. Risk Assessment

| Risk | Likelihood | Impact | Inherent rating |
| --- | --- | --- | --- |
| Face image capture without a trusted server-side detector | High | High | **High** |
| AI analysis sent to an unauthorised destination | Medium | High | High |
| Cross-border transfer of personal data without a documented basis | Medium | High | High |
| Backup contents become accessible from a non-encrypted location | Low | High | Medium |
| Evidence media exposed through a misconfigured access URL | Medium | High | High |
| Audit log tampering | Low | High | Medium |
| Support access used to read data outside the granted scope | Low | High | Medium |
| Tenant deletion leaving a residual record in backups | Low | Medium | Low |

## 4. Mitigation Measures

### Technical

- **Face blur.** A trusted server-side detector is required; the
  raw original is held under stricter access controls; failure
  policies (detector unavailable) are documented in
  `apps/evidence/services.py`. The detector is exercised in the
  release test suite.
- **AI transfer.** Owner acceptance is required per legal basis;
  only the permitted data set is sent; opaque reference media
  identifiers are used; the in-flight analysis is cancelled on
  acceptance revocation. See `apps/ai_gateway/services.py` and
  `apps/compliance/services.py`.
- **Cross-border transfer.** Documented per ROPA entry with a
  transfer mechanism. Cross-border rows require
  ``transfer_mechanism``; the service rejects empty values.
- **Backups.** Encrypted at rest; remote destination is documented;
  restoration is tested, not assumed
  (`docs/PHASE11_RESTORE_TEST_REPORT.md`).
- **Media access.** Signed and expiring URLs; tenant-scoped
  authorization; branch-scope is enforced at the service layer.
- **Audit integrity.** HMAC chain; the chain is verified as part of
  release testing.
- **Support access.** Per-individual grants with an explicit
  reason and an expiry; every support action is audited and the
  authorisation is consulted at the service layer.
- **Tenant deletion.** Hard delete at the end of the read-only
  window; backups expire through the documented cycle; the daily
  sweep is idempotent.

### Organisational

- A Data Protection Officer role is required for production
  promotion; sign-off is captured in
  `docs/PHASE12_AI_AGREEMENT_REPORT.md` and the legal review record.
- The legal-policy documents under `docs/legal/` are reviewed
  annually or on a material change; the per-document `CHANGELOG.md`
  records the review.
- The ROPA is published through `/api/v1/compliance/ropa`; the
  source data is in `apps/compliance/models.py` and is seeded
  by the `seed_ropa` management command.
- DSR intake is reachable at `/api/v1/compliance/dsr`; the
  workflow is owned by the company owner with platform DPO
  visibility through the audit log.
- The breach response plan is at
  `docs/legal/10_BREACH_RESPONSE/README.md`; the incident
  response runbook is at `docs/runbooks/incident-response.md`.

## 5. Consultation

- **Internal.** DPO, Platform Owner, security lead, technical
  team. Consultation is recorded in the release sign-off.
- **External.** Qualified legal counsel. The legal text under
  `docs/legal/` is placeholder until legal counsel has reviewed
  and approved the wording.
- **Data subjects.** Employees acknowledge the privacy notice on
  first use; the acknowledgement is recorded as a
  `LegalAcceptance` row with
  `document_type="employee_privacy"`.

## 6. Conclusion

The platform can demonstrate proportionality, lawful basis, and
mitigation for every documented processing activity **provided** the
legal text is reviewed and the technical controls above remain in
force. Real-user pilot, external AI transfer, connector enrolment
with personal data, and production promotion are gated on this
review.
