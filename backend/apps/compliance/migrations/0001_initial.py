"""Initial migration for the compliance module.

This migration creates the three ROPA/DSR/legal-document tables
documented in ``apps/compliance/models.py``.
"""

from __future__ import annotations

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenancy", "0002_supportauthorization_expiry"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProcessingActivity",
            fields=[
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=200, unique=True)),
                ("purpose", models.TextField()),
                ("controller", models.CharField(max_length=200)),
                ("processor", models.CharField(default="Mhami Platform", max_length=200)),
                ("data_categories", models.JSONField(default=list)),
                ("data_subject_categories", models.JSONField(default=list)),
                ("recipients", models.JSONField(default=list)),
                (
                    "lawful_basis",
                    models.CharField(
                        choices=[
                            ("consent", "Consent"),
                            ("contract", "Contract performance"),
                            ("legal_obligation", "Legal obligation"),
                            ("vital_interests", "Vital interests"),
                            ("public_task", "Public task"),
                            ("legitimate_interests", "Legitimate interests"),
                        ],
                        max_length=64,
                    ),
                ),
                ("cross_border_transfer", models.BooleanField(default=False)),
                ("transfer_mechanism", models.CharField(blank=True, max_length=200)),
                ("retention_days", models.PositiveIntegerField()),
                ("security_measures", models.TextField()),
                ("last_reviewed_at", models.DateField()),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.AddIndex(
            model_name="processingactivity",
            index=models.Index(fields=["is_published", "name"], name="compliance__is_publ_e5d526_idx"),
        ),
        migrations.AddIndex(
            model_name="processingactivity",
            index=models.Index(fields=["last_reviewed_at"], name="compliance__last_re_63d0f4_idx"),
        ),
        migrations.CreateModel(
            name="DSRRequest",
            fields=[
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                (
                    "request_type",
                    models.CharField(
                        choices=[
                            ("access", "Right to Access"),
                            ("rectification", "Right to Rectification"),
                            ("erasure", "Right to Erasure"),
                            ("restriction", "Right to Restriction"),
                            ("portability", "Right to Portability"),
                            ("objection", "Right to Object"),
                        ],
                        max_length=32,
                    ),
                ),
                ("subject_email", models.EmailField(max_length=254)),
                ("subject_reference", models.CharField(blank=True, max_length=200)),
                ("description", models.TextField(blank=True)),
                ("verification_token_hash", models.CharField(blank=True, max_length=64)),
                ("verification_sent_at", models.DateTimeField(blank=True, null=True)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("verification_attempts", models.PositiveSmallIntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("verified", "Identity Verified"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=32,
                    ),
                ),
                ("decision_notes", models.TextField(blank=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dsr_requests",
                        to="tenancy.company",
                    ),
                ),
                (
                    "submitted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="dsr_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "decided_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="dsr_decisions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-submitted_at",),
            },
        ),
        migrations.AddIndex(
            model_name="dsrrequest",
            index=models.Index(fields=["company", "status"], name="compliance__company_d05fff_idx"),
        ),
        migrations.AddIndex(
            model_name="dsrrequest",
            index=models.Index(fields=["status", "submitted_at"], name="compliance__status_82396f_idx"),
        ),
        migrations.CreateModel(
            name="LegalDocument",
            fields=[
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("terms", "Terms of Use"),
                            ("privacy", "Privacy Notice"),
                            ("ai_transfer", "AI Transfer Notice"),
                            ("employee_privacy", "Employee Privacy Acknowledgement"),
                            ("data_processing", "Data Processing Terms"),
                            ("retention", "Retention and Deletion Policy"),
                            ("support_access", "Support Access Authorization"),
                            ("dpia", "Data Protection Impact Assessment"),
                            ("breach_response", "Data Breach Response Plan"),
                            ("ropa", "Record of Processing Activities"),
                        ],
                        max_length=64,
                    ),
                ),
                ("version", models.CharField(max_length=64)),
                ("content_path", models.CharField(max_length=500)),
                ("summary", models.CharField(blank=True, max_length=500)),
                ("effective_date", models.DateField()),
                ("supersedes_version", models.CharField(blank=True, max_length=64)),
                ("published_at", models.DateTimeField(auto_now_add=True)),
                ("is_current", models.BooleanField(default=False)),
                (
                    "published_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="published_legal_documents",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("kind", "-effective_date"),
            },
        ),
        migrations.AddConstraint(
            model_name="legaldocument",
            constraint=models.UniqueConstraint(
                fields=("kind", "version"),
                name="compliance_legal_document_unique_version",
            ),
        ),
        migrations.AddConstraint(
            model_name="legaldocument",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_current", True)),
                fields=("kind", "is_current"),
                name="compliance_legal_document_single_current",
            ),
        ),
        migrations.AddIndex(
            model_name="legaldocument",
            index=models.Index(fields=["kind", "effective_date"], name="compliance__kind_243a1a_idx"),
        ),
    ]
