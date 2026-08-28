# Pilot Task Catalog

## Status

Exit dossier issued by `PILOT-ASSURANCE-02`. Reference templates are entered as `TaskTemplate` records and validated against the required fields below.

## Purpose

Capture the actual operational standards required to configure initial task templates.

## Required Fields Per Template

- **Identity.** Template name, industry, branch applicability (which of the three pilot branches), and job role or assignee policy (who may claim/execute).
- **Schedule.** Daily, weekly, or shift-relative schedule and grace policy (late/early tolerance before an instance is flagged).
- **Work definition.** Checklist items and step-by-step instructions for the worker.
- **Evidence capture.** Required images, numbers, notes, and confirmations per checklist item.
- **Media policy.** Minimum and maximum images, reference media (golden examples), random challenge policy (probability a step is randomly re-verified), and risk level (low / medium / high).
- **Outcomes.** What constitutes completion, alert, retry, missed work, and corrective work, plus the state-machine transitions they trigger.
- **Quality control.** Quality Monitor verification criteria and the source SOP the template encodes.
- **Weighting.** Template weight and permitted performance-policy impact (whether and how the template may influence a worker's performance standing).

## Approved Initial Reference Templates

- **Shift cash handover documentation without accounting reconciliation.** A closing-shift handover template capturing till/cash drawer counts and seal evidence; explicitly excludes accounting reconciliation (finance tasks are out of pilot scope). Risk: medium. Minimal image set (till, sealed bag) with a random-challenge re-verification step.
- **Critical cleanliness and preparation-area inspection.** A mid-day and pre-service inspection of food-prep surfaces, sanitizer levels, and storage. Risk: high. Larger minimum image set with reference media and mandatory monitor confirmation on failure.
- **Shift close and handover documentation.** An end-of-shift closeout capturing station cleanliness, equipment-off evidence, and open-task handover notes to the next shift lead. Risk: medium. Includes a transfer scenario for unresolved tasks.
