from __future__ import annotations

import hashlib
import hmac
import json

from django.conf import settings
from django.db import migrations, models


def _payload(row, previous_hash: str) -> bytes:
    values = {
        "id": str(row.id),
        "event_type": row.event_type,
        "actor_id": row.actor_id,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "branch_id": row.branch_id,
        "timestamp": row.timestamp.isoformat(),
        "request_id": str(row.request_id),
        "before": row.before,
        "after": row.after,
        "metadata": row.metadata,
        "previous_hash": previous_hash,
    }
    return json.dumps(values, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def backfill_integrity_fields(apps, schema_editor):
    AuditEvent = apps.get_model("audit", "AuditEvent")
    secret = str(getattr(settings, "AUDIT_HMAC_SECRET", settings.SECRET_KEY)).encode("utf-8")
    previous_hash = ""
    for row in AuditEvent.objects.order_by("timestamp", "id"):
        event_hash = hashlib.sha256(_payload(row, previous_hash)).hexdigest()
        digest = hmac.new(secret, event_hash.encode("ascii"), hashlib.sha256).hexdigest()
        AuditEvent.objects.filter(pk=row.pk).update(
            previous_hash=previous_hash,
            event_hash=event_hash,
            integrity_hmac=digest,
        )
        previous_hash = event_hash


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="auditevent",
            name="previous_hash",
            field=models.CharField(default="", editable=False, max_length=64),
        ),
        migrations.AddField(
            model_name="auditevent",
            name="event_hash",
            field=models.CharField(default="", editable=False, max_length=64),
        ),
        migrations.AddField(
            model_name="auditevent",
            name="integrity_hmac",
            field=models.CharField(default="", editable=False, max_length=64),
        ),
        migrations.RunPython(backfill_integrity_fields, migrations.RunPython.noop),
    ]
