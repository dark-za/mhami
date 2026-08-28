# C-07: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Code-level branch scope enforcement

`backend/apps/evidence/api/views.py` enforces a uniform branch-scope
check before every evidence, issue, message, capture-session, and media
operation. Each affected path now calls
`context.require_branch(...)` immediately after the company and
branch-level objects are loaded:

```python
# C-07: branch scope check. A user with branch-level access can
# only see workflows for branches in their active scope.
context.require_branch(task.branch_id)
```

The helper itself lives in `apps/tenancy/access.py` and raises
`PlatformPermissionException` (HTTP 403) on mismatch, so cross-branch
probes do not learn whether the workflow exists in another branch.

### Workflow consistency

`EvidenceTaskView`, issue creation, and message creation all run
through the same gate. Issue creation additionally requires the
referenced `TaskInstance` and any reply target to live in the same
branch. This is enforced inside the serializer with the standard
`validate_company_reference` helper from BE-02.

### Tests

`backend/apps/evidence/tests/` contains PostgreSQL-bound tests that:

- Submit a request as a branch-A employee to a branch-B task and assert
  a 403 response.
- Submit a message with a `parent_message_id` from a different branch
  and assert the same 403.
- Submit a capture session upload with the wrong branch and assert the
  same 403.
- Verify that an Owner can still access the audit trail cross-branch
  via the documented override (the override is itself a recorded audit
  event).

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 Common branch-scope check before every read/mutation | PASS | `context.require_branch` in every relevant view |
| AC-2 Issue / task / reply references in same company+branch | PASS | Serializer + view checks |
| AC-3 Cross-branch GET/POST rejected for employee & monitor | PASS | Evidence tests |
| AC-4 Owner/support access policy documented and tested | PASS | Audit log override path |
| AC-5 PostgreSQL API tests cover all paths | PASS | `evidence/tests/` |

## Risks / Follow-ups

- The threat model in `docs/SECURITY_THREAT_MODEL.md` is updated to
  call out branch-scope as a hard isolation boundary, not just a
  recommendation.
