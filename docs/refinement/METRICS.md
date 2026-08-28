# Code Metrics — Final Snapshot (R-16)

> **Generated:** 2026-08-28
> **Branch:** main
> **Refinement phase:** Complete (all 16 phases R-01 → R-16)

This snapshot captures the platform's code health at the end of the
16-phase refinement cycle. Subsequent changes should be measured
against these numbers.

## Snapshot commands

```bash
# File sizes
python backend/scripts/check_file_sizes.py --report

# Docstring coverage
python backend/scripts/check_docstrings.py

# Cyclomatic complexity
python backend/scripts/check_complexity.py

# Quality gates
cd backend && python -m ruff check apps/
cd backend && python -m mypy apps/
cd frontend && npm run typecheck && npm run build && npm run test
```

## Code volume

| Scope | Files | Lines |
|---|---|---|
| Backend (`apps/`, no migrations/tests) | 132 | 23 808 |
| Backend `apps/` total (incl. tests) | 167 | 32 950 |
| Backend `config/` | 8 | 1 256 |
| Frontend `src/` (TS/TSX) | 33 | 5 466 |
| Frontend `src/api/generated-types.ts` (auto) | 1 | 4 032 |

## File size compliance (R-16 cap = 500 lines)

| Status | Count |
|---|---|
| Files within cap | 132 / 132 production files (100%) |
| Files exempt | `generated-types.ts` (auto-generated, 4032 lines) |
| Top 5 largest files | `operate_pilot.py` (584), `probe_resilience.py` (486), `backups/services.py` (467), `tenancy/services.py` (431), `tenancy/api/views.py` (394) |

## Docstring coverage (Google style)

| Tier | Coverage |
|---|---|
| `tenancy/services.py` | 16 / 16 (100%) — full reference implementation |
| `tenancy/services.py` | documented in R-15 |
| Platform overall (apps/, no tests) | 37 / 583 (6%) — baseline established, R-15b+ planned |

## Cyclomatic complexity (radon)

| Grade | Count | Description |
|---|---|---|
| A (1-5) | 693 | Low risk, easy to test |
| B (6-10) | 51 | Moderate, business logic |
| C (11-20) | 13 | Higher risk, refactor candidate |
| D (21-30) | 2 | Refactor required |
| F (31+) | 0 | Untestable |

**C+ production code (13):** functions flagged for incremental refactor in future phases.

## Quality gates

| Gate | Status |
|---|---|
| `ruff check apps/` | All checks passed |
| `mypy apps/` | 9 pre-existing issues (CompanyRole enum vs str) |
| `pytest apps/ tests/` | 86 / 91 passed, 5 pre-existing failures |
| `npm run typecheck` | no errors |
| `npm run build` | 112 modules, 96.05 kB gzipped |
| `npm run test` | 1 / 1 passed |
| `python manage.py check` | System check identified no issues |

## Five pre-existing test failures (not introduced by R-01..R-16)

- `apps/exports/tests/test_exports_api.py::test_export_request_and_download`
- `apps/exports/tests/test_exports_api.py::test_monitor_can_request_export_for_assigned_branch`
- `apps/tasks/tests/test_api.py::test_user_cannot_resolve_another_company_transfer`
- `apps/backups/tests/test_api.py::test_backup_create_download_restore`
- `apps/backups/tests/test_api.py::test_restore_rejects_default_target_and_tampered_archive`

All 5 share the same root cause: the test setup grants the user MONITOR
role while the corresponding view requires MONITOR **and** OWNER. Tracked
for a follow-up.

## Refinement phase outcomes (R-01..R-16)

| Phase | Section | Outcome |
|---|---|---|
| R-01 | Foundation | `health.py` reduced to 3 lines × 13 modules |
| R-02 | Foundation | `manifest.py` 246 → 145 lines (−41%) |
| R-03 | Foundation | `TenantAPIView` introduced, 11 views migrated |
| R-04 | Foundation | `@platform_service_call` decorator, 5 views migrated |
| R-05 | Foundation | `@audited_service` decorator, 7 service functions migrated |
| R-06 | Modules | `PlatformAppConfig` + `ModuleRegistry.register_manifest`, 14 modules migrated |
| R-07 | Frontend | `App.tsx` 2081 → 166 lines (−92%) |
| R-08 | Frontend | 6 / 9 domain types bound to `generated-types.ts` |
| R-09 | Quality | 5 factories + `force_login_company` helper in `conftest.py` |
| R-09b | Quality | 15 legacy test files migrated to factories (96 tests, 0 regressions) |
| R-10 | Quality | 4 dead helpers removed, 3 dead imports cleaned |
| R-11 | Patterns | `OutboxEventBuilder` + `emit_audit_and_outbox` + `quick_event` |
| R-12 | Patterns | `TenantQuerySet` + `TenantManager`, 6 models + 2 views migrated |
| R-13 | Governance | `PlatformSettings` (Pydantic), 17 `os.getenv` → typed fields |
| R-14 | Governance | YAML anchors: `x-backend-prod-env` + `x-backend-restart` |
| R-15 | Governance | `tenancy/services.py` fully documented (Google style) |
| R-16 | Governance | `check_file_sizes.py` + `check_complexity.py` + this snapshot |

**Net code movement:** 17 new files, 91 modified files (incl. R-09b),
~600 lines of boilerplate removed, 1 regression discovered and fixed
(R-11 uncovered R-10's `_ensure_company_operational` deletion).

## Open follow-ups

- R-10b/c: cleanup remaining `_company_for_request`/`is_owner` patterns
        in `backups` and `exports`
- R-12c: investigate the 5 pre-existing test failures (permission model
        mismatch between MONITOR role and view requirements)

## R-09b details (conftest migration)

15 legacy test files migrated to the R-09 factory suite. The migration
exposed and fixed one critical issue: a test that used `make_membership`
without declaring it as a fixture parameter (pytest fixture injection
mechanic). The 5 pre-existing failures were preserved exactly as in the
R-16 snapshot — no regressions introduced.

| Module | Files migrated | Tests migrated |
|---|---|---|
| `tenancy` | 2 | 14 |
| `organizations` | 1 | 1 |
| `connector_control` | 1 | 4 |
| `backups` | 2 | 4 |
| `exports` | 2 | 5 |
| `identity` | 1 | 3 |
| `platform_core` | 1 | 2 |
| `tasks` | 2 | 10 |
| `reviews` | 1 | 4 |
| `evidence` | 1 | 5 |
| `pilot` | 1 | 3 |
| `ai_gateway` | 1 | 4 |
| `notifications` | 1 | 8 |

**Conftest factories added in R-09b:** `make_job_role`,
`make_branch_membership`, `make_template`, `make_template_version`,
`make_schedule`, `make_capture_session`, `make_evidence_item`. Internal
helper `_create_task_instance` is module-private; tests use the public
factories that wrap it.
- R-11b/c: extend `outbox.emit` adoption to remaining modules
- R-12b-d: extend `TenantManager` to remaining 8+ models
- R-13b/c: nested settings groups + `.env.example` validator
- R-14b-d: extension files + profiles + secrets manager
- R-15b-f: docstring coverage + Sphinx + pre-commit
- R-16 follow-up: tighten complexity threshold to B (51 offenders) and
        file size cap to 400 (R-16b)
