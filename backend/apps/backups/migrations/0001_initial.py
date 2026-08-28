from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenancy", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BackupPolicy",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("destination_name", models.CharField(default="secondary", max_length=255)),
                ("encrypted", models.BooleanField(default=True)),
                ("schedule_cron", models.CharField(default="0 2 * * *", max_length=64)),
                ("rpo_hours", models.PositiveSmallIntegerField(default=24)),
                ("rto_hours", models.PositiveSmallIntegerField(default=24)),
                ("includes_private_media", models.BooleanField(default=True)),
                ("includes_configuration", models.BooleanField(default=True)),
                ("includes_tenant_state", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="backup_policy", to="tenancy.company")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="backup_policy_updates", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="BackupRun",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("requested", "Requested"), ("completed", "Completed"), ("failed", "Failed"), ("restored", "Restored")], default="requested", max_length=32)),
                ("artifact_name", models.CharField(blank=True, max_length=255)),
                ("manifest", models.JSONField(default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("restored_at", models.DateTimeField(blank=True, null=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="backup_runs", to="tenancy.company")),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="backup_runs", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="RestoreRun",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("requested", "Requested"), ("completed", "Completed"), ("failed", "Failed"), ("restored", "Restored")], default="requested", max_length=32)),
                ("verified_database", models.BooleanField(default=False)),
                ("verified_media", models.BooleanField(default=False)),
                ("verified_configuration", models.BooleanField(default=False)),
                ("report", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("backup_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="restore_runs", to="backups.backuprun")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="restore_runs", to="tenancy.company")),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="restore_runs", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
