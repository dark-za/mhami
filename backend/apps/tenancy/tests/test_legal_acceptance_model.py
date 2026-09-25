"""Model-level tests for LegalAcceptance version validation."""

from __future__ import annotations

import pytest

from apps.compliance.models import LegalDocumentKind
from apps.compliance.services import publish_legal_document
from apps.tenancy.models import LegalAcceptance, LegalDocumentType

pytestmark = pytest.mark.django_db


def _publish_terms(publisher, version: str) -> None:
    publish_legal_document(
        kind=LegalDocumentKind.TERMS,
        version=version,
        content_path=f"docs/legal/01_TERMS_OF_USE/{version}.md",
        summary=f"Terms of Use {version}",
        effective_date="2026-01-01",
        published_by=publisher,
    )


def test_acceptance_rejects_stale_version(make_user, make_company, make_membership):
    """A version that is not the currently published one is refused."""
    from apps.organizations.models import CompanyRole

    publisher = make_user(login_id="legal-publisher")
    _publish_terms(publisher, "v1.0")
    owner = make_user(login_id="legal-owner")
    company = make_company(name="Legal Co", code="legal-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)

    with pytest.raises(ValueError) as excinfo:
        LegalAcceptance.objects.create(
            company=company,
            accepted_by=owner,
            document_type=LegalDocumentType.TERMS,
            document_version="v0.9",
        )
    assert "currently published" in str(excinfo.value)
    assert not LegalAcceptance.objects.filter(company=company).exists()


def test_acceptance_accepts_current_version(make_user, make_company, make_membership):
    """Matching the currently published version is allowed."""
    from apps.organizations.models import CompanyRole

    publisher = make_user(login_id="legal-publisher")
    _publish_terms(publisher, "v1.0")
    owner = make_user(login_id="legal-owner")
    company = make_company(name="Legal Co", code="legal-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)

    acceptance = LegalAcceptance.objects.create(
        company=company,
        accepted_by=owner,
        document_type=LegalDocumentType.TERMS,
        document_version="v1.0",
    )
    assert acceptance.pk is not None


def test_acceptance_allowed_when_nothing_published(make_user, make_company, make_membership):
    """Initial provisioning (default "v1") works before any document is published."""
    from apps.organizations.models import CompanyRole

    owner = make_user(login_id="legal-owner")
    company = make_company(name="Legal Co", code="legal-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)

    acceptance = LegalAcceptance.objects.create(
        company=company,
        accepted_by=owner,
        document_type=LegalDocumentType.TERMS,
        document_version="v1",
    )
    assert acceptance.pk is not None


def test_acceptance_historical_import_bypasses_check(make_user, make_company, make_membership):
    """A controlled historical import may record a superseded version."""
    from apps.organizations.models import CompanyRole

    publisher = make_user(login_id="legal-publisher")
    _publish_terms(publisher, "v1.0")
    owner = make_user(login_id="legal-owner")
    company = make_company(name="Legal Co", code="legal-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)

    acceptance = LegalAcceptance.objects.create(
        company=company,
        accepted_by=owner,
        document_type=LegalDocumentType.TERMS,
        document_version="v0.9",
        metadata={"historical_import": True},
    )
    assert acceptance.pk is not None


def test_acceptance_update_skips_recheck(make_user, make_company, make_membership):
    """The version check runs only when creating a row, not on updates."""
    from apps.organizations.models import CompanyRole

    publisher = make_user(login_id="legal-publisher")
    _publish_terms(publisher, "v1.0")
    owner = make_user(login_id="legal-owner")
    company = make_company(name="Legal Co", code="legal-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)

    acceptance = LegalAcceptance.objects.create(
        company=company,
        accepted_by=owner,
        document_type=LegalDocumentType.TERMS,
        document_version="v1.0",
    )
    acceptance.document_version = "v0.9"
    acceptance.save()
    acceptance.refresh_from_db()
    assert acceptance.document_version == "v0.9"
