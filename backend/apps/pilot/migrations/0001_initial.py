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
            name="PilotProgram",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(default="planned", max_length=32)),
                ("branch_count_target", models.PositiveSmallIntegerField(default=3)),
                ("employee_count_target", models.PositiveSmallIntegerField(default=30)),
                ("chrome_device_count", models.PositiveSmallIntegerField(default=1)),
                ("ai_provider_name", models.CharField(blank=True, max_length=64)),
                ("connector_owner", models.CharField(blank=True, max_length=255)),
                ("test_environment", models.CharField(blank=True, max_length=255)),
                ("success_measures", models.JSONField(default=list)),
                ("escalation_contacts", models.JSONField(default=list)),
                ("operating_checklist", models.JSONField(default=list)),
                ("weekly_metrics_goal", models.JSONField(default=dict)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="pilot_program", to="tenancy.company")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pilot_program_updates", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="PilotWeeklyReport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("week_ending", models.DateField()),
                ("metrics", models.JSONField(default=dict)),
                ("ai_agreement_rate", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("error_analysis", models.TextField(blank=True)),
                ("capacity_findings", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pilot_weekly_reports", to=settings.AUTH_USER_MODEL)),
                ("pilot_program", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="weekly_reports", to="pilot.pilotprogram")),
            ],
        ),
        migrations.CreateModel(
            name="PilotIssue",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("severity", models.CharField(default="medium", max_length=32)),
                ("status", models.CharField(default="open", max_length=32)),
                ("details", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pilot_issues", to=settings.AUTH_USER_MODEL)),
                ("pilot_program", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="issues", to="pilot.pilotprogram")),
            ],
        ),
        migrations.CreateModel(
            name="PilotChangeRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("rationale", models.TextField(blank=True)),
                ("status", models.CharField(default="requested", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pilot_change_approvals", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pilot_change_requests", to=settings.AUTH_USER_MODEL)),
                ("pilot_program", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="change_requests", to="pilot.pilotprogram")),
            ],
        ),
    ]
