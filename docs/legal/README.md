# Legal Policy Workspace

## Status

Placeholder only. These files must be drafted and reviewed by qualified
legal counsel before use. **Until the legal text is reviewed and
approved, the platform records placeholder acceptance only and the
documents are not binding.**

## Directory Layout

```
docs/legal/
├── README.md                          # this file
├── 01_TERMS_OF_USE/
│   ├── v1.0.md
│   └── CHANGELOG.md
├── 02_PRIVACY_NOTICE/
│   ├── v1.0.md
│   └── CHANGELOG.md
├── 03_DATA_PROCESSING_TERMS/
│   ├── v1.0.md
│   └── CHANGELOG.md
├── 04_AI_TRANSFER_NOTICE/
│   ├── v1.0.md
│   └── CHANGELOG.md
├── 05_EMPLOYEE_PRIVACY/
│   ├── v1.0.md
│   └── CHANGELOG.md
├── 06_RETENTION_DELETION/
│   ├── v1.0.md
│   └── CHANGELOG.md
├── 07_SUPPORT_ACCESS/
│   ├── v1.0.md
│   └── CHANGELOG.md
├── 08_TEMPLATES/
│   └── README.md                      # shared drafting templates
├── 09_DPIA/                           # Data Protection Impact Assessment
├── 10_BREACH_RESPONSE/                # Data Breach Response Plan
└── 11_ROPA/                           # Record of Processing Activities
```

## Required Documents

- **01_TERMS_OF_USE** — company self-registration, 30-day trial,
  suspension, 90-day read-only export window, deletion lifecycle,
  owner responsibility for AI provider selection.
- **02_PRIVACY_NOTICE** — controller/processor split, data
  categories, employee acknowledgement, blur behaviour.
- **03_DATA_PROCESSING_TERMS** — controller/processor instructions,
  support access, sub-processor disclosures, retention and deletion.
- **04_AI_TRANSFER_NOTICE** — owner acceptance requirement,
  permitted data set, company-controlled provider, revocation.
- **05_EMPLOYEE_PRIVACY** — first-use acknowledgement, task evidence
  scope, branch access, blur and retention behaviour.
- **06_RETENTION_DELETION** — active and suspended-tenant retention,
  backup expiry, hard-delete path.
- **07_SUPPORT_ACCESS** — per-individual grant, auditability, expiry
  semantics, MFA on support accounts.
- **09_DPIA** — assessment for face-blur evidence, AI analysis, and
  hosting/backup transfer risk.
- **10_BREACH_RESPONSE** — severity matrix, response procedure,
  notification timelines, response team.
- **11_ROPA** — Record of Processing Activities for every processing
  purpose, exported through the `apps/compliance` API.

## Product Requirements for Legal Text

- The company is the data controller; the platform is the processor.
- The owner accepts versioned policies before continued
  administration after material updates (`LegalAcceptance`).
- Employees acknowledge the applicable privacy notice on first use
  (`LegalAcceptance`, `document_type="employee_privacy"`).
- External AI transfer is permitted only after explicit owner
  acceptance (`LegalAcceptance`, `document_type="ai_transfer"`).
- Tenant data has a 90-day read-only export period after suspension
  or cancellation, followed by deletion through the documented
  backup-expiry process.

## Versioning Rules

- A new version is published by writing `vX.Y.md` in the relevant
  document directory and appending an entry to its `CHANGELOG.md`.
- The platform exposes the current published version through the
  `LegalDocument` registry (`apps/tenancy/models.py`).
- When the current version changes, the owner is required to
  re-accept before continued administration; the
  `AcceptanceView` and the staging `record_pilot_acceptances`
  command both honour the new version.

## Gate Dependency

No real-user pilot, external AI transfer, connector enrolment with
personal data, or production promotion may occur until the
applicable Legal, Security, and Privacy approvals are recorded.
Drafting documents is not itself evidence of PDPL readiness.
