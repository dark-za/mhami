# Phase 09: AI Gateway and Tenant Connector

## Status

Complete.

## Objective

Add optional, tenant-controlled evidence-image verification without binding the platform to one provider or allowing unsafe direct access to tenant private networks.

## Entry Requirements

- Phase 08 is complete and the product is operationally useful without AI.
- Pilot company provides criteria, reference material, provider choice, endpoint details, and owner-approved AI data-transfer acceptance.
- Connector threat model, enrollment flow, Docker Linux support matrix, and structured-output contract are approved.

## Scope

- Implement the provider interface and structured JSON result validation.
- Implement owner-only AI provider configuration, credentials, model selection, usage metrics, estimated cost where available, and monthly limits.
- Implement quality-monitor management of versioned criteria and reference media.
- Implement AI analysis records, prompt versions, retries, timeouts, idempotency, and AI queue isolation.
- Implement tenant connector enrollment, mutual authentication or equivalent secure channel, version compatibility, health, revocation, and job dispatch.
- Implement Shadow Mode, comparison against human decisions, threshold tracking by risk level, and owner-controlled auto-pass activation per template.
- Route provider failures, uncertain outputs, visual-risk findings, duplicate risk, and challenge failure to monitor alerts.

## Explicit Exclusions

- No arbitrary executable AI plugins or model binaries uploaded through the UI.
- No direct unrestricted network calls from shared SaaS workers to tenant private addresses.
- No AI-driven disciplinary action or automatic employment account suspension.
- No generic data analysis, predictive AI, task recommendation, or free-form chat in V1.

## Required Software and Services

- `ai_gateway` and `connector_control` modules.
- Dedicated Celery AI worker queue.
- Tenant Connector built and distributed as a Linux Docker workload.
- Provider contract test harness and fake provider for automated tests.

## Security and Data Requirements

- Only blurred face derivatives may leave the platform for AI analysis.
- Provider keys remain encrypted and unavailable to browser code.
- Connector privileges are limited to configured provider operations and authenticated platform jobs.
- Every provider change, criteria change, connector event, analysis run, and auto-pass enablement is audited.
- Semantic criteria changes create future-facing versions.

## Deliverables

- AI provider contract and fake provider.
- Tenant connector contract, enrollment lifecycle, health view, and Docker Linux deployment guide.
- Provider configuration UI for owners and criteria UI for monitors.
- Shadow Mode dashboards and agreement metrics.
- Auto-pass eligibility gate implementation.

## Verification

- Invalid provider JSON, timeouts, 429s, 5xx responses, connector outage, and invalid criteria all route safely to review.
- A private provider can be reached only through the authenticated tenant connector.
- AI output cannot bypass human and policy gates.
- Auto-pass cannot be enabled below the approved risk threshold.
- Unit tests do not call live providers; staging contract tests use a controlled dataset.

## Exit Criteria

- The pilot company can run AI Shadow Mode through its selected provider safely.
- Provider or connector failure never blocks evidence submission or silently passes evidence.
- AI behavior is traceable, comparable to human judgment, and reversible by feature flag.

## Stop Conditions

- Shared platform workers can reach arbitrary tenant private network targets.
- AI results are accepted without schema validation.
- A provider failure incorrectly completes a task.
