from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from contextlib import contextmanager

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection, models, transaction
from django.utils import timezone

# H-08: PG advisory lock key for the audit chain. Picked high enough to
# avoid collision with any other application-level advisory lock the
# platform may take. Locking this key before computing the chain head
# gives us a global serialisation point that does not depend on the
# presence of a wrapping transaction (the historical implementation only
# held a row lock when ``connection.get_autocommit()`` was False).
AUDIT_CHAIN_ADVISORY_LOCK_KEY = 0x4D48414D49  # "MHAMI"


@contextmanager
def _audit_chain_lock():
    """Hold a PostgreSQL advisory transaction lock for the audit chain.

    Falls back to a no-op on SQLite so the test suite (which runs on
    SQLite by default) is not blocked. In production we run on
    PostgreSQL, where the lock is what actually serialises concurrent
    audit writers.
    """
    vendor = connection.vendor
    if vendor != "postgresql":
        yield
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [AUDIT_CHAIN_ADVISORY_LOCK_KEY])
    yield


def _canonical_event(event: "AuditEvent", previous_hash: str) -> bytes:
    payload = {
        "id": str(event.id),
        "event_type": event.event_type,
        "actor_id": event.actor_id,
        "target_type": event.target_type,
        "target_id": event.target_id,
        "branch_id": event.branch_id,
        "timestamp": event.timestamp.isoformat(),
        "request_id": str(event.request_id),
        "before": event.before,
        "after": event.after,
        "metadata": event.metadata,
        "previous_hash": previous_hash,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def calculate_event_hash(event: "AuditEvent", previous_hash: str) -> str:
    return hashlib.sha256(_canonical_event(event, previous_hash)).hexdigest()


def calculate_event_hmac(event_hash: str) -> str:
    secret = str(getattr(settings, "AUDIT_HMAC_SECRET", settings.SECRET_KEY)).encode("utf-8")
    return hmac.new(secret, event_hash.encode("ascii"), hashlib.sha256).hexdigest()


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=200)
    actor_id = models.CharField(max_length=64, blank=True)
    target_type = models.CharField(max_length=200)
    target_id = models.CharField(max_length=200)
    branch_id = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, editable=False)
    request_id = models.UUIDField(default=uuid.uuid4)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    previous_hash = models.CharField(max_length=64, default="", editable=False)
    event_hash = models.CharField(max_length=64, default="", editable=False)
    integrity_hmac = models.CharField(max_length=64, default="", editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["actor_id", "timestamp"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Audit events are append-only")
        if self.timestamp is None:
            self.timestamp = timezone.now()
        # H-08: open a transaction (if we are not already inside one) and
        # hold the audit chain advisory lock so concurrent writers are
        # serialised on PostgreSQL. We always go through this path — the
        # old code relied on the caller being in a transaction and on
        # ``select_for_update`` being a no-op outside a transaction.
        with transaction.atomic():
            with _audit_chain_lock():
                # ``select_for_update`` requires a transaction; combined
                # with the advisory lock it gives us belt-and-braces
                # against a missing transaction wrapper at the call site.
                previous = (
                    type(self).objects.select_for_update().order_by("-timestamp", "-id").first()
                )
                self.previous_hash = previous.event_hash if previous else ""
                self.event_hash = calculate_event_hash(self, self.previous_hash)
                self.integrity_hmac = calculate_event_hmac(self.event_hash)
                return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit events are append-only")

    @property
    def chain_hash(self) -> str:
        return self.event_hash

    @property
    def hmac_digest(self) -> str:
        return self.integrity_hmac

    def verify_integrity(self, previous_hash: str | None = None) -> bool:
        expected_previous = self.previous_hash if previous_hash is None else previous_hash
        expected_hash = calculate_event_hash(self, expected_previous)
        return (
            hmac.compare_digest(self.event_hash, expected_hash)
            and hmac.compare_digest(self.integrity_hmac, calculate_event_hmac(self.event_hash))
            and self.previous_hash == expected_previous
        )
