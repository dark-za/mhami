"""BE-05 regression tests: log failed login attempts.

The ``CompanyCodeBackend`` must record an audit event for every
unsuccessful login attempt. The reason code in the metadata is the
authoritative contract; tests assert each of the known reasons is
covered (missing fields, unknown company, inactive company, unknown
user, bad password, no membership).
"""
from __future__ import annotations

import pytest
from django.test import RequestFactory

from apps.audit.models import AuditEvent
from apps.identity.models import User
from apps.organizations.models import CompanyMembership, CompanyRole
from apps.tenancy.auth_backends import CompanyCodeBackend
from apps.tenancy.models import Company, CompanyStatus

pytestmark = pytest.mark.django_db


def _request():
    """Build a minimal request object with a ``REMOTE_ADDR``."""
    factory = RequestFactory()
    request = factory.post("/api/v1/auth/login")
    request.META["REMOTE_ADDR"] = "203.0.113.7"
    return request


def _login_failed_events(reason: str) -> list[AuditEvent]:
    return [
        event
        for event in AuditEvent.objects.filter(event_type="LOGIN_FAILED").all()
        if event.metadata.get("reason") == reason
    ]


def test_missing_fields_recorded_as_failure():
    backend = CompanyCodeBackend()
    result = backend.authenticate(request=_request(), company_code="", login_id="x", password="p")
    assert result is None
    assert _login_failed_events("missing_fields"), "missing_fields event expected"


def test_unknown_company_recorded_as_failure():
    backend = CompanyCodeBackend()
    result = backend.authenticate(
        request=_request(), company_code="nope", login_id="u", password="p"
    )
    assert result is None
    assert _login_failed_events("unknown_company")


def test_inactive_company_recorded_as_failure(make_company):
    company = make_company(status=CompanyStatus.SUSPENDED)
    backend = CompanyCodeBackend()
    result = backend.authenticate(
        request=_request(), company_code=company.code, login_id="u", password="p"
    )
    assert result is None
    assert _login_failed_events("inactive_company")


def test_unknown_user_recorded_as_failure(make_company):
    company = make_company()
    backend = CompanyCodeBackend()
    result = backend.authenticate(
        request=_request(), company_code=company.code, login_id="ghost", password="p"
    )
    assert result is None
    assert _login_failed_events("unknown_user")


def test_bad_password_recorded_as_failure(make_user, make_company):
    user = make_user(login_id="login-fail")
    company = make_company()
    CompanyMembership.objects.create(company=company, user=user, role=CompanyRole.OWNER)
    backend = CompanyCodeBackend()
    result = backend.authenticate(
        request=_request(),
        company_code=company.code,
        login_id=user.login_id,
        password="wrong",
    )
    assert result is None
    assert _login_failed_events("bad_password")


def test_not_authorized_for_company_recorded_as_failure(make_user, make_company):
    """A user that exists but is not a member of the active company."""
    user = make_user(login_id="outsider")
    user.set_password("TestPass123!")
    user.save()
    company = make_company()
    backend = CompanyCodeBackend()
    result = backend.authenticate(
        request=_request(),
        company_code=company.code,
        login_id=user.login_id,
        password="TestPass123!",
    )
    assert result is None
    assert _login_failed_events("not_authorized_for_company")


def test_metadata_stores_remote_addr_and_company_code(make_company):
    company = make_company()
    backend = CompanyCodeBackend()
    backend.authenticate(
        request=_request(), company_code=company.code, login_id="ghost", password="p"
    )
    event = _login_failed_events("unknown_user")[-1]
    assert event.metadata["remote_addr"] == "203.0.113.7"
    assert event.metadata["company_code"] == company.code
