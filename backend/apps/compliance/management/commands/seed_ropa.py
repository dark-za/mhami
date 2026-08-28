"""Seed the published ROPA with the platform's documented activities.

Usage::

    python manage.py seed_ropa

The command is idempotent. Existing rows are updated in place; new
rows are added for activities that have been added to the manifest.

The command is the platform-side companion to
``docs/legal/11_ROPA/manifest.md`` and to
``docs/SECURITY_AND_DATA_BASELINE.md``. It is the data behind the
``/api/v1/compliance/ropa`` endpoint.
"""

from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from apps.compliance.models import LegalBasis
from apps.compliance.services import publish_processing_activity


# Each tuple is a (name, payload) pair. The payload is forwarded to
# :func:`apps.compliance.services.publish_processing_activity` verbatim.
SEED_ACTIVITIES: list[tuple[str, dict[str, object]]] = [
    (
        "company_registration",
        {
            "name": "Company Registration",
            "purpose": "Onboarding new tenant companies and their initial owner account.",
            "controller": "Tenant company (self-registered)",
            "data_categories": [
                "company_name",
                "company_code",
                "industry",
                "contact_email",
                "contact_phone",
                "owner_login_id",
                "owner_display_name",
            ],
            "data_subject_categories": ["business owners"],
            "recipients": ["internal platform staff"],
            "lawful_basis": LegalBasis.CONTRACT,
            "retention_days": 365 + 90,  # active contract + 90-day export window
            "security_measures": "Encryption at rest, TLS in transit, MFA on owner login, audited registration events.",
            "cross_border_transfer": False,
        },
    ),
    (
        "evidence_capture",
        {
            "name": "Evidence Capture",
            "purpose": "Collecting direct task evidence (camera images, numeric data, notes) for review and audit.",
            "controller": "Tenant company",
            "data_categories": [
                "camera_images",
                "blurred_derivatives",
                "numeric_inputs",
                "free_form_notes",
                "task_metadata",
            ],
            "data_subject_categories": ["employees", "third parties incidentally captured in evidence"],
            "recipients": ["branch monitors", "company owner", "audit process"],
            "lawful_basis": LegalBasis.LEGITIMATE_INTERESTS,
            "retention_days": 180,
            "security_measures": "Private media storage, signed access URLs, face-blur derivatives before release for review, tenant-scoped authorization.",
            "cross_border_transfer": False,
        },
    ),
    (
        "review_and_decisions",
        {
            "name": "Review and Decisions",
            "purpose": "Recording quality-monitor and owner decisions, including accept, retry, escalate, and corrective actions.",
            "controller": "Tenant company",
            "data_categories": [
                "decision_payload",
                "decision_rationale",
                "monitor_identity",
                "branch_scope",
            ],
            "data_subject_categories": ["employees", "monitors", "owners"],
            "recipients": ["tenant owner", "audit process"],
            "lawful_basis": LegalBasis.LEGITIMATE_INTERESTS,
            "retention_days": 365,
            "security_measures": "Append-only audit chain, HMAC integrity, branch-scoped access, role-required authorization.",
            "cross_border_transfer": False,
        },
    ),
    (
        "external_ai_analysis",
        {
            "name": "External AI Analysis",
            "purpose": "Sending permitted task criteria, opaque reference media identifiers, and blurred evidence derivatives to the tenant-selected AI provider for verification assistance.",
            "controller": "Tenant company",
            "data_categories": [
                "task_criteria",
                "reference_media_id",
                "blurred_evidence_derivatives",
            ],
            "data_subject_categories": ["no personal data; blurred derivatives only"],
            "recipients": ["tenant-selected AI provider"],
            "lawful_basis": LegalBasis.CONSENT,
            "cross_border_transfer": True,
            "transfer_mechanism": "Per-tenant provider contract; transfer only after explicit owner acceptance of the AI Transfer Notice.",
            "retention_days": 30,
            "security_measures": "Owner-controlled endpoint and credentials, opaque identifiers, blurred derivatives only, in-flight cancellation on revocation.",
        },
    ),
    (
        "tenant_support",
        {
            "name": "Tenant Support",
            "purpose": "Providing named platform support access on explicit owner request.",
            "controller": "Tenant company",
            "data_categories": [
                "support_user_id",
                "grant_reason",
                "grant_expiry",
                "support_actions",
            ],
            "data_subject_categories": ["company owner", "support users"],
            "recipients": ["platform support team", "tenant owner"],
            "lawful_basis": LegalBasis.LEGITIMATE_INTERESTS,
            "retention_days": 365,
            "security_measures": "Per-individual grants, audit logging, expiry semantics, MFA on support accounts.",
            "cross_border_transfer": False,
        },
    ),
    (
        "export_and_deletion",
        {
            "name": "Export and Deletion",
            "purpose": "Owner-initiated export during the 90-day read-only window and subsequent hard deletion.",
            "controller": "Tenant company",
            "data_categories": ["exported_company_data", "deletion_proof"],
            "data_subject_categories": ["company owner", "employees"],
            "recipients": ["company owner"],
            "lawful_basis": LegalBasis.LEGAL_OBLIGATION,
            "retention_days": 90,
            "security_measures": "Owner-only export authorization, signed and expiring download URLs, audited export action, hard delete at end of window with backup expiry through documented cycle.",
            "cross_border_transfer": False,
        },
    ),
]


class Command(BaseCommand):
    help = "Publish the documented ROPA rows for the platform."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--last-reviewed-at",
            default=date.today().isoformat(),
            help="ISO date (YYYY-MM-DD) used as the last_reviewed_at stamp.",
        )

    def handle(self, *args, **options) -> None:
        last_reviewed = date.fromisoformat(options["last_reviewed_at"])
        published = 0
        updated = 0
        for name, payload in SEED_ACTIVITIES:
            payload = {**payload, "last_reviewed_at": last_reviewed, "actor_id": "seed_ropa"}
            activity = publish_processing_activity(**payload)
            if activity.published_at and activity.published_at.date() == last_reviewed:
                published += 1
            else:
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"ROPA rows refreshed: {len(SEED_ACTIVITIES)} total, {published} newly published, {updated} updated."
            )
        )
