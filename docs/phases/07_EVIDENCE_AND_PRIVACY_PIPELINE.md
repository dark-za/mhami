# Phase 07: Evidence and Privacy Pipeline

## Status

Complete.

## Objective

Enable direct, private, auditable evidence collection from Chrome while enforcing media safety, non-replacement, branch-scoped duplicate risk, face protection, and task-bound discussion.

## Entry Requirements

- Phase 06 is complete and task state transitions are fully tested.
- Image-size limits, storage capacity direction, and face-derivative approach are approved.
- Chrome Android camera behavior is validated with pilot devices.

## Scope

- Implement short-lived, single-use capture sessions bound to task, user, company, and branch.
- Implement Chrome live-camera capture with no gallery/file-picker fallback.
- Implement image, number, note, and confirmation evidence items according to template/checklist policy.
- Implement private media quarantine, signature validation, image safety checks, resizing, hashing, and branch-scoped similarity risk.
- Implement face detection and blurred derivative handling: only the blurred derivative persists and can be sent to external AI.
- Implement immutable evidence submission history and retry/resubmission attachment behavior.
- Implement high-risk random challenges according to task template policy.
- Implement task issue reports and bounded task discussion with monitor replies and extra evidence.
- Implement media worker queue and health indicators.

## Explicit Exclusions

- No gallery upload, video, GPS, audio, generic file evidence, or offline capture.
- No public media links.
- No facial recognition or employee identification from imagery.
- No AI provider integration beyond interface preparation.

## Required Software and Services

- Pillow, python-magic or equivalent signature validation, image hashing, private storage abstraction, Celery media worker, and a vetted face-detection approach selected by ADR.

## Security and Data Requirements

- Raw uploads remain quarantined until validation succeeds.
- If face handling creates a derivative, delete the unblurred source immediately after processing.
- Do not log raw media, signed download URLs, upload content, credentials, or session identifiers.
- All media reads require company, branch, and role authorization.
- Capture-session reuse, expiration, and cross-user use must fail safely.

## Deliverables

- `evidence` module with models, services, APIs, private-media authorization, worker jobs, manifest, health check, and audit events.
- Chrome camera capture interface and task evidence UI.
- Duplicate-risk and face-derivative documentation.
- Media retention and deletion hooks prepared for tenant lifecycle.

## Verification

- Gallery upload attempts are rejected.
- Invalid files, oversized files, decompression bombs, expired capture sessions, reused capture sessions, and unauthorized media access fail safely.
- Face-containing images retain only their blurred derivative.
- Similar-image risk is confined to the same branch and creates a review signal rather than automatic punishment.
- Employee and monitor task discussion is scoped to the task and authorized users.
- Standard build and quality gates pass: `python -m pytest`, `python -m ruff check .`, `python -m mypy .`, `npm run lint`, `npm run build`, `npm run test`, and the OpenAPI schema is regenerated with frontend types refreshed.

## Exit Criteria

- Employees can submit required V1 evidence safely from Chrome.
- Evidence remains private, immutable, traceable, and ready for human review without AI.
- Media failures do not incorrectly complete a task.

## Stop Conditions

- A file can bypass quarantine or become publicly accessible.
- Unblurred face images persist or reach external AI.
- Evidence replacement destroys historical context.
