from __future__ import annotations

from datetime import time, timedelta
from types import SimpleNamespace

import pytest
from django.core.cache import cache
from django.test import Client
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from apps.audit.models import AuditEvent
from apps.evidence.services import can_access_media
from apps.identity.models import MfaEnrollment
from apps.identity.models import User
from apps.organizations.models import Branch, CompanyMembership, CompanyRole
from apps.tenancy.api.views import _totp_token
from apps.tenancy.models import Company, CompanyStatus, SupportAuthorization
from apps.tenancy.services import enroll_totp, process_lifecycle_expirations

pytestmark = pytest.mark.django_db


STRICT_THROTTLE_SETTINGS = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.platform_core.errors.platform_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "registration_ip": "2/hour",
        "login_ip": "10/minute",
        "login_account": "2/minute",
        "mfa_user": "2/minute",
    },
}


def _register_payload(code: str = "acme") -> dict[str, object]:
    return {
        "company_name": "Acme",
        "company_code": code,
        "industry": "restaurants_cafes",
        "owner_login_id": "owner",
        "owner_password": "Mha!mi-Test-2026#",
        "owner_display_name": "Owner",
        "contact_email": "owner@example.com",
    }


def test_register_login_and_logout_flow():
    client = Client()
    register_response = client.post("/api/v1/auth/register", data=_register_payload(), content_type="application/json")
    assert register_response.status_code == 201
    login_response = client.post(
        "/api/v1/auth/login",
        data={"company_code": "acme", "login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert login_response.status_code == 200
    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["company"]["code"] == "acme"
    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204


def test_active_company_is_taken_from_the_authorized_session_scope(make_user):
    user = make_user(login_id="multi-company-owner", password="Mha!mi-Test-2026#")
    company_a = Company.objects.create(
        name="Company A",
        code="company-a",
        owner=user,
        trial_ends_at=timezone.now() + timedelta(days=30),
    )
    company_b = Company.objects.create(
        name="Company B",
        code="company-b",
        owner=user,
        trial_ends_at=timezone.now() + timedelta(days=30),
    )
    CompanyMembership.objects.create(company=company_a, user=user, role=CompanyRole.OWNER)
    CompanyMembership.objects.create(company=company_b, user=user, role=CompanyRole.OWNER)
    client = Client()
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company_a.id)
    session.save()

    response_a = client.get("/api/v1/auth/me")
    session = client.session
    session["company_id"] = str(company_b.id)
    session.save()
    response_b = client.get("/api/v1/auth/me")

    assert response_a.status_code == 200
    assert response_a.json()["company"]["id"] == str(company_a.id)
    assert response_b.status_code == 200
    assert response_b.json()["company"]["id"] == str(company_b.id)
    assert len(response_b.json()["memberships"]) == 1


def test_forged_company_session_is_rejected(make_user, make_company, make_membership):
    owner = make_user(login_id="real-owner", password="Mha!mi-Test-2026#")
    attacker = make_user(login_id="tenant-attacker", password="Mha!mi-Test-2026#")
    company = make_company(name="Protected Company", code="protected-company", owner=owner)
    make_membership(user=owner, company=company)
    client = Client()
    client.force_login(attacker, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 403


@override_settings(REST_FRAMEWORK=STRICT_THROTTLE_SETTINGS)
def test_login_is_throttled_by_account_without_revealing_account_existence(make_user, make_company, make_membership):
    cache.clear()
    owner = make_user(login_id="throttled-owner", password="Mha!mi-Test-2026#")
    company = make_company(name="Throttle Company", code="throttle-company", owner=owner)
    make_membership(user=owner, company=company)
    client = Client()
    payload = {
        "company_code": company.code,
        "login_id": owner.login_id,
        "password": "wrong-password",
    }

    first = client.post("/api/v1/auth/login", data=payload, content_type="application/json")
    second = client.post("/api/v1/auth/login", data=payload, content_type="application/json")
    blocked = client.post("/api/v1/auth/login", data=payload, content_type="application/json")
    unknown = Client().post(
        "/api/v1/auth/login",
        data={**payload, "company_code": "unknown-company", "login_id": "unknown-user"},
        content_type="application/json",
        REMOTE_ADDR="198.51.100.10",
    )

    assert first.status_code == 400
    assert second.status_code == 400
    assert blocked.status_code == 429
    assert unknown.status_code == 400


@override_settings(REST_FRAMEWORK=STRICT_THROTTLE_SETTINGS)
def test_registration_and_mfa_verification_are_throttled():
    cache.clear()
    client = Client()
    for index in range(2):
        response = client.post(
            "/api/v1/auth/register",
            data={
                **_register_payload(code=f"limited-{index}"),
                "owner_login_id": f"limited-owner-{index}",
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        client.post("/api/v1/auth/logout")

    blocked_registration = client.post(
        "/api/v1/auth/register",
        data={
            **_register_payload(code="limited-blocked"),
            "owner_login_id": "limited-owner-blocked",
        },
        content_type="application/json",
    )
    assert blocked_registration.status_code == 429

    cache.clear()
    mfa_client = Client()
    mfa_client.post(
        "/api/v1/auth/register",
        data={**_register_payload(code="mfa-limited"), "owner_login_id": "mfa-limited-owner"},
        content_type="application/json",
        REMOTE_ADDR="198.51.100.20",
    )
    enrollment = mfa_client.post(
        "/api/v1/auth/mfa/enroll",
        data={"method_type": "totp", "label": "phone"},
        content_type="application/json",
    ).json()
    invalid_payload = {"enrollment_id": enrollment["id"], "code": "000000"}
    first = mfa_client.post(
        "/api/v1/auth/mfa/verify",
        data=invalid_payload,
        content_type="application/json",
    )
    blocked = mfa_client.post(
        "/api/v1/auth/mfa/verify",
        data=invalid_payload,
        content_type="application/json",
    )

    assert first.status_code == 400
    assert blocked.status_code == 429


def test_registration_rejects_weak_or_common_passwords():
    response = Client().post(
        "/api/v1/auth/register",
        data={**_register_payload(), "owner_password": "password123"},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert not Company.objects.filter(code="acme").exists()


def test_owner_can_create_branch_and_membership():
    client = Client()
    client.post("/api/v1/auth/register", data=_register_payload(), content_type="application/json")
    branch_response = client.post(
        "/api/v1/organizations/branches",
        data={
            "name": "Main",
            "code": "main",
            "timezone": "Asia/Riyadh",
            "operational_day_cutoff": "03:00:00",
        },
        content_type="application/json",
    )
    assert branch_response.status_code == 201
    employee = client.post(
        "/api/v1/auth/company/users",
        data={"login_id": "employee", "password": "Mha!mi-Test-2026#", "display_name": "Emp", "role": "employee"},
        content_type="application/json",
    ).json()["user"]
    role_response = client.post(
        "/api/v1/organizations/job-roles",
        data={"name": "Cashier", "code": "cashier"},
        content_type="application/json",
    )
    assert role_response.status_code == 201
    company = Company.objects.get(code="acme")
    branch = company.branches.get(code="main")
    role = company.job_roles.get(code="cashier")
    branch_membership_response = client.post(
        "/api/v1/auth/company/branch-memberships",
        data={
            "user_id": employee["id"],
            "branch_id": str(branch.id),
            "job_role_id": str(role.id),
            "membership_type": "primary",
        },
        content_type="application/json",
    )
    assert branch_membership_response.status_code == 201


def test_totp_enrollment_and_verification():
    client = Client()
    client.post("/api/v1/auth/register", data=_register_payload(), content_type="application/json")
    enroll_response = client.post(
        "/api/v1/auth/mfa/enroll",
        data={"method_type": "totp", "label": "phone"},
        content_type="application/json",
    )
    assert enroll_response.status_code == 201
    enrollment_id = enroll_response.json()["id"]
    enrollment = MfaEnrollment.objects.get(id=enrollment_id)
    verify_response = client.post(
        "/api/v1/auth/mfa/verify",
        data={"enrollment_id": enrollment_id, "code": _totp_token(enrollment.secret)},
        content_type="application/json",
    )
    assert verify_response.status_code == 200
    assert enroll_response.json()["secret"] == enrollment.secret
    assert "secret" not in verify_response.json()


def test_login_requires_mfa_code_after_totp_verified():
    client = Client()
    client.post("/api/v1/auth/register", data=_register_payload(), content_type="application/json")
    enroll_response = client.post(
        "/api/v1/auth/mfa/enroll",
        data={"method_type": "totp", "label": "phone"},
        content_type="application/json",
    )
    assert enroll_response.status_code == 201
    enrollment = MfaEnrollment.objects.get(id=enroll_response.json()["id"])
    with freeze_time("2020-01-01 00:00:00"):
        verify_response = client.post(
            "/api/v1/auth/mfa/verify",
            data={"enrollment_id": enrollment.id, "code": _totp_token(enrollment.secret)},
            content_type="application/json",
        )
    assert verify_response.status_code == 200

    denied = client.post(
        "/api/v1/auth/login",
        data={"company_code": "acme", "login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert denied.status_code == 400

    accepted = client.post(
        "/api/v1/auth/login",
        data={"company_code": "acme", "login_id": "owner", "password": "Mha!mi-Test-2026#", "mfa_code": _totp_token(enrollment.secret)},
        content_type="application/json",
    )
    assert accepted.status_code == 200
    client.post("/api/v1/auth/logout")


def test_totp_verification_code_cannot_be_reused_for_login():
    client = Client()
    client.post("/api/v1/auth/register", data=_register_payload(), content_type="application/json")
    enrollment = enroll_totp(User.objects.get(login_id="owner"), label="verification-replay-test")
    code = _totp_token(enrollment.secret)

    verify_response = client.post(
        "/api/v1/auth/mfa/verify",
        data={"enrollment_id": enrollment.id, "code": code},
        content_type="application/json",
    )
    client.post("/api/v1/auth/logout")
    replay = client.post(
        "/api/v1/auth/login",
        data={
            "company_code": "acme",
            "login_id": "owner",
            "password": "Mha!mi-Test-2026#",
            "mfa_code": code,
        },
        content_type="application/json",
    )

    assert verify_response.status_code == 200
    assert replay.status_code == 400


def test_totp_code_cannot_be_replayed_for_a_second_login():
    client = Client()
    client.post("/api/v1/auth/register", data=_register_payload(), content_type="application/json")
    enrollment = enroll_totp(User.objects.get(login_id="owner"), label="replay-test")
    enrollment.verified_at = timezone.now()
    enrollment.save(update_fields=["verified_at"])
    code = _totp_token(enrollment.secret)
    client.post("/api/v1/auth/logout")

    first = client.post(
        "/api/v1/auth/login",
        data={
            "company_code": "acme",
            "login_id": "owner",
            "password": "Mha!mi-Test-2026#",
            "mfa_code": code,
        },
        content_type="application/json",
    )
    client.post("/api/v1/auth/logout")
    replay = client.post(
        "/api/v1/auth/login",
        data={
            "company_code": "acme",
            "login_id": "owner",
            "password": "Mha!mi-Test-2026#",
            "mfa_code": code,
        },
        content_type="application/json",
    )

    assert first.status_code == 200
    assert replay.status_code == 400


def test_unimplemented_passkey_enrollment_is_rejected_without_creating_a_record():
    client = Client()
    client.post("/api/v1/auth/register", data=_register_payload(), content_type="application/json")

    response = client.post(
        "/api/v1/auth/mfa/enroll",
        data={"method_type": "passkey", "label": "unsupported"},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert not MfaEnrollment.objects.filter(method_type="passkey").exists()


def test_expired_trial_is_read_only_then_pending_deletion_and_blocks_writes():
    client = Client()
    client.post("/api/v1/auth/register", data=_register_payload(), content_type="application/json")
    company = Company.objects.get(code="acme")
    now = timezone.now()
    company.trial_ends_at = now - timedelta(seconds=1)
    company.save(update_fields=["trial_ends_at"])

    assert process_lifecycle_expirations(at=now, dry_run=True) == {
        "read_only": 1,
        "pending_deletion": 0,
        "support_expired": 0,
    }
    process_lifecycle_expirations(at=now)
    company.refresh_from_db()
    assert company.status == CompanyStatus.READ_ONLY
    assert company.read_only_until == now + timedelta(days=90)
    assert company.deletion_due_at == company.read_only_until
    assert client.get("/api/v1/auth/me").json()["company"]["read_only_until"] is not None

    read_response = client.get("/api/v1/organizations/branches")
    write_response = client.post(
        "/api/v1/organizations/branches",
        data={
            "name": "Blocked",
            "code": "blocked",
            "timezone": "Asia/Riyadh",
            "operational_day_cutoff": "03:00:00",
        },
        content_type="application/json",
    )
    assert read_response.status_code == 200
    assert write_response.status_code == 400

    process_lifecycle_expirations(at=now + timedelta(days=90))
    company.refresh_from_db()
    assert company.status == CompanyStatus.PENDING_DELETION
    assert AuditEvent.objects.filter(event_type="COMPANY_LIFECYCLE_TRANSITIONED", target_id=str(company.id)).count() == 2


def test_support_grant_is_scoped_audited_expiring_and_revocable(make_user):
    owner_client = Client()
    owner_client.post("/api/v1/auth/register", data=_register_payload(), content_type="application/json")
    company = Company.objects.get(code="acme")
    support = make_user(login_id="support", password="supportpass")
    enrollment = enroll_totp(support, label="support-test")
    enrollment.verified_at = timezone.now()
    enrollment.save(update_fields=["verified_at"])
    expires_at = timezone.now() + timedelta(hours=1)
    grant_response = owner_client.post(
        "/api/v1/auth/company/support",
        data={
            "support_user_id": str(support.id),
            "reason": "Investigate export request",
            "expires_at": expires_at.isoformat(),
        },
        content_type="application/json",
    )
    assert grant_response.status_code == 201
    grant_id = grant_response.json()["id"]
    enrollment.verified_at = None
    enrollment.save(update_fields=["verified_at"])
    denied_without_mfa = Client().post(
        "/api/v1/auth/login",
        data={"company_code": "acme", "login_id": "support", "password": "supportpass"},
        content_type="application/json",
    )
    assert denied_without_mfa.status_code == 400
    enrollment.verified_at = timezone.now()
    enrollment.save(update_fields=["verified_at"])
    support_client = Client()
    login_response = support_client.post(
        "/api/v1/auth/login",
        data={
            "company_code": "acme",
            "login_id": "support",
            "password": "supportpass",
            "mfa_code": _totp_token(enrollment.secret),
        },
        content_type="application/json",
    )
    assert login_response.status_code == 200
    assert AuditEvent.objects.filter(event_type="SUPPORT_ACCESS_GRANTED", target_id=grant_id).exists()
    assert AuditEvent.objects.filter(event_type="SUPPORT_ACCESS_USED", target_id=grant_id).exists()

    branch = Branch.objects.create(
        company=company,
        name="Private",
        code="private",
        operational_day_cutoff=time(3),
    )
    assert can_access_media(
        support,
        SimpleNamespace(submitted_by_id=company.owner_id, company=company, branch=branch),
    ) is False

    other_owner = make_user(login_id="other-owner", password="Mha!mi-Test-2026#")
    other_company = Company.objects.create(
        name="Other",
        code="other",
        owner=other_owner,
        trial_ends_at=timezone.now() + timedelta(days=30),
    )
    denied_other_tenant = Client().post(
        "/api/v1/auth/login",
        data={
            "company_code": other_company.code,
            "login_id": "support",
            "password": "supportpass",
            "mfa_code": _totp_token(enrollment.secret),
        },
        content_type="application/json",
    )
    assert denied_other_tenant.status_code == 400

    revoke_response = owner_client.delete(
        "/api/v1/auth/company/support",
        data={"support_user_id": str(support.id)},
        content_type="application/json",
    )
    assert revoke_response.status_code == 204
    assert AuditEvent.objects.filter(event_type="SUPPORT_ACCESS_REVOKED", target_id=grant_id).exists()
    denied_revoked = Client().post(
        "/api/v1/auth/login",
        data={
            "company_code": "acme",
            "login_id": "support",
            "password": "supportpass",
            "mfa_code": _totp_token(enrollment.secret),
        },
        content_type="application/json",
    )
    assert denied_revoked.status_code == 400

    expiring_response = owner_client.post(
        "/api/v1/auth/company/support",
        data={
            "support_user_id": str(support.id),
            "reason": "Temporary diagnostic session",
            "expires_at": (timezone.now() + timedelta(hours=1)).isoformat(),
        },
        content_type="application/json",
    )
    assert expiring_response.status_code == 201
    expiring_grant_id = expiring_response.json()["id"]
    SupportAuthorization.objects.filter(id=expiring_grant_id).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    denied_expired = Client().post(
        "/api/v1/auth/login",
        data={
            "company_code": "acme",
            "login_id": "support",
            "password": "supportpass",
            "mfa_code": _totp_token(enrollment.secret),
        },
        content_type="application/json",
    )
    assert denied_expired.status_code == 400
    assert process_lifecycle_expirations()["support_expired"] == 1
    assert SupportAuthorization.objects.get(id=expiring_grant_id).active is False
    assert AuditEvent.objects.filter(event_type="SUPPORT_ACCESS_EXPIRED", target_id=expiring_grant_id).exists()
