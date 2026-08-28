# Project Charter

## Status

Approved planning baseline. No implementation has started.

## Product Mission

Deliver a secure, multi-tenant web platform that helps organizations prove work was performed, collect direct evidence, identify exceptions, correct issues, and understand operational performance.

The platform must make the employee experience simple, give quality monitors an exception-focused workspace, give owners control and concise insight, and give engineers explicit module boundaries.

## Product Boundary

The platform is sector-neutral. A company selects an industry from a controlled list with an `Other` option. The initial list includes restaurants and cafes, retail, and logistics. Industry selection recommends starter templates only; it never prevents a company from creating permitted task templates.

The first internal pilot will use an organization with three to five branches and approximately thirty employees. Restaurant-oriented templates are initial reference content, not a platform dependency.

## V1 In Scope

- Self-service company registration with a unique permanent company code chosen by the owner.
- A 30-day trial, manual extension, suspension, read-only export period, and deletion lifecycle.
- Core roles: Platform Administrator, Company Owner, Quality Monitor, and Employee.
- Branch-scoped operational work, simple weekly shifts, task templates, schedules, task instances, review, and reporting.
- Camera-live image evidence, numeric evidence, notes, confirmations, task discussions, and structured corrective decisions.
- Tenant-controlled AI provider configuration through a standard contract and a Linux Docker connector.
- Arabic and English user interfaces, selectable Gregorian or Hijri date display, and Chrome-only browser support.
- Private platform media storage, owner/monitor-scoped exports, structured audit, security controls, and operational readiness.

## Explicitly Out of Scope for V1

- Accounting, payroll, inventory, purchasing, POS, full HR, workforce attendance, and full maintenance systems.
- Public file uploads, gallery evidence uploads, video evidence, GPS evidence, and offline task submission.
- PWA installation, service worker caching, and offline synchronization.
- Arbitrary code or plugin uploads from a user interface.
- External notification providers, external archive providers, and customer-facing payment processing. Their extension points may be planned, not implemented.
- Legal compliance certification, facial recognition, emotion detection, biometric profiling, or automatic disciplinary decisions.

## Success Conditions

- Organizations can configure branches, users, shifts, templates, and policies without developer intervention.
- Employees can perform assigned work from Chrome, capture direct evidence, understand the next action, and receive only relevant notifications.
- Quality monitors see alerts, overdue tasks, resubmissions, and employee issue reports before general noise.
- Owners can understand branch completion, quality exceptions, trial status, and policy-driven performance indicators.
- AI failure, connector failure, or media risk never silently marks unsafe evidence as successful.
- Tenant boundaries, audit integrity, recovery, and data-deletion commitments are demonstrable.

## Core Principles

- Prefer explicit, simple, code-defined behavior over dynamic engines and hidden automation.
- Keep tenant data isolated by default.
- Preserve historical facts through append-only events and versions.
- Use AI as a bounded quality aid, never an unquestionable authority.
- Make human override possible, attributable, and auditable.
- Treat media, provider endpoints, tenant credentials, and employee data as sensitive.
