# C-09: Repair Backup API Contracts and Authorization

## Discovery

Backup views and services have divergent signatures and fields:

- `backend/apps/backups/api/views.py:54-105`
- `backend/apps/backups/services.py:284-304`
- `backend/apps/backups/services.py:405-411`

The current API passes `requested_by` and `payload` where services require
explicit parameters, orders by a missing field, and uses role literals that do
not match the model values.

## Goal

Restore a single explicit contract for backup policy, create, list, download,
and restore before adding encryption or PostgreSQL recovery features.

## Acceptance Criteria

1. OpenAPI, serializers, URLs, views, services, and frontend client describe
   identical request and response contracts.
2. Owner-only policy is decided by product and enforced consistently; monitors
   never receive a complete archive unless an approved requirement permits it.
3. API tests execute policy, create, list, download, tamper rejection, and
   restore through public URLs against PostgreSQL and a worker.
4. Contract tests fail on an argument, response-key, status-code, or schema
   drift.
5. No test is weakened by changing a role until the approved authorization
   matrix is recorded.

## Required Evidence

- Before/after failing request output.
- OpenAPI diff and generated-client verification.
- QA and Security approval.
