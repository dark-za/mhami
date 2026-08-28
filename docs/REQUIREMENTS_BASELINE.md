# Requirements Baseline

## Status

Approved product baseline for planning. Values marked `inventory-dependent` are intentionally deferred until the Phase 00 server inventory.

## Tenant Lifecycle

### Registration

- A visitor can create a company without manual identity verification.
- Registration requires company name, owner name, a unique permanent company code, login credentials, and either email or phone contact information.
- The company code is a tenant identifier, not a shared secret or second authentication factor.
- Automated abuse protection is required through rate limits, CAPTCHA or honeypot controls, and platform suspension capability.
- The first registered user is the Company Owner.

### Trial, Suspension, and Deletion

- Every new company starts a 30-day trial immediately after registration.
- The Platform Administrator can extend or activate a company manually.
- Suspension blocks operational activity. The owner retains a read-only export portal for 90 days.
- After 90 days, tenant business data and media are deleted from primary storage and removed from backups through the documented backup-retention cycle, subject to legal exceptions.
- V1 has no customer payment gateway, subscription billing engine, commercial quotas, or customer-facing plan editor.

## Roles and Scope

| Role | Scope | Primary authority |
| --- | --- | --- |
| Platform Administrator | Entire platform | Tenant lifecycle, platform settings, support, safety, and operations. |
| Company Owner | One company | Company settings, owner-level policies, branches, users, AI provider settings, exports, and trial visibility. |
| Quality Monitor | Assigned branches | Tasks, schedules, review, task reassignment, employee management within authorized branch scope, and AI criteria. |
| Employee | One active branch | Assigned tasks, permitted branch task visibility, direct evidence capture, task transfer requests, and task-specific issue reports. |
| Platform Support Actor | Explicitly authorized company only | Support actions through an individual support account with audit attribution. |

The Company Owner, Quality Monitor, and authorized support actor can manage employee accounts only within their granted scope. Ownership recovery or ownership transfer is a documented Platform Support process in V1.

## Authentication and Accounts

- Login uses company code, login identifier, and password.
- Company code is unique and immutable after registration.
- Employees use individually assigned credentials. The owner distributes credentials and can update employee login identifiers or passwords.
- Owner recovery is a manual support process; employee recovery is owner-controlled in V1.
- Platform Administrators and Company Owners require MFA through TOTP or passkeys.
- All browser authentication uses secure cookie sessions and CSRF protection.

## Organization, Branches, and Shifts

- A company selects an industry from a controlled list with `Other`.
- A branch has a configurable timezone and a required operational-day cutoff.
- An employee has one active branch in V1.
- A transfer preserves historical records, cancels and recreates affected scheduled work, and requires monitor intervention for open work.
- Simple weekly shifts support schedule generation only. They are not attendance or payroll records.

## Tasks and Scheduling

- Task templates are versioned. Any semantic change to instructions, evidence, verification, references, challenge, checklist, or schedule creates a future-facing version.
- Cosmetic text corrections may be edited with audit history when they do not change execution or verification meaning.
- Templates may be shared, branch-specific, or branch-customized according to the task.
- Assignment may be to a named employee, a role pool, or a monitor-distributed pool, depending on the template.
- V1 schedule types are daily fixed-time, weekly fixed-time, and shift-relative.
- One-off tasks can be created only from approved templates by an owner or monitor.
- Employees must explicitly start a task before evidence capture.
- All employees in a branch can see task details and assignees. Evidence visibility is more restricted by default.
- A task transfer request normally involves the assigned employee and monitor; the monitor has recorded override authority.
- Overdue behavior is configured per template. The monitor is alerted and decides the final exception outcome.

## Evidence, Media, and Discussion

