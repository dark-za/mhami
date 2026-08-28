# BE-04: Implementation Guide

## Step 1: Audit

```bash
Get-ChildItem backend/apps -Recurse -Filter "*.py" | ForEach-Object {
  Select-String $_ -Pattern "AuditEvent\.objects\.(create|update|delete)"
} | Select-Object Path, LineNumber, Line
# Inventory the writers; document any that bypass save()
```

## Step 2: `delete()` override

### 2.1 File: `backend/apps/audit/models.py`

```python
class AuditEvent(models.Model):
    # ... existing fields ...

    def delete(self, *args, **kwargs):
        raise PermissionError("AuditEvent is append-only")

    def save(self, *args, **kwargs):
        from django.db import transaction
        with transaction.atomic():
            super().save(*args, **kwargs)
```

**Verify:**
```bash
cd backend
python -c "
import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'
import django; django.setup()
from apps.audit.models import AuditEvent
from apps.identity.models import User
u = User.objects.first()
e = AuditEvent.objects.create(event='test', actor=u)
try:
    e.delete()
    print('UNEXPECTED: no error')
except PermissionError as exc:
    print('OK:', exc)
"
# Expected: "OK: AuditEvent is append-only"
```

## Step 3: `verify_chain()`

### 3.1 File: `backend/apps/audit/services.py`

```python
"""Audit chain verification.

Returns (ok: bool, first_bad_id: int|None).
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional, Tuple

from .models import AuditEvent


def _hash(event: AuditEvent) -> str:
    payload = json.dumps({
        "id": str(event.id),
        "event": event.event,
        "actor_id": str(event.actor_id) if event.actor_id else None,
        "context": event.context,
        "created_at": event.created_at.isoformat(),
    }, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_chain() -> Tuple[bool, Optional[int]]:
    prev_hash = "0" * 64
    for i, event in enumerate(AuditEvent.objects.order_by("id")):
        if event.previous_hash != prev_hash:
            return False, event.id
        prev_hash = _hash(event)
    return True, None
```

## Step 4: Tamper test

### 4.1 New file: `backend/apps/audit/tests/test_audit_chain_tamper.py`

```python
"""Tamper detection on the audit chain."""
from __future__ import annotations

import pytest

from apps.audit.models import AuditEvent
from apps.audit.services import verify_chain

pytestmark = pytest.mark.django_db


def test_verify_chain_clean(make_user):
    make_user(login_id="u")
    e1 = AuditEvent.objects.create(event="a")
    e2 = AuditEvent.objects.create(event="b")
    ok, bad = verify_chain()
    assert ok is True
    assert bad is None


def test_verify_chain_detects_tampered_row(make_user):
    make_user(login_id="u")
    e1 = AuditEvent.objects.create(event="a")
    e2 = AuditEvent.objects.create(event="b")
    # Tamper by raw SQL (bypasses our save)
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE audit_auditevent SET context = %s WHERE id = %s",
            ['{"tampered": true}', e2.id],
        )
    ok, bad = verify_chain()
    assert ok is False
    assert bad == e2.id
```

**Verify:**
```bash
cd backend
pytest apps/audit/tests/test_audit_chain_tamper.py -v
# Expected: 2 passed
```

## Step 5: Release smoke

### 5.1 Update `backend/tests/test_release_smoke.py` (from QA-01)

```python
def test_audit_chain_intact():
    from apps.audit.services import verify_chain
    ok, bad = verify_chain()
    assert ok is True
    assert bad is None
```

**Verify:**
```bash
cd backend
pytest tests/test_release_smoke.py -v
# Expected: green
```

## Step 6: Docs

1. Update `CHANGELOG.md` with a `BE-04` entry.
2. Add a row to `upgrads/12_TRACKING/DONE_LOG.md`.

---

## Safety Checks

| Check | Command | Expected |
|---|---|---|
| `delete()` raises | python -c "..." | PermissionError |
| `save()` is atomic | `grep "transaction.atomic" apps/audit/models.py` | match |
| `verify_chain()` clean | `pytest apps/audit/tests/test_audit_chain_tamper.py` | passed |
| Release smoke | `pytest tests/test_release_smoke.py` | green |
| H-08 race test | `pytest apps/audit/tests/test_audit_chain_hardening.py` | passed |
