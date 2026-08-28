# BE-04: Audit Chain Review

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The audit chain is a critical control: every `AuditEvent` carries `previous_hash` and a signature. The H-08 fix added a `select_for_update` + advisory lock to serialise writers. The chain must be reviewed for:

- `previous_hash` keyed on the **id** of the prior event (not timestamp).
- `verify_integrity` walks the full chain.
- No `update` on `AuditEvent` outside a transaction.
- `delete` is blocked.

**Evidence gathered:**

```bash
# 1. Find every place that writes to AuditEvent
Get-ChildItem backend/apps -Recurse -Filter "*.py" | ForEach-Object {
  Select-String $_ -Pattern "AuditEvent\.objects\.create|AuditEvent\.objects\.update"
} | Measure-Object | Select-Object -ExpandProperty Count

# 2. Find AuditEvent delete
Get-ChildItem backend/apps -Recurse -Filter "*.py" | ForEach-Object {
  Select-String $_ -Pattern "AuditEvent\.objects\.delete|\.delete\(\)"
}
```

### Impact

| Dimension | Impact |
|---|---|
| Security | A tampered audit row breaks the chain; the chain must be tamper-evident. |
| Compliance | PDPL requires an immutable, verifiable record of processing. |
| Operational | A bug in `verify_integrity` could mask tampering. |

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `previous_hash` keyed on id | yes (H-08) | unchanged |
| `verify_integrity` walks full chain | yes | unchanged |
| No `update` outside transaction | partial | enforced |
| No `delete` | partial | enforced |
| Race-condition test (H-08) | yes | unchanged |

---

## 3. Goal Statement

> Within **3 days**, audit the chain end-to-end and enforce: (a) `AuditEvent.save()` always opens a transaction; (b) `AuditEvent.delete()` is forbidden; (c) `verify_integrity` runs in the release smoke test.

### Acceptance Criteria

1. **AC-1:** `AuditEvent.save()` calls `transaction.atomic()` (or is always called from within one).
2. **AC-2:** `AuditEvent.delete()` raises `PermissionError`.
3. **AC-3:** `verify_integrity()` returns the first tampered row's id and index.
4. **AC-4:** A test mutates an `AuditEvent` row's `payload` and asserts `verify_integrity()` reports it.
5. **AC-5:** The release smoke (QA-01) calls `verify_integrity()` and exits non-zero on any gap.
6. **AC-6:** H-08's `test_concurrent_writers_do_not_collide_on_previous_hash` still passes.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A legitimate `update` on `AuditEvent` (e.g. cascade) is needed | Low | High | Use `signal` instead of `save()`; document |
| `verify_integrity` is too slow on a large chain | Medium | Medium | Run it nightly, not on every API call |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Audit every `AuditEvent.objects.update/delete` call | Backend | not-started |
| 2 | Override `AuditEvent.save()` to wrap in transaction (if not already) | Backend | not-started |
| 3 | Override `AuditEvent.delete()` to raise | Backend | not-started |
| 4 | Add tamper test | Backend | not-started |
| 5 | Add `verify_integrity` to release smoke | QA Lead | not-started |
| 6 | Update `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [upgrads/02_HIGH_PRIORITY/H-08_AUDIT_RACE_CONDITION](../../02_HIGH_PRIORITY/H-08_AUDIT_RACE_CONDITION/00_DISCOVERY.md)
- [upgrads/06_QUALITY_ASSURANCE/QA-01_TEST_LAYERS](../06_QUALITY_ASSURANCE/QA-01_TEST_LAYERS/00_DISCOVERY.md) — release smoke
- [docs/SECURITY_AND_DATA_BASELINE.md](../../../docs/SECURITY_AND_DATA_BASELINE.md) — PDPL audit requirements
