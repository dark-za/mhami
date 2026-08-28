# Domain Model Baseline

## Tenant and Identity

- `Company`: tenant boundary, company code, industry, branding, status, trial dates, legal acceptances, and support authorization.
- `User`: individual authenticated actor with stable UUID, login identifier, display name, MFA state, and activity state.
- `CompanyMembership`: relates a user to a company role and defines active status.
- `Branch`: company location, timezone, required operational-day cutoff, active state, and branch configuration.
- `UserBranchMembership`: one active employee branch in V1, historical membership dates, branch-scoped monitor access, and job role.
- `JobRole`: company-defined operational role used by templates and reporting.
- `WeeklyShift`: simple recurring employee shift used only to generate shift-relative tasks.

## Task Execution

- `TaskTemplate`: reusable business definition.
- `TaskTemplateVersion`: immutable execution and verification standard for historical tasks.
- `TaskSchedule`: daily, weekly, or shift-relative recurrence and assignment policy.
- `TaskInstance`: actual scheduled or one-off work item.
- `TaskStatusEvent`: append-only state transition history.
- `TaskTransferRequest`: employee request and monitor decision for task reassignment.
- `TaskIssue`: employee-reported obstacle or concern tied to a task.
- `TaskDiscussionMessage`: bounded task-specific communication and evidence references.
- `CorrectiveTask`: a future corrective work item created by monitor decision.

## Evidence and Media

- `CaptureSession`: short-lived, single-use live-camera authorization.
- `EvidenceSubmission`: immutable submitted evidence set for a task instance.
- `EvidenceItem`: image, number, note, or confirmation item tied to a task or checklist item.
- `MediaAsset`: quarantined, validated, private stored derivative with hash and duplicate-risk metadata.
- `FaceDerivative`: blurred stored derivative when a source image contains a face; the unblurred source is transient only.
- `DuplicateRisk`: branch-scoped duplicate or similarity assessment.

## Review, AI, and Policy

- `ReviewDecision`: append-only monitor decision and reason.
- `AIProviderConfiguration`: owner-controlled tenant provider configuration and data-transfer acceptance.
- `AIAnalysisRun`: provider, model, prompt version, result, latency, usage, cost estimate, and outcome.
- `VerificationCriteriaVersion`: monitor-controlled criteria and reference-media version associated with a template version.
- `ConnectorRegistration`: tenant connector identity, version, health, and compatibility.
- `PerformancePolicy`: limited owner-configurable weights, display choices, restatement behavior, and allowed restriction rules.
- `PerformanceRestriction`: policy-triggered operational restriction with monitor override history.

## SaaS, Audit, and Export

- `TrialStatus`: trial, active, suspended, read-only export window, pending deletion, or deleted state.
- `LegalAcceptance`: versioned owner acceptance and employee acknowledgement records.
- `SupportAuthorization`: revocable company grant for named platform support actors.
- `AuditEvent`: append-only business and security history with integrity metadata.
- `OutboxEvent`: transactionally persisted asynchronous domain event.
- `ExportJob`: authorized asynchronous ZIP, CSV, or PDF export request and temporary delivery record.

## Core Task States

The implementation phase must finalize a transition table, but the baseline states are:

```text
SCHEDULED
AVAILABLE
IN_PROGRESS
PROOF_SUBMITTED
VALIDATING
AI_PROCESSING
NEEDS_REVIEW
COMPLETED
RETRY_REQUIRED
MISSED
CANCELLED
```

Historical completion must never be overwritten. A later review creates an additional decision and may change current reporting according to company policy.
