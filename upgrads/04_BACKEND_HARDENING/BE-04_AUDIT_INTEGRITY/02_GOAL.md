# BE-04: Goal and Plan

## SMART Goal

> Within **3 days**, audit the chain end-to-end and enforce:
> (a) `AuditEvent.save()` opens a transaction;
> (b) `AuditEvent.delete()` raises;
> (c) `verify_integrity()` is exercised in the release smoke;
> (d) a tamper test exists and passes.

## Acceptance Standards

### Standard 1: `save()` wraps in transaction

```python
# apps/audit/models.py
class AuditEvent(models.Model):
    # ...
    def save(self, *args, **kwargs):
        from django.db import transaction
        with transaction.atomic():
            super().save(*args, **kwargs)
```

### Standard 2: `delete()` is forbidden

```python
def delete(self, *args, **kwargs):
    raise PermissionError("AuditEvent is append-only")
```

### Standard 3: `verify_integrity()` is callable

```python
def verify_chain():
    """Return (ok: bool, first_bad_id: int|None)."""
```

### Standard 4: Tamper test

```python
def test_verify_chain_detects_tampered_row():
    e1 = AuditEvent.objects.create(event="a")
    e2 = AuditEvent.objects.create(event="b")
    e2.payload = '{"tampered": true}'  # not via .objects.update
    e2.save()  # bypasses our atomic wrapper, but verify_chain recomputes
    ok, bad_id = verify_chain()
    assert not ok
    assert bad_id == e2.id
```

### Standard 5: Release smoke

The release smoke (`backend/tests/test_release_smoke.py`, added in QA-01) calls `verify_chain()` and exits non-zero on any gap.

---

## Implementation Plan

### Day 1 — Audit

- [ ] Inventory every `AuditEvent.objects.create/update/delete`.
- [ ] Confirm H-08's `save()` is in place.

### Day 2 — Enforce

- [ ] Add `delete()` override.
- [ ] Confirm `save()` is atomic.

### Day 3 — Tests

- [ ] Add tamper test.
- [ ] Update release smoke to call `verify_chain()`.

---

## Checkpoints

| CP | Condition |
|---|---|
| CP-1 | `delete()` raises |
| CP-2 | tamper test passes |
| CP-3 | release smoke green |
| CP-4 | H-08 still passes |

---

## Cancellation Criteria

- A legitimate `delete()` is needed → use a soft-delete flag instead; do not permit hard delete.
