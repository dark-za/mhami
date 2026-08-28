from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="FeatureFlag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=200)),
                ("enabled", models.BooleanField(default=False)),
                ("scope", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=["key", "scope"], name="platform_feature_flag_unique_scope"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ModuleHealthSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("module_slug", models.CharField(max_length=120, unique=True)),
                ("status", models.CharField(max_length=20)),
                ("details", models.JSONField(default=dict)),
                ("checked_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="OutboxEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_name", models.CharField(max_length=200)),
                ("aggregate_type", models.CharField(max_length=200)),
                ("aggregate_id", models.CharField(max_length=200)),
                ("payload", models.JSONField(default=dict)),
                ("request_id", models.UUIDField(default=uuid.uuid4)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("attempt_count", models.PositiveIntegerField(default=0)),
                ("last_error", models.TextField(blank=True)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["event_name", "occurred_at"], name="platform_co_event_n_266a98_idx"),
                    models.Index(fields=["published_at", "occurred_at"], name="platform_co_publish_7fd604_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="PlatformSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=200, unique=True)),
                ("value", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
