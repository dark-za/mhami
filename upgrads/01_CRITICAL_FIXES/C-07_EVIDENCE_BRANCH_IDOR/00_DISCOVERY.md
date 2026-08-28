# C-07: Enforce Evidence Branch Isolation

## Discovery

`EvidenceTaskView`, issue creation, and issue messages scope targets to the
company but do not consistently require access to the target branch:

- `backend/apps/evidence/api/views.py:72-90`
- `backend/apps/evidence/api/views.py:104-138`

An employee in branch A can read or mutate evidence workflow metadata for a
known task or issue UUID in branch B of the same company. Message creation also
needs to prove that the supplied task, issue, and optional reply belong to the
same branch-scoped workflow.

## Goal

Before any pilot or external-data processing, enforce authorization before
every evidence read or mutation and return an indistinguishable 403/404 for
out-of-scope branch targets.

## Acceptance Criteria

1. Every task, issue, message, capture session, and media path calls a common
   branch-scope check before serialization or mutation.
2. Issue, task, and reply references must belong to the same company, branch,
   and workflow relationship.
3. Cross-branch GET and POST attempts fail for employee and monitor accounts.
4. Owner/support access follows an explicit documented policy and is tested.
5. PostgreSQL API tests cover evidence details, issue creation, messages,
   sessions, media, and UUID enumeration behavior.

## Required Evidence

- Commit SHA and CI URL.
- Cross-branch negative-test output on PostgreSQL.
- Security reviewer approval and updated threat-model reference.
