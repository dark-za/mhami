# Security and Data Baseline

## Security Standard

Use OWASP ASVS 5.0 Level 2 as the application-security baseline. Security controls are phase gates, not a final polish task.

## Tenant and Authorization Rules

- Every data access is scoped to a company before object resolution.
- Branch-sensitive data is additionally scoped through `UserBranchMembership`.
- Platform Support access is denied unless the company has an active authorization grant.
- Support, owner, monitor, and employee actions are performed by individual user identities, never shared accounts.
- IDOR, tenant escape, branch escape, and stale-session tests are mandatory.

## Identity Rules

- Use a custom Django user model before the first migration.
- Use secure cookie sessions, CSRF protection, rate limiting, and Django password hashing.
- Require TOTP or passkey MFA for Platform Administrators and Company Owners.
- Company code is a tenant locator, not a secret.
- Registration is protected against automation even though manual identity verification is not required.

## Audit Integrity

- Audit and status events are append-only.
- Each relevant event records actor UUID, timestamp, request ID, tenant, branch when applicable, before/after data, and source metadata.
- Internal cryptographic integrity protection must make unexpected event alteration detectable.
- Audit attribution is not a legally qualified external electronic signature in V1.

## Media Security

- Accept only JPEG, PNG, and WebP within platform limits.
- Validate signatures and image safety; do not trust browser content type.
- Keep media private and outside any public web root.
- Run quarantine, validation, hashing, duplicate assessment, and face-derivative processing before media becomes ready.
- Never expose a permanent public media URL.
- A face-containing source is not retained after its blurred derivative is created. The derivative is the stored evidence and external AI input.
- Gallery, video, location, and offline evidence are excluded from V1.

## AI and Connector Security

- AI jobs run only outside the HTTP request path.
- Provider credentials are encrypted at rest and never exposed to frontend code, logs, or exports.
- External data transfer requires tenant-owner acceptance of a versioned notice.
- Provider results must validate against the structured-output contract.
- Private endpoints are reached through the tenant connector, not by arbitrary direct network access from the shared SaaS runtime.
- The connector must be authenticated, versioned, health-checked, least-privileged, and able to be revoked.
- AI cannot automatically create disciplinary consequences. Human-approved final outcomes drive any allowed operational restriction.

## Privacy and Retention

- The tenant company is the data controller; the platform acts as processor under versioned terms.
- Employees acknowledge the applicable privacy notice on first use.
- Active tenant data remains according to the approved retention policy. Suspended or cancelled tenants receive a 90-day read-only export period before deletion.
- Deletion includes primary records and media, then backups at the next documented backup-expiry cycle, subject to lawful retention exceptions.
- Terms of use, privacy notice, and AI transfer notice are versioned and require owner acceptance before continued administration after a material update.

## Operations Security

- No secrets in Git, images, logs, or browser builds.
- Separate DEV, TEST, STAGING, and PRODUCTION databases.
- Production rollout requires staging verification, backup verification, migration review, and smoke testing.
- The initial host is a known single point of failure until the inventory and backup design are approved.
