"""Publish the canonical v1.0 versions of the legal documents.

Usage::

    python manage.py seed_legal_documents

The command registers one row per document kind in the
:class:`apps.compliance.models.LegalDocument` table, pointing at the
versioned files under ``docs/legal/``. It is idempotent — re-running
it is a no-op because the (kind, version) pair is unique.

The command is the platform-side companion to the versioned document
directories under ``docs/legal/`` and to the per-directory
``CHANGELOG.md`` files. It does not bypass the legal review gate: the
``is_legal_review_complete`` field is set to ``False`` until the
platform owner signs off, even though the documents are technically
published for the platform to fetch.
"""

from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from apps.compliance.models import LegalDocumentKind
from apps.compliance.services import publish_legal_document
from apps.identity.models import User


SEED_DOCUMENTS: list[dict[str, object]] = [
    {
        "kind": LegalDocumentKind.TERMS,
        "version": "v1.0",
        "content_path": "docs/legal/01_TERMS_OF_USE/v1.0.md",
        "summary": "Terms of Use: registration, trial, lifecycle, AI provider selection, acceptance tracking.",
    },
    {
        "kind": LegalDocumentKind.PRIVACY,
        "version": "v1.0",
        "content_path": "docs/legal/02_PRIVACY_NOTICE/v1.0.md",
        "summary": "Privacy Notice: controller/processor roles, data categories, blur behaviour, retention.",
    },
    {
        "kind": LegalDocumentKind.DATA_PROCESSING,
        "version": "v1.0",
        "content_path": "docs/legal/03_DATA_PROCESSING_TERMS/v1.0.md",
        "summary": "Data Processing Terms: controller/processor instructions, support, sub-processors, retention.",
    },
    {
        "kind": LegalDocumentKind.AI_TRANSFER,
        "version": "v1.0",
        "content_path": "docs/legal/04_AI_TRANSFER_NOTICE/v1.0.md",
        "summary": "AI Transfer Notice: owner acceptance, permitted data set, provider selection, revocation.",
    },
    {
        "kind": LegalDocumentKind.EMPLOYEE_PRIVACY,
        "version": "v1.0",
        "content_path": "docs/legal/05_EMPLOYEE_PRIVACY/v1.0.md",
        "summary": "Employee Privacy Acknowledgement: first-use acknowledgement, scope, retention.",
    },
    {
        "kind": LegalDocumentKind.RETENTION,
        "version": "v1.0",
        "content_path": "docs/legal/06_RETENTION_DELETION/v1.0.md",
        "summary": "Retention and Deletion Policy: 90-day read-only window, hard delete, backup expiry.",
    },
    {
        "kind": LegalDocumentKind.SUPPORT_ACCESS,
        "version": "v1.0",
        "content_path": "docs/legal/07_SUPPORT_ACCESS/v1.0.md",
        "summary": "Support Access Authorization: per-individual grants, auditability, expiry, MFA.",
    },
]


class Command(BaseCommand):
    help = "Publish the v1.0 versions of every legal document under docs/legal/."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--effective-date",
            default=date.today().isoformat(),
            help="ISO date (YYYY-MM-DD) used as the effective_date stamp.",
        )
        parser.add_argument(
            "--publisher-login-id",
            default="platform-admin",
            help="Login id of the platform user used as the published_by actor.",
        )

    def handle(self, *args, **options) -> None:
        effective = date.fromisoformat(options["effective_date"])
        publisher = User.objects.filter(login_id=options["publisher_login_id"]).first()
        if publisher is None:
            # Use a system user fallback so the migration is reproducible in
            # dev. Production must use a real platform owner.
            publisher, _ = User.objects.get_or_create(
                login_id="system-legal-publisher",
                defaults={"display_name": "System Legal Publisher", "is_staff": True, "is_active": True},
            )
        published = 0
        skipped = 0
        for entry in SEED_DOCUMENTS:
            try:
                publish_legal_document(
                    kind=entry["kind"],
                    version=entry["version"],
                    content_path=entry["content_path"],
                    summary=entry["summary"],
                    effective_date=effective,
                    published_by=publisher,
                )
                published += 1
            except Exception as exc:  # noqa: BLE001 - surfaced to operator
                if "is already published" in str(exc):
                    skipped += 1
                    continue
                raise
        self.stdout.write(
            self.style.SUCCESS(
                f"Legal documents refreshed: {published} newly published, {skipped} already published."
            )
        )
