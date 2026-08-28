# H-07: Fix 5 pytest failures

## Discovery

### Failing tests (from docs/refinement/METRICS.md)

```
1. apps/exports/tests/test_exports_api.py::test_export_request_and_download
2. apps/exports/tests/test_exports_api.py::test_monitor_can_request_export_for_assigned_branch
3. apps/tasks/tests/test_api.py::test_user_cannot_resolve_another_company_transfer
4. apps/backups/tests/test_api.py::test_backup_create_download_restore
5. apps/backups/tests/test_api.py::test_restore_rejects_default_target_and_tampered_archive
```

### Root Cause
> "test setup grants the user MONITOR role while the corresponding view requires MONITOR **and** OWNER"

### Fix (Two options)

#### Option A: Update tests to grant OWNER
```python
# Before
def test_export_request_and_download():
    membership = make_membership(role=CompanyRole.MONITOR)
    # ...

# After
def test_export_request_and_download():
    membership = make_membership(role=CompanyRole.OWNER)  # ✅
    # ...
```

#### Option B: Update views to allow MONITOR
```python
# Before
class ExportRequestView(TenantAPIView):
    def post(self, request):
        if not is_owner(request.user, company):
            raise PlatformAPIException("Owner access required.")

# After
class ExportRequestView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)  # ✅

    def post(self, request):
        # Allow monitor for branch-scoped exports
        if is_owner(request.user, company):
            pass
        elif has_branch_scope(request.user, company, branch_ids):
            pass
        else:
            raise PlatformAPIException("Insufficient permissions.")
```

### Decision Required
> **Product Owner approval is needed** on which of the two options.

### Acceptance Standards
- AC-1: All 5 tests succeed
- AC-2: No regression
- AC-3: pyproject.toml mypy passes
- AC-4: pytest --tb=short passes
