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
            name="TenantConnectorEnrollment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("connector_version", models.CharField(max_length=64)),
                ("compatibility_window", models.CharField(default=">=0.1,<1.0", max_length=64)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("active", "Active"), ("revoked", "Revoked"), ("outdated", "Outdated")], default="pending", max_length=32)),
                ("health_status", models.CharField(choices=[("healthy", "Healthy"), ("degraded", "Degraded"), ("offline", "Offline")], default="offline", max_length=32)),
                ("shared_secret_fingerprint", models.CharField(blank=True, max_length=128)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="connector_enrollment", to="tenancy.company")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="connector_enrollments", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
