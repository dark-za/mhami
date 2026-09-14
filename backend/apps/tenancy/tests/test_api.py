from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client
from django.test import override_settings
from django.utils import timezone
from apps.audit.models import AuditEvent
from apps.identity.models import User
from apps.organizations.models import CompanyMembership, CompanyRole
from apps.tenancy.models import Company, CompanyStatus, InstallationState
from apps.tenancy.services import initial_setup_required

pytestmark = pytest.mark.django_db


STRICT_THROTTLE_SETTINGS = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.platform_core.errors.platform_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "registration_ip": "2/hour",
        "login_ip": "10/minute",
        "login_account": "2/minute",
    },
}


@pytest.fixture(autouse=True)
def _clear_auth_throttle_cache():
    cache.clear()
    yield
    cache.clear()


def _provision_owner(
    company_name: str = "Acme",
    owner_login_id: str = "owner",
    owner_display_name: str = "Owner",
    password: str = "Mha!mi-Test-2026#",
) -> Company:
    call_command(
        "provision_owner",
        organization_name=company_name,
        owner_login_id=owner_login_id,
        owner_display_name=owner_display_name,
        password=password,
    )
    return Company.objects.get()


def test_provision_owner_creates_sole_organization_and_owner_membership():
    company = _provision_owner()
    assert Company.objects.count() == 1
    assert company.name == "Acme"
    assert company.status == CompanyStatus.ACTIVE
    owner = User.objects.get(login_id="owner")
    assert CompanyMembership.objects.filter(company=company, user=owner, role=CompanyRole.OWNER, active=True).exists()
    assert company.owner_id == owner.id
    assert InstallationState.objects.get(pk=1).is_configured is True


def test_provision_owner_fails_if_any_organization_already_exists():
    _provision_owner()
    with pytest.raises(CommandError, match="already exists"):
        call_command(
            "provision_owner",
            organization_name="Second",
            owner_login_id="owner2",
            owner_display_name="Owner2",
            password="Mha!mi-Test-2026#",
        )
    assert Company.objects.count() == 1


def test_provision_owner_never_replaces_data_or_creates_second_org():
    _provision_owner(company_name="First", owner_login_id="owner1", password="Mha!mi-Test-2026#")
    first_id = Company.objects.get().id
    try:
        call_command(
            "provision_owner",
            organization_name="Second",
            owner_login_id="owner2",
            owner_display_name="Owner2",
            password="Mha!mi-Test-2026#",
        )
    except CommandError:
        pass
    assert Company.objects.count() == 1
    assert Company.objects.get().id == first_id
    assert not User.objects.filter(login_id="owner2").exists()


def test_register_endpoint_is_absent():
    client = Client()
    response = client.post("/api/v1/auth/register", data={}, content_type="application/json")
    assert response.status_code == 404


def _csrf_client() -> Client:
    client = Client(enforce_csrf_checks=True)
    response = client.get("/api/v1/bootstrap")
    assert response.status_code == 200
    return client


def _setup_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "organization_name": "Browser Setup Organization",
        "owner_login_id": "browser-owner",
        "owner_display_name": "Browser Owner",
        "password": "Mha!mi-Test-2026#",
        "setup_token": "setup-token-for-tests-2026",
    }
    payload.update(overrides)
    return payload


def test_bootstrap_reports_first_setup_without_disclosing_configuration():
    response = Client().get("/api/v1/bootstrap")
    assert response.status_code == 200
    assert response.json()["installation"] == {"setup_required": True}
    assert "setup_token" not in response.content.decode()


def test_browser_setup_never_reopens_after_a_configured_installation_is_damaged():
    state = InstallationState.objects.get(pk=1)
    state.configured_at = timezone.now()
    state.save(update_fields=["configured_at"])
    assert initial_setup_required() is False


