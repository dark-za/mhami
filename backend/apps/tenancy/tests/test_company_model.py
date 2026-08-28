"""Unit tests for :class:`~apps.tenancy.models.Company` lifecycle state."""

from __future__ import annotations

import pytest

from apps.tenancy.models import CompanyStatus

pytestmark = pytest.mark.django_db


def test_company_operational_state(make_user, make_company):
    """TRIAL companies are operational; SUSPENDED companies are not."""
    company = make_company()
    assert company.is_operational() is True
    company.status = CompanyStatus.SUSPENDED
    assert company.is_operational() is False
