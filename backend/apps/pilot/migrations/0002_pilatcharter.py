from __future__ import annotations

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pilot", "0001_initial"),
        ("tenancy", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PilotCharter",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("decision", models.CharField(choices=[("authorize", "Authorize"), ("decline", "Decline"), ("withdraw", "Withdraw")], max_length=16)),
                ("rationale", models.TextField()),
                ("conditions", models.TextField(blank=True)),
                ("observation_start", models.DateField(blank=True, null=True)),
                ("observation_end", models.DateField(blank=True, null=True)),
                ("success_measures", models.JSONField(default=list)),
                ("signed_at", models.DateTimeField(auto_now_add=True)),
                ("signature_hmac", models.CharField(blank=True, max_length=64)),
                ("metadata", models.JSONField(default=dict)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pilot_charters", to="tenancy.company")),
                ("pilot_program", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="charters", to="pilot.pilotprogram")),
                ("signed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pilot_charters", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["company", "signed_at"], name="pilot_charter_co_sa_idx"),
                    models.Index(fields=["pilot_program", "signed_at"], name="pilot_charter_pp_sa_idx"),
                ],
            },
        ),
    ]
