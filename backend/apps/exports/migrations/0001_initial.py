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
            name="ExportBoundaryPolicy",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("future_notification_boundaries", models.JSONField(default=list)),
                ("external_storage_boundaries", models.JSONField(default=list)),
                ("provider_review_checklist", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="export_policy", to="tenancy.company")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="export_policy_updates", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="ExportRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("export_type", models.CharField(choices=[("csv", "CSV"), ("zip", "ZIP"), ("pdf", "PDF")], max_length=32)),
                ("branch_ids", models.JSONField(default=list)),
                ("categories", models.JSONField(default=list)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("queued", "Queued"), ("completed", "Completed"), ("failed", "Failed"), ("expired", "Expired")], default="queued", max_length=32)),
                ("download_token", models.CharField(max_length=128, unique=True)),
                ("file_name", models.CharField(blank=True, max_length=255)),
                ("expires_at", models.DateTimeField()),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("downloaded_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="export_requests", to="tenancy.company")),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="export_requests", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
