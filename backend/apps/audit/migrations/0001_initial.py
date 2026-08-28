from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(max_length=200)),
                ("actor_id", models.CharField(blank=True, max_length=64)),
                ("target_type", models.CharField(max_length=200)),
                ("target_id", models.CharField(max_length=200)),
                ("branch_id", models.CharField(blank=True, max_length=200)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("request_id", models.UUIDField(default=uuid.uuid4)),
                ("before", models.JSONField(default=dict)),
                ("after", models.JSONField(default=dict)),
                ("metadata", models.JSONField(default=dict)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["actor_id", "timestamp"], name="audit_audit_actor_i_573746_idx"),
                    models.Index(fields=["target_type", "target_id"], name="audit_audit_target__59bbff_idx"),
                ],
            },
        ),
    ]
