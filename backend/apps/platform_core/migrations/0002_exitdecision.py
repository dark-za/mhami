"""Add ExitDecision model for C-06.

The model captures the platform owner's binding decision on a phase exit
dossier. Decisions are immutable once signed; a revocation creates a
new decision that supersedes the previous one. The signature is an
HMAC-SHA256 over the canonical payload so a tampered rationale is
detected at verification time.
"""

from __future__ import annotations

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("platform_core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ExitDecision",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("phase", models.CharField(max_length=16)),
                ("decision", models.CharField(choices=[("approved", "Approved"), ("conditional", "Conditional approval"), ("rejected", "Rejected"), ("deferred", "Deferred")], max_length=16)),
                ("rationale", models.TextField()),
                ("signed_at", models.DateTimeField(auto_now_add=True)),
                ("signature_hmac", models.CharField(blank=True, max_length=64)),
                ("metadata", models.JSONField(default=dict)),
                ("signed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="exit_decisions", to=settings.AUTH_USER_MODEL)),
                ("supersedes", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="superseded_by", to="platform_core.exitdecision")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["phase", "signed_at"], name="platform_co_phase__idx"),
                    models.Index(fields=["phase", "decision"], name="platform_co_phase__dec_idx"),
                ],
            },
        ),
    ]
