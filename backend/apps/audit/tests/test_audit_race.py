"""H-08 regression tests: AuditEvent chain serialisation.

The audit chain must remain tamper-evident under concurrent writes. The
fix relies on a PostgreSQL ``pg_advisory_xact_lock`` plus an explicit
``select_for_update`` so two writers that try to commit in the same
microsecond do not produce two events with the same ``previous_hash``.

The tests run against the configured database. The single-writer part
runs on any backend; the multi-thread part is conditional on PostgreSQL
because SQLite cannot exercise a real race with the Python GIL.
"""

from __future__ import annotations

import threading

import pytest

from apps.audit.models import AuditEvent, calculate_event_hash
from apps.audit.services import record_audit_event, verify_audit_chain

pytestmark = pytest.mark.django_db


def test_chain_links_when_written_sequentially():
    record_audit_event(event_type="SEQ_1", target_type="system", target_id="1")
    record_audit_event(event_type="SEQ_2", target_type="system", target_id="2")
    record_audit_event(event_type="SEQ_3", target_type="system", target_id="3")

    events = list(AuditEvent.objects.order_by("timestamp", "id"))
    assert [event.event_type for event in events] == ["SEQ_1", "SEQ_2", "SEQ_3"]
    assert events[0].previous_hash == ""
    assert events[1].previous_hash == events[0].event_hash
    assert events[2].previous_hash == events[1].event_hash
    # Each event hash must match the canonical calculation, which proves
    # the chain was built with the previous event's hash and not a stale
    # value.
    for index, event in enumerate(events):
        previous_hash = events[index - 1].event_hash if index else ""
        assert event.event_hash == calculate_event_hash(event, previous_hash)
    assert verify_audit_chain() is True


def test_concurrent_writers_do_not_collide_on_previous_hash():
    """Run on PostgreSQL only — SQLite serialises everything in the GIL.

    The advisory lock is the contract: two writers must observe distinct
    ``previous_hash`` values, which means a deterministic chain order.
    """
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("Audit chain race test requires PostgreSQL.")

    from django.test.utils import setup_test_environment, teardown_test_environment  # noqa: F401

    barrier = threading.Barrier(8)
    results: list[str] = []
    lock = threading.Lock()

    def writer(idx: int) -> None:
        from django.db import connection as thread_connection
        # Each thread needs its own connection; pytest-django handles
        # this via the test database alias, but we still have to close
        # and reopen so the thread sees committed data from peers.
        try:
            barrier.wait(timeout=10)
            event = record_audit_event(
                event_type=f"RACE_{idx}",
                target_type="system",
                target_id=str(idx),
            )
            with lock:
                results.append(event.previous_hash)
        finally:
            thread_connection.close()

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # The advisory lock serialises the writes, so every writer observed
    # a *previous* event whose hash is the head of the chain at write
    # time. We assert that no two threads observed the same previous
    # head — that would mean they raced past each other.
    assert len(results) == 8
    assert len(set(results)) == 8, f"Duplicate previous_hash detected: {results}"
    # And the chain is still valid.
    assert verify_audit_chain() is True
