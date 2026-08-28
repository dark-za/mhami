"""Helpers that link :mod:`apps.tenancy` legal acceptances to the
:class:`~apps.compliance.models.LegalDocument` registry.

The :class:`~apps.tenancy.models.LegalAcceptance` model records the
``(document_type, version)`` pair that an owner or employee has
accepted. The :class:`~apps.compliance.models.LegalDocument` registry
is the single source of truth for what is currently published.

The helpers in this module:

* Map ``LegalDocumentType`` (tenancy) to ``LegalDocumentKind``
  (compliance) so the two enums can be cross-referenced.
* Expose :func:`is_acceptance_current` to check whether a stored
  acceptance is for the currently-published version.
* Expose :func:`missing_acceptance_kinds` to enumerate the document
  kinds a tenant still needs to accept.
* Expose :func:`require_current_acceptance` as a service-side guard
  used by the registration and management flows.

The module deliberately imports ``apps.tenancy`` lazily inside the
helper functions to avoid an import cycle between the two apps.
"""

from __future__ import annotations

from typing import Iterable

from django.db.models import QuerySet


# Map ``LegalDocumentType`` (tenancy) → ``LegalDocumentKind`` (compliance).
# The mapping is the single point of contact between the two enums; if
# either side is extended, the mapping is updated here.
LEGAL_TYPE_TO_KIND: dict[str, str] = {
    "terms": "terms",
    "privacy": "privacy",
    "ai_transfer": "ai_transfer",
    "employee_privacy": "employee_privacy",
}


def is_acceptance_current(*, document_type: str, document_version: str) -> bool:
    """Return ``True`` if a stored acceptance is for the current version.

    Args:
        document_type: A value from
            :class:`apps.tenancy.models.LegalDocumentType`.
        document_version: The version string stored on the acceptance.

    Returns:
        ``True`` if the current published
        :class:`~apps.compliance.models.LegalDocument` for the matching
        kind has the same version; ``False`` otherwise. If no document
        is currently published for the kind, the acceptance cannot be
        current.
    """
    from .models import LegalDocumentKind
    from .services import current_legal_document

    kind_value = LEGAL_TYPE_TO_KIND.get(document_type)
    if kind_value is None:
        return False
    try:
        kind = LegalDocumentKind(kind_value)
    except ValueError:
        return False
    document = current_legal_document(kind)
    if document is None:
        return False
    return document.version == document_version


def missing_acceptance_kinds(company) -> list[str]:
    """Return the document kinds a tenant still needs to accept.

    The function inspects the company's existing
    :class:`~apps.tenancy.models.LegalAcceptance` rows and returns the
    kinds (in the ``LegalDocumentType`` vocabulary) that do **not** have
    an acceptance for the currently-published version. Used by
    :func:`require_current_acceptance` and by the dashboard.

    Args:
        company: The :class:`~apps.tenancy.models.Company` to inspect.

    Returns:
        A list of ``LegalDocumentType`` values for which the company has
        no current-version acceptance.
    """
    from .models import LegalDocumentKind
    from .services import current_legal_document
    from apps.tenancy.models import LegalAcceptance

    outstanding: list[str] = []
    for tenancy_value, kind_value in LEGAL_TYPE_TO_KIND.items():
        try:
            kind = LegalDocumentKind(kind_value)
        except ValueError:
            continue
        document = current_legal_document(kind)
        if document is None:
            # No document is currently published for this kind. Skip
            # rather than block — there is nothing to accept.
            continue
        accepted = LegalAcceptance.objects.filter(
            company=company,
            document_type=tenancy_value,
            document_version=document.version,
        ).exists()
        if not accepted:
            outstanding.append(tenancy_value)
    return outstanding


def require_current_acceptance(company, *, kinds: Iterable[str] | None = None) -> None:
    """Raise :class:`AcceptanceRequired` if the tenant is missing current acceptances.

    Args:
        company: The :class:`~apps.tenancy.models.Company` to validate.
        kinds: Optional subset of ``LegalDocumentType`` values to check.
            Defaults to all kinds for which a document is currently
            published.

    Raises:
        AcceptanceRequired: If any required kind lacks a current
            acceptance. The exception carries the list of missing kinds
            in :attr:`AcceptanceRequired.missing_kinds`.
    """
    missing = missing_acceptance_kinds(company)
    if kinds is not None:
        kinds_set = set(kinds)
        missing = [value for value in missing if value in kinds_set]
    if missing:
        raise AcceptanceRequired(missing)


class AcceptanceRequired(Exception):
    """Raised when a tenant is missing one or more current legal acceptances.

    Attributes:
        missing_kinds: The list of ``LegalDocumentType`` values for
            which no current acceptance was found.
    """

    def __init__(self, missing_kinds: list[str]):
        self.missing_kinds = missing_kinds
        super().__init__(
            "Company is missing current legal acceptances for: " + ", ".join(missing_kinds)
        )


def query_legal_acceptances(company) -> QuerySet:
    """Return the queryset of acceptances for a company.

    The helper is a thin wrapper around
    :class:`~apps.tenancy.models.LegalAcceptance` so the compliance
    module can avoid importing the tenancy models at module load time.

    Args:
        company: The :class:`~apps.tenancy.models.Company` to filter on.

    Returns:
        The :class:`QuerySet` of acceptances for the company.
    """
    from apps.tenancy.models import LegalAcceptance

    return LegalAcceptance.objects.filter(company=company)