- V1 evidence types are live camera image, number, note, and confirmation, configurable per task or checklist item.
- Gallery uploads, general file inputs, video, GPS, and offline submission are excluded from V1.
- Chrome is the only supported browser family in V1.
- Images may be required per task or per checklist item, with task-specific minimum and maximum counts, references, and instructions.
- High-risk templates can require a random challenge.
- After submission, evidence cannot be replaced or deleted by the employee. New evidence is added through a retry, resubmission, or monitor instruction.
- Duplicate-risk comparison is scoped to the branch. It is a review signal, not a punishment.
- Employees can report an issue inside a task with a photo and note. The monitor can reply in a task-scoped discussion; this is not general chat.
- Accepted formats are JPEG, PNG, and WebP. Platform defaults are 10 MB maximum and 2048 px maximum image dimension.

## Face and External-AI Privacy Policy

- The camera flow instructs users to avoid capturing people.
- If a face is detected, the system keeps only a blurred derivative as the stored evidence and as the external AI input. The unblurred source is temporary and must be discarded immediately after derivative generation.
- The system does not perform facial recognition, person identification, emotion detection, or biometric profiling.

## Verification and Review

- Submitted evidence is technically validated and processed asynchronously.
- In Shadow Mode, AI emits review signals but does not determine task completion.
- An owner may enable AI-assisted auto-pass per template after reviewing human-labeled results and the threshold gate for that template risk level.
- Default minimum evidence thresholds before auto-pass eligibility are: low risk 50 human-reviewed samples, medium risk 100 samples, high risk human review until an explicit higher-risk approval exists.
- AI uncertainty, provider failure, visual-criterion risk, duplicate risk, random-challenge failure, and employee issue reports create monitor alerts.
- The monitor may approve despite an alert, retry the same task, mark it missed, or create a corrective task. Every decision has an auditable reason.
- A later review never erases the original completion, evidence, AI output, or decision. It appends a new audit decision.

## AI Provider and Connector

- Each company can choose its provider, model, endpoint configuration, and credentials through the owner-only AI settings area.
- The provider must satisfy the platform structured-output contract. Protocol-specific adapters require reviewed code, not user-uploaded code.
- A Linux Docker tenant connector is required in V1 for private, local, and customer-controlled provider connectivity.
- The connector isolates the shared platform from direct access to tenant private networks.
- The owner must explicitly accept a versioned data-transfer notice before enabling an external AI provider.
- Quality Monitors directly maintain criteria and reference media. The owner controls provider selection, keys, enablement, and auto-pass activation.
- V1 AI use is limited to evidence image verification. Future data analysis, task suggestion, and summary use cases are deferred.
- The platform records analysis count, success state, duration, estimated cost when possible, and configurable monthly limits.

## Reporting and Performance Policies

- Owner dashboard priorities: daily and branch completion, quality alerts, and trial or subscription status.
- Monitor dashboard priorities: AI alerts, overdue tasks, employee issue reports, and resubmissions.
- Productivity is based on timely completion of assigned work and task-template weights.
- Quality is based on final human outcomes and missed or late work. AI alerts alone cannot determine an employee score or restriction.
- Owner-configurable V1 policy settings are limited to task weights, employee score visibility, report restatement behavior, and predefined operational restrictions.
- Permitted automated restrictions are monitor approval before sensitive work, blocking self-claim of sensitive work, extra evidence requirements, and owner alerts. Account suspension is not an automated employee restriction.
- Every automated restriction must be overridable by a monitor with an auditable reason and a visible explanation to the employee.

## User Experience and Branding

- V1 supports Arabic and English with RTL and LTR layouts.
- A user can choose Gregorian or Hijri date display without changing stored business time.
- V1 is responsive web only, with no PWA installation or offline experience.
- Each company provides a name, logo, and three free brand colors. The system must choose safe text, borders, and status cues so color alone never communicates a critical state.
- In-app notifications cover new or transferred tasks, retry or rejection, monitor replies, monitor alerts, overdue tasks, trial notices, and suspension notices.

## Data Access and Exports

- Default evidence access: executor, authorized monitor, and owner.
- Owner can export company-wide data.
- Monitor can export only assigned-branch data.
- Platform Support can export only after explicit tenant authorization.
- Exports are generated asynchronously and may include ZIP media archives, CSV structured data, and PDF summaries.
- Private platform storage is the source of truth. Google Drive, OneDrive, customer-server archival, and other external storage destinations are deferred.
