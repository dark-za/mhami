# Record of Processing Activities (ROPA) — v1.0

## Status

**Living document, platform-side. The published rows are the source of truth for the `/api/v1/compliance/ropa` endpoint.**

The ROPA is the platform's record of every documented processing
activity the platform performs on the controller's behalf. Each row
in the database is published through the management command
`python manage.py seed_ropa`; the seed data is the canonical
platform-side record.

## Versioning

| Field | Value |
| --- | --- |
| Document type | Record of Processing Activities |
| Document version | v1.0 |
| Effective date | _pending legal review_ |
| Approved by | _pending_ |
| Review cadence | Annual or on material change |

## Structure

| Field | Source |
| --- | --- |
| Name | Unique processing-activity name (the ROPA key). |
| Purpose | Plain-language statement of the purpose. |
| Controller | The legal controller (the tenant company, by default). |
| Processor | The processor label, defaults to "Mhami Platform". |
| Data categories | Iterable of personal-data categories. |
| Data subject categories | Iterable of data subject categories. |
| Recipients | Iterable of recipient categories. |
| Lawful basis | One of `LegalBasis` values. |
| Cross-border transfer | Boolean. |
| Transfer mechanism | Free-text, required when cross-border is true. |
| Retention days | Integer. |
| Security measures | Plain-language description of the measures. |
| Last reviewed at | ISO date. |

The fields mirror `apps/compliance/models.ProcessingActivity`.

## Seeded Activities

The platform ships with the following rows. They are the
documented baseline; a tenant may add additional rows through the
compliance API as the company grows.

### 1. Company Registration

- **Name.** Company Registration
- **Purpose.** Onboarding new tenant companies and their initial
  owner account.
- **Controller.** Tenant company (self-registered).
- **Data categories.** Company name, code, industry, contact
  email/phone, owner login id, owner display name.
- **Data subject categories.** Business owners.
- **Recipients.** Internal platform staff.
- **Lawful basis.** Contract performance.
- **Cross-border transfer.** No.
- **Retention.** Active contract + 90 days.
- **Security measures.** Encryption at rest, TLS in transit, MFA
  on owner login, audited registration events.

### 2. Evidence Capture

- **Name.** Evidence Capture
- **Purpose.** Collecting direct task evidence (camera images,
  numeric data, notes) for review and audit.
- **Controller.** Tenant company.
- **Data categories.** Camera images, blurred derivatives, numeric
  inputs, free-form notes, task metadata.
- **Data subject categories.** Employees, third parties
  incidentally captured in evidence.
- **Recipients.** Branch monitors, company owner, audit process.
- **Lawful basis.** Legitimate interests.
- **Cross-border transfer.** No.
- **Retention.** 180 days.
- **Security measures.** Private media storage, signed access URLs,
  face-blur derivatives before release for review, tenant-scoped
  authorization.

### 3. Review and Decisions

- **Name.** Review and Decisions
- **Purpose.** Recording quality-monitor and owner decisions.
- **Controller.** Tenant company.
- **Data categories.** Decision payload, decision rationale,
  monitor identity, branch scope.
- **Data subject categories.** Employees, monitors, owners.
- **Recipients.** Tenant owner, audit process.
- **Lawful basis.** Legitimate interests.
- **Cross-border transfer.** No.
- **Retention.** 365 days.
- **Security measures.** Append-only audit chain, HMAC integrity,
  branch-scoped access, role-required authorization.

### 4. External AI Analysis

- **Name.** External AI Analysis
- **Purpose.** Sending permitted task criteria, opaque reference
  media identifiers, and blurred evidence derivatives to the
  tenant-selected AI provider for verification assistance.
- **Controller.** Tenant company.
- **Data categories.** Task criteria, reference media id, blurred
  evidence derivatives.
- **Data subject categories.** No personal data; blurred
  derivatives only.
- **Recipients.** Tenant-selected AI provider.
- **Lawful basis.** Consent.
- **Cross-border transfer.** Yes.
- **Transfer mechanism.** Per-tenant provider contract; transfer
  only after explicit owner acceptance of the AI Transfer Notice.
- **Retention.** 30 days.
- **Security measures.** Owner-controlled endpoint and credentials,
  opaque identifiers, blurred derivatives only, in-flight
  cancellation on revocation.

### 5. Tenant Support

- **Name.** Tenant Support
- **Purpose.** Providing named platform support access on explicit
  owner request.
- **Controller.** Tenant company.
- **Data categories.** Support user id, grant reason, grant
  expiry, support actions.
- **Data subject categories.** Company owner, support users.
- **Recipients.** Platform support team, tenant owner.
- **Lawful basis.** Legitimate interests.
- **Cross-border transfer.** No.
- **Retention.** 365 days.
- **Security measures.** Per-individual grants, audit logging,
  expiry semantics, MFA on support accounts.

### 6. Export and Deletion

- **Name.** Export and Deletion
- **Purpose.** Owner-initiated export during the 90-day read-only
  window and subsequent hard deletion.
- **Controller.** Tenant company.
- **Data categories.** Exported company data, deletion proof.
- **Data subject categories.** Company owner, employees.
- **Recipients.** Company owner.
- **Lawful basis.** Legal obligation.
- **Cross-border transfer.** No.
- **Retention.** 90 days.
- **Security measures.** Owner-only export authorization, signed
  and expiring download URLs, audited export action, hard delete
  at end of window with backup expiry through documented cycle.

## API and Re-seeding

- The ROPA is published through `GET /api/v1/compliance/ropa`.
- The ROPA is reseeded through
  `python manage.py seed_ropa --last-reviewed-at YYYY-MM-DD`. The
  command is idempotent and updates the `last_reviewed_at` stamp
  for every row.
- A new processing activity is added by extending
  `SEED_ACTIVITIES` in
  `apps/compliance/management/commands/seed_ropa.py` and
  re-running the command.
