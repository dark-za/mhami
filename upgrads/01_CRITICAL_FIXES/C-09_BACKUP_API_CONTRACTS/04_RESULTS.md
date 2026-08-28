# C-09: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Unified service signature

`apps/backups/services.py` now exposes a stable set of entry points
with explicit parameters and a single return contract:

```python
def create_backup_run(
    company_id: str,
    requested_by: User,
    policy: BackupPolicy,
) -> BackupRun
```

View, serializer, and OpenAPI definitions in `apps/backups/api/` call
this signature with the same parameter names, eliminating the prior
divergence between views, services, and the generated TypeScript
client.

### Authorization

The Owner-only policy is enforced inside `BackupPolicyView` and the
`create_backup_run` service. Monitors can list backup metadata but
never receive a complete archive. Downloads require an explicit
download token that is bound to the requesting user and a single run
id; the token is consumed on first successful download.

### Contract tests

`apps/backups/tests/test_api.py` exercises:

- Policy create / read / update with the public URL.
- Backup run create / list / status.
- Download with a valid token; missing / expired / mismatched tokens
  are rejected.
- Tamper rejection: flipping a single byte in the archive fails the
  integrity check.
- Restore: when a backup and the matching restore policy are
  available, the run is executed by the worker and a status event is
  recorded.

All tests run against PostgreSQL with a real worker process so the
contract covers the actual end-to-end behaviour, not just the unit
boundary.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 OpenAPI / serializers / views / services / frontend share the same contract | PASS | `services.create_backup_run(...)` signature + generated client verification |
| AC-2 Owner-only policy decided and enforced consistently | PASS | `BackupPolicyView` + service authorization |
| AC-3 API tests cover policy / create / list / download / tamper / restore | PASS | `test_api.py` |
| AC-4 Contract tests fail on argument / response-key / status-code / schema drift | PASS | `test_api.py` + OpenAPI schema diff |
| AC-5 No test weakened by changing a role | PASS | Authorization matrix in `apps/backups/AUTHORIZATION.md` |

## Risks / Follow-ups

- H-05 (Fernet encryption) and H-06 (PostgreSQL restore) extend this
  contract; their results feed back here.
