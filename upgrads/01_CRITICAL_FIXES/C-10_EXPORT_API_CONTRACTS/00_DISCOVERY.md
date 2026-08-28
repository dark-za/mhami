# C-10: Repair Export Contracts and Data Minimization

## Discovery

Export endpoints, service signatures, URLs, and frontend assumptions diverge:

- `backend/apps/exports/api/views.py:20-66`
- `frontend/src/pages/shared/ExportsPage.tsx`

The list key, policy method, request payload, and download parameter do not
match. Requested categories are stored but do not limit artifact content, and
list responses expose download tokens too broadly.

## Goal

Provide a tested export workflow that returns only requested and authorized data
and has one generated API contract.

## Acceptance Criteria

1. Policy, request, list, processing, download, expiry, and physical deletion
   work through the browser and public API contract.
2. Category allowlists change artifact content and are tested with negative
   assertions for excluded data.
3. Tokens are never returned in broad list responses or audit metadata; access
   follows owner/requester/branch policy.
4. Expiry removes the artifact from storage and records a non-secret audit
   event.
5. Contract, branch-scope, CSV-injection, and retention tests run in CI.

## Required Evidence

- Generated-client contract test output.
- Artifact content manifest and deletion proof.
- Privacy reviewer approval for minimization behavior.
