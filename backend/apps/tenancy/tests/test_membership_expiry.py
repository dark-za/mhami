"""C-08 regression tests: membership expiry and revocation.

The tenant context helper now treats a membership with a past
``active_until`` as inactive even when ``active=True``. The test
exercises the boundary in both directions.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from apps.organizations.models import CompanyMembership, CompanyRole
from apps.tenancy.access import active_membership_q, tenant_context

pytestmark = pytest.mark.django_db


def _setup(make_user, make_company, make_membership):
    owner = make_user(login_id="exp-owner", display_name="Owner")
    company = make_company(code="exp-co", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    return owner, company


def test_active_membership_q_excludes_past_expiry(make_user, make_company, make_membership):
    owner, company = _setup(make_user, make_company, make_membership)
    future = timezone.now() + timedelta(days=1)
    CompanyMembership.objects.filter(user=owner, company=company).update(active_until=future)
    assert CompanyMembership.objects.filter(active_membership_q(), user=owner, company=company).exists()
    CompanyMembership.objects.filter(user=owner, company=company).update(active_until=timezone.now() - timedelta(seconds=1))
    assert not CompanyMembership.objects.filter(active_membership_q(), user=owner, company=company).exists()


def test_tenant_context_rejects_expired_membership(make_user, make_company, make_membership):
    owner, company = _setup(make_user, make_company, make_membership)
    # Expire the membership.
    CompanyMembership.objects.filter(user=owner, company=company).update(active_until=timezone.now() - timedelta(hours=1))
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()
    request = client.get("/api/v1/auth/me").wsgi_request
    request.user = owner
    with pytest.raises(Exception):
        tenant_context(request)


def test_tenant_context_accepts_future_expiry(make_user, make_company, make_membership):
    owner, company = _setup(make_user, make_company, make_membership)
    CompanyMembership.objects.filter(user=owner, company=company).update(active_until=timezone.now() + timedelta(days=2))
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()
    request = client.get("/api/v1/auth/me").wsgi_request
    request.user = owner
    context = tenant_context(request)
    assert context.company.id == company.id
    assert context.role == CompanyRole.OWNER
