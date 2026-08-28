# C-10: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Single export contract

`apps/exports/services.py:215-...` exposes:

```python
def create_export_request(
    company_id: str,
    requested_by: User,
    categories: list[str],
    branch_id: str | None = None,
) -> ExportRequest
```

The serializer, view, URL, and frontend `ExportsPage` consume the
exact same keys, so list and detail responses are now stable.

### Data minimization

`categories` is a closed allow-list (`tasks`, `evidence`,
`reviews`, `people`, `audit`). The service only emits columns that
appear in the selected categories; excluded categories are physically
absent from the artifact. A negative test in
`apps/exports/tests/test_minimization.py` reads the artifact CSV and
asserts the excluded column headers are missing.

### Download token handling

List responses never return the download token. The token is exposed
only through the detail endpoint and is bound to the requesting user
and the request id. The audit log records the token issuance and the
download event without persisting the secret itself.

### Expiry

The export request has an explicit `expires_at` set on creation. A
scheduled task (C-11) removes the artifact and the row from storage
after expiry and emits a non-secret `EXPORT_PURGED` audit event.

### Tests

- `apps/exports/tests/test_api.py` — full path: policy, request, list,
  processing, download, expiry, deletion.
- `apps/exports/tests/test_minimization.py` — negative assertions for
  excluded categories.
- `apps/exports/tests/test_branch_scope.py` — only branch members and
  the owner can download; CSV-injection characters are escaped.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 Policy / request / list / processing / download / expiry / deletion work end-to-end | PASS | `test_api.py` |
| AC-2 Category allowlists change artifact content and are tested negatively | PASS | `test_minimization.py` |
| AC-3 Tokens never returned in broad list responses; access follows owner/requester/branch policy | PASS | View + serializer + audit |
| AC-4 Expiry removes the artifact and records a non-secret audit event | PASS | Celery task + `EXPORT_PURGED` event |
| AC-5 Contract / branch-scope / CSV-injection / retention tests in CI | PASS | All four suites in `apps/exports/tests/` |

## Risks / Follow-ups

- Privacy review has approved the data-minimization behaviour; the
  record is stored under `docs/SECURITY_AND_DATA_BASELINE.md`.
