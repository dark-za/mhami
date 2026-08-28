# H-08: Fix race condition in Audit chain

## Discovery

### Problem
`apps/audit/models.py:73-87`:
```python
def save(self, *args, **kwargs):
    if not self._state.adding:
        raise ValidationError("Audit events are append-only")
    if self.timestamp is None:
        self.timestamp = timezone.now()
    previous_query = type(self).objects.order_by("-timestamp", "-id")
    if not connection.get_autocommit():
        previous_query = previous_query.select_for_update()
    previous = previous_query.first()
    self.previous_hash = previous.event_hash if previous else ""
    # ...
```

### Scenario
- In autocommit mode (outside transaction):
  - `select_for_update` is not applied
  - If two events are inserted in the same microsecond, both get the same `previous_hash`
  - **Chain integrity is lost**

### Fix

**File:** `apps/audit/models.py`

```python
class AuditEvent(models.Model):
    # ✅ BigAutoField for deterministic ordering
    id = models.BigAutoField(primary_key=True)
    # or UUID but with sequence:
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    # event_sequence = models.BigIntegerField(unique=True)  # ✅ new

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Audit events are append-only")

        with transaction.atomic():
            # ✅ Use sequence-based ordering
            previous = (
                type(self).objects
                .select_for_update()
                .order_by("-id")
                .first()
            )
            self.previous_hash = previous.event_hash if previous else ""

            if self.timestamp is None:
                self.timestamp = timezone.now()

            self.event_hash = calculate_event_hash(self, self.previous_hash)
            self.integrity_hmac = calculate_event_hmac(self.event_hash)

            super().save(*args, **kwargs)
```

### Test

```python
def test_audit_chain_no_race_in_concurrent_inserts():
    """Two concurrent inserts must not produce same previous_hash."""
    import threading

    results = []
    def insert():
        event = AuditEvent.objects.create(
            event_type="TEST",
            target_type="x",
            target_id="1",
            actor_id="a",
            metadata={},
        )
        results.append(event.previous_hash)

    threads = [threading.Thread(target=insert) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All previous_hash values should be different (or empty for first)
    unique_hashes = set(h for h in results if h)
    assert len(unique_hashes) >= 9  # 9 out of 10 should be unique
```

### Acceptance Standards
- AC-1: concurrent inserts do not cause same previous_hash
- AC-2: select_for_update works in all states
- AC-3: chain verification passes
- AC-4: performance test (1000 inserts) < 5s
