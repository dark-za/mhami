# Section 2: High Priority Fixes

> **The 8 high-priority fixes** identified in the hostile Audit.
> Each fix has a sub-folder with up to 5 documents (00_DISCOVERY.md, 01_VERIFICATION.md, 02_GOAL.md, 03_IMPLEMENTATION.md, 04_TESTING.md, 04_RESULTS.md).

## List of Fixes

| # | Title | Folder | Priority | Estimated Duration |
|---|---|---|---|---|
| H-01 | ReviewDecisionCreateView without required_roles | `H-01_REVIEW_DECISION_RBAC/` | P1 | 1 day |
| H-02 | ReviewPolicyView.patch without required_roles | `H-02_REVIEW_POLICY_RBAC/` | P1 | 1 day |
| H-03 | Implement real OpenAI Provider | `H-03_REAL_AI_PROVIDER/` | P1 | 1 week |
| H-04 | Implement Linux Docker connector | `H-04_LINUX_CONNECTOR/` | P0 | 2 weeks |
| H-05 | Implement Fernet encryption for backups | `H-05_BACKUP_ENCRYPTION/` | P1 | 1 week |
| H-06 | Backup restore to PostgreSQL | `H-06_BACKUP_POSTGRES_RESTORE/` | P1 | 1 week |
| H-07 | Fix 5 pytest failures | `H-07_TEST_FAILURES/` | P0 | 3 days |
| H-08 | Fix race in Audit chain | `H-08_AUDIT_RACE_CONDITION/` | P1 | 2 days |

## H-07: Fix 5 pytest failures (Quick Detail)

**Failed files (from docs/refinement/METRICS.md):**
- `apps/exports/tests/test_exports_api.py::test_export_request_and_download`
- `apps/exports/tests/test_exports_api.py::test_monitor_can_request_export_for_assigned_branch`
- `apps/tasks/tests/test_api.py::test_user_cannot_resolve_another_company_transfer`
- `apps/backups/tests/test_api.py::test_backup_create_download_restore`
- `apps/backups/tests/test_api.py::test_restore_rejects_default_target_and_tampered_archive`

**Initial hypothesis only:** Some tests grant MONITOR while views require OWNER.
This must not be treated as the root cause until API/service signatures, URLs,
serialization, and the approved product authorization matrix have been tested.

**Proposed Fix:**
1. Reproduce each failure through the public endpoint and identify its actual contract failure.
2. Record the approved authorization matrix with Product Owner and Security.
3. Update production code or tests only after the matrix and contract are proven.

**Requirement:** Do not weaken tests by changing a role merely to make CI green.

## H-08: Fix race in Audit chain (Quick Detail)

**Problem:** `apps/audit/models.py:76`:
```python
previous_query = type(self).objects.order_by("-timestamp", "-id")
if not connection.get_autocommit():
    previous_query = previous_query.select_for_update()
previous = previous_query.first()
```

**Problem:** If two events are inserted in the same microsecond (with autocommit=True), `select_for_update` is not applied.

**Fix:**
1. Add a `BigAutoField` monotonic sequence as an alternative `id`.
2. or Use `select_for_update(nowait=False, skip_locked=False)` outside transaction.
3. or Add `created_at` to `auto_now_add=True` and order by it.

**Rejected as insufficient:** A `BigAutoField` or ordering by a new timestamp
does not serialize the empty-chain case and may break UUID references.

**Required design direction:**
1. Keep the existing event primary key unless a separately reviewed migration proves compatibility.
2. Lock a singleton `AuditChainHead` for the relevant scope, or use a PostgreSQL advisory transaction lock.
3. Insert the event and update the head in the same transaction.
4. Verify with independent PostgreSQL connections and 100+ concurrent writes.
```python
class AuditEvent(models.Model):
    id = models.BigAutoField(primary_key=True)  # monotonic
    # ...

    def save(self, *args, **kwargs):
        with transaction.atomic():
            previous = type(self).objects.select_for_update().order_by("-id").first()
            # id-based ordering
            self.previous_hash = previous.event_hash if previous else ""
            # ...
```
