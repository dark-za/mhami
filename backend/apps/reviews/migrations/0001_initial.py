from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenancy", "0001_initial"),
        ("organizations", "0001_initial"),
        ("tasks", "0001_initial"),
        ("evidence", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ReviewPolicySetting",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("employee_score_visibility", models.CharField(default="summary", max_length=32)),
                ("historical_report_restatement", models.BooleanField(default=False)),
                ("monitor_approval_required", models.BooleanField(default=True)),
                ("sensitive_task_claim_restricted", models.BooleanField(default=True)),
                ("extra_evidence_required", models.BooleanField(default=False)),
                ("owner_alerts_enabled", models.BooleanField(default=True)),
                ("approved_task_weight_cap", models.PositiveSmallIntegerField(default=5)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="review_policy", to="tenancy.company")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="review_policy_updates", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="ReviewDecision",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("decision_type", models.CharField(choices=[("approve", "Approve"), ("approve_despite_alert", "Approve Despite Alert"), ("retry_same_task", "Retry Same Task"), ("mark_missed", "Mark Missed"), ("create_corrective_task", "Create Corrective Task"), ("cancel", "Cancel"), ("override_restriction", "Override Restriction")], max_length=32)),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("restriction_name", models.CharField(blank=True, max_length=128)),
                ("original_status", models.CharField(blank=True, max_length=32)),
                ("resulting_status", models.CharField(blank=True, max_length=32)),
                ("metadata", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="review_decisions", to="organizations.branch")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="review_decisions", to="tenancy.company")),
                ("decided_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="review_decisions", to=settings.AUTH_USER_MODEL)),
                ("evidence_item", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="review_decisions", to="evidence.evidenceitem")),
                ("generated_task_instance", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="generated_by_review_decisions", to="tasks.taskinstance")),
                ("issue_report", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="review_decisions", to="evidence.taskissuereport")),
                ("task_instance", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="review_decisions", to="tasks.taskinstance")),
            ],
        ),
    ]