@override_settings(INITIAL_SETUP_TOKEN="setup-token-for-tests-2026")
def test_browser_setup_requires_csrf_and_the_server_setup_token():
    client = Client(enforce_csrf_checks=True)
    blocked = client.post(
        "/api/v1/setup/initialize",
        data=_setup_payload(),
        content_type="application/json",
    )
    assert blocked.status_code == 403
    assert Company.objects.count() == 0

    client = _csrf_client()
    invalid = client.post(
        "/api/v1/setup/initialize",
        data=_setup_payload(setup_token="wrong-setup-token-2026"),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert invalid.status_code == 400
    assert Company.objects.count() == 0


@override_settings(INITIAL_SETUP_TOKEN="setup-token-for-tests-2026")
@pytest.mark.parametrize("missing_state", [False, True])
def test_browser_setup_creates_owner_logs_in_and_closes_permanently(missing_state):
    if missing_state:
        User.objects.all().delete()
        AuditEvent.objects.all().delete()
        InstallationState.objects.all().delete()
    assert initial_setup_required() is True
    client = _csrf_client()
    response = client.post(
        "/api/v1/setup/initialize",
        data=_setup_payload(),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert response.status_code == 201
    assert Company.objects.count() == 1
    assert InstallationState.objects.get(pk=1).is_configured is True
    assert response.json()["user"]["login_id"] == "browser-owner"
    assert client.get("/api/v1/auth/me").status_code == 200
    assert AuditEvent.objects.filter(event_type="INSTALLATION_INITIALIZED").exists()

    second = client.post(
        "/api/v1/setup/initialize",
        data=_setup_payload(owner_login_id="second-owner"),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert second.status_code == 400
    assert Company.objects.count() == 1
    assert not User.objects.filter(login_id="second-owner").exists()


@pytest.mark.parametrize("retained_data", ["user", "audit"])
def test_missing_installation_state_with_retained_data_fails_closed(retained_data):
    InstallationState.objects.all().delete()
    if retained_data == "user":
        User.objects.create_user(login_id="retained-user", password="Mha!mi-Test-2026#")
    else:
        from apps.audit.services import record_audit_event

        record_audit_event(event_type="INSTALLATION_INITIALIZED", target_type="company", target_id="former-company")
    assert initial_setup_required() is False
    with pytest.raises(CommandError, match="operator recovery"):
        _provision_owner()
    assert not Company.objects.exists()
    assert not InstallationState.objects.exists()


def test_mfa_endpoints_are_absent():
    client = Client()
    assert client.post("/api/v1/auth/mfa/enroll", data={}, content_type="application/json").status_code == 404
    assert client.post("/api/v1/auth/mfa/verify", data={}, content_type="application/json").status_code == 404


def test_login_and_logout_flow_with_local_credentials():
    _provision_owner()
    client = Client()
    login_response = client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert login_response.status_code == 200
    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["company"]["code"] == "acme"
    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204


def test_login_uses_only_login_id_and_password():
    _provision_owner()
    client = Client()
    # Valid login without company_code
    response = client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert response.status_code == 200
    # Retired company_code field is rejected with 400 validation error
    client.post("/api/v1/auth/logout")
    response2 = client.post(
        "/api/v1/auth/login",
        data={"company_code": "ignored", "login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert response2.status_code == 400
    assert "company_code" in response2.content.decode()
    mfa_response = client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#", "mfa_code": "123456"},
        content_type="application/json",
    )
    assert mfa_response.status_code == 400
    assert "mfa_code" in mfa_response.content.decode()


def test_disabled_user_cannot_login_with_valid_password():
    company = _provision_owner()
    owner = company.owner
    owner.is_active = False
    owner.save(update_fields=["is_active"])
    response = Client().post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert not AuditEvent.objects.filter(event_type="USER_LOGIN").exists()


def test_authentication_backend_does_not_restore_disabled_user():
    from apps.tenancy.auth_backends import LocalInstallationBackend

    company = _provision_owner()
    owner = company.owner
    backend = LocalInstallationBackend()
    assert backend.get_user(owner.id) == owner
    owner.is_active = False
    owner.save(update_fields=["is_active"])
    assert backend.get_user(owner.id) is None


def test_cli_password_with_surrounding_spaces_logs_in_without_normalization():
    password = "  Mha!mi-Test-2026#  "
    _provision_owner(password=password)
    client = Client()
    response = client.post(
        "/api/v1/auth/login", data={"login_id": "owner", "password": password}, content_type="application/json",
    )
    assert response.status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 204
    rejected = client.post(
        "/api/v1/auth/login", data={"login_id": "owner", "password": password.strip()}, content_type="application/json",
    )
    assert rejected.status_code == 400


@override_settings(INITIAL_SETUP_TOKEN="setup-token-for-tests-2026")
def test_browser_setup_preserves_password_exactly():
    password = "  Mha!mi-Test-2026#  "
    client = _csrf_client()
    response = client.post(
        "/api/v1/setup/initialize", data=_setup_payload(password=password), content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert response.status_code == 201
    owner = User.objects.get(login_id="browser-owner")
    assert owner.check_password(password)
    assert not owner.check_password(password.strip())


def test_member_creation_preserves_password_exactly():
    company = _provision_owner()
    client = Client()
    client.force_login(company.owner, backend="apps.tenancy.auth_backends.LocalInstallationBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()
    password = "  Mha!mi-Test-2026#  "
    response = client.post(
        "/api/v1/auth/company/users",
        data={"login_id": "new-employee", "password": password, "role": "employee"},
        content_type="application/json",
    )
    assert response.status_code == 201
    user = User.objects.get(login_id="new-employee")
    assert user.check_password(password)
    assert not user.check_password(password.strip())


@pytest.mark.parametrize("protection", ["missing", "wrong_token", "foreign_origin", "valid"])
def test_login_enforces_csrf_before_creating_a_session(protection):
    _provision_owner()
    client = Client(enforce_csrf_checks=True)
    headers = {}
    if protection != "missing":
        assert client.get("/api/v1/bootstrap").status_code == 200
        csrf_token = client.cookies["csrftoken"].value
        headers["HTTP_X_CSRFTOKEN"] = "x" * 32 if protection == "wrong_token" else csrf_token
    if protection == "foreign_origin":
        headers["HTTP_ORIGIN"] = "https://untrusted.invalid"
    response = client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
        **headers,
    )
    if protection == "valid":
        assert response.status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 200
        assert client.cookies["csrftoken"].value != csrf_token
    else:
        assert response.status_code == 403
        assert "_auth_user_id" not in client.session
        assert not AuditEvent.objects.filter(event_type="USER_LOGIN").exists()


@pytest.mark.parametrize("termination", ["expired", "logout"])
def test_terminated_session_rejects_another_client_and_bootstrap_is_anonymous(termination):
    from django.contrib.sessions.models import Session

    _provision_owner()
    first = Client()
    signed_in = first.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert signed_in.status_code == 200
    other_tab = Client()
    other_tab.cookies.update(first.cookies)
    assert other_tab.get("/api/v1/auth/me").status_code == 200
    if termination == "expired":
        Session.objects.filter(session_key=first.session.session_key).update(
            expire_date=timezone.now() - timedelta(seconds=1)
        )
    else:
        assert first.post("/api/v1/auth/logout").status_code == 204
    denied = other_tab.get("/api/v1/auth/me")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "NOT_AUTHENTICATED"
    bootstrap = other_tab.get("/api/v1/bootstrap").json()
    assert bootstrap["current_user"]["is_authenticated"] is False
    assert bootstrap["company"] is None
    assert bootstrap["permissions"] == []


def test_login_fails_closed_if_no_organization():
    client = Client()
    response = client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert AuditEvent.objects.filter(event_type="LOGIN_FAILED", metadata__reason="no_organization").exists()


def test_login_fails_closed_if_multiple_organizations(make_user):
    _provision_owner()
    # Forge second company directly (simulating corrupted state)
    other_owner = make_user(login_id="other-owner", password="Mha!mi-Test-2026#")
    Company.objects.create(
        name="Other",
        code="other",
        owner=other_owner,
        status=CompanyStatus.ACTIVE,
    )
    client = Client()
    response = client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_login_fails_for_inactive_organization():
    company = _provision_owner()
    company.status = CompanyStatus.SUSPENDED
    company.save(update_fields=["status"])
    client = Client()
    response = client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_login_fails_for_unknown_user_bad_password_and_no_membership(make_user):
    _provision_owner()
    client = Client()
    unknown = client.post(
        "/api/v1/auth/login",
        data={"login_id": "ghost", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert unknown.status_code == 400
    bad = client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "wrong-password-long-enough"},
        content_type="application/json",
    )
    assert bad.status_code == 400
    make_user(login_id="outsider", password="Mha!mi-Test-2026#")
    outsider_no_membership = client.post(
        "/api/v1/auth/login",
        data={"login_id": "outsider", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert outsider_no_membership.status_code == 400


def test_forged_company_session_is_rejected(make_user, make_company, make_membership):
    _provision_owner()
    sole = Company.objects.get()
    # Ensure owner already has membership; attacker is not member of sole org
    attacker = make_user(login_id="tenant-attacker", password="Mha!mi-Test-2026#")
    client = Client()
    client.force_login(attacker, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(sole.id)
    session.save()

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 403


@override_settings(REST_FRAMEWORK=STRICT_THROTTLE_SETTINGS)
def test_login_is_throttled_by_account_without_revealing_account_existence(make_user):
    cache.clear()
    _provision_owner()
    owner = User.objects.get(login_id="owner")
    client = Client()
    payload = {
        "login_id": owner.login_id,
        "password": "wrong-password",
    }

    first = client.post("/api/v1/auth/login", data=payload, content_type="application/json")
    second = client.post("/api/v1/auth/login", data=payload, content_type="application/json")
    blocked = client.post("/api/v1/auth/login", data=payload, content_type="application/json")
    unknown = Client().post(
        "/api/v1/auth/login",
        data={"login_id": "unknown-user", "password": "wrong-password"},
        content_type="application/json",
        REMOTE_ADDR="198.51.100.10",
    )

    assert first.status_code == 400
    assert second.status_code == 400
    assert blocked.status_code == 429
    assert unknown.status_code == 400


def test_owner_can_create_branch_and_membership():
    _provision_owner()
    client = Client()
    client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
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
    company = Company.objects.get()
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


def test_suspended_company_blocks_writes_and_login():
    company = _provision_owner()
    company.status = CompanyStatus.SUSPENDED
    company.save(update_fields=["status"])
    client = Client()
    # Login must fail for suspended company
    login_response = client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert login_response.status_code == 400
    # ensure_company_operational also blocks mutations
    from apps.tenancy.services import ensure_company_operational

    with pytest.raises(ValueError, match="read-only"):
        ensure_company_operational(company)
    # is_operational is False for suspended
    assert company.is_operational() is False
    # company serializer exposes suspended_at (may be None) but no trial fields
    from apps.tenancy.serializers import CompanySerializer

    data = CompanySerializer(company).data
    assert "trial_ends_at" not in data
    assert "read_only_until" not in data
    assert "deletion_due_at" not in data
    assert "suspended_at" in data


def test_no_support_endpoints_or_login_capability(make_user):
    _provision_owner()
    client = Client()
    client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    support_user = make_user(login_id="support", password="SupportPass123!")
    grant_response = client.post(
        "/api/v1/auth/company/support",
        data={
            "support_user_id": str(support_user.id),
            "reason": "Investigate",
            "expires_at": (timezone.now() + timedelta(hours=1)).isoformat(),
        },
        content_type="application/json",
    )
    assert grant_response.status_code == 404
    delete_response = client.delete(
        "/api/v1/auth/company/support",
        data={"support_user_id": str(support_user.id)},
        content_type="application/json",
    )
    assert delete_response.status_code == 404

    denied = Client().post(
        "/api/v1/auth/login",
        data={"login_id": "support", "password": "SupportPass123!"},
        content_type="application/json",
    )
    assert denied.status_code == 400
    assert not AuditEvent.objects.filter(event_type="SUPPORT_ACCESS_USED").exists()


def test_login_does_not_emit_support_access_used_audit():
    _provision_owner()
    client = Client()
    client.post(
        "/api/v1/auth/login",
        data={"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert AuditEvent.objects.filter(event_type="USER_LOGIN").exists()
    assert not AuditEvent.objects.filter(event_type="SUPPORT_ACCESS_USED").exists()


def test_tenant_context_has_no_support_attribute(make_user):
    from apps.tenancy.access import TenantContext
    from apps.tenancy.models import Company

    user = make_user()
    company = Company.objects.create(
        name="TenantCheck",
        code="tenant-check",
        owner=user,
        status=CompanyStatus.ACTIVE,
    )
    ctx = TenantContext(company=company, role="owner", branch_ids=frozenset())
    assert not hasattr(ctx, "is_support")
