"""C-06 regression tests: phase exit decision workflow.

The workflow lets a platform administrator sign a binding decision on a
phase exit dossier. Decisions are immutable and signed with an HMAC over
the canonical payload. Revocations create a new decision that supersedes
the previous one.
"""

from __future__ import annotations


import pytest
from django.test import Client

from apps.identity.models import User
from apps.platform_core.models import ExitDecision

pytestmark = pytest.mark.django_db


def _make_platform_admin(login_id: str = "owner-sign") -> User:
    return User.objects.create_user(
        login_id=login_id,
        password="Mha!mi-Test-2026#",
        is_staff=True,
        is_superuser=True,
    )


def test_employee_cannot_sign_exit_decision():
    employee = User.objects.create_user(login_id="emp-sign", password="Mha!mi-Test-2026#")
    client = Client()
    client.force_login(employee, backend="django.contrib.auth.backends.ModelBackend")
    response = client.post(
        "/api/v1/platform/exit-decisions/phase_12",
        data={"decision": "approved", "rationale": "x" * 20},
        content_type="application/json",
    )
    assert response.status_code == 403


def test_platform_admin_can_sign_exit_decision():
    admin = _make_platform_admin()
    client = Client()
    client.force_login(admin, backend="django.contrib.auth.backends.ModelBackend")
    response = client.post(
        "/api/v1/platform/exit-decisions/phase_12",
        data={
            "decision": "approved",
            "rationale": "All gates green and pilot evidence complete.",
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["phase"] == "phase_12"
    assert body["decision"] == "approved"
    assert body["signature_hmac"]
    decision = ExitDecision.objects.get(id=body["id"])
    assert decision.verify_signature() is True


def test_decision_signature_changes_when_rationale_tampered():
    admin = _make_platform_admin("tamper-admin")
    decision = ExitDecision.objects.create(
        phase="phase_12",
        decision="approved",
        rationale="All gates green and pilot evidence complete.",
        signed_by=admin,
    )
    decision.signature_hmac = decision.compute_signature()
    decision.save()
    # Tamper with the rationale and check the signature no longer matches.
    decision.rationale = "Tampered rationale"
    decision.save()
    decision.refresh_from_db()
    assert decision.verify_signature() is False


def test_revocation_creates_superseding_decision():
    admin = _make_platform_admin("revoke-admin")
    first = ExitDecision.objects.create(
        phase="phase_12",
        decision="approved",
        rationale="Initial approval based on the pilot dossier.",
        signed_by=admin,
    )
    first.signature_hmac = first.compute_signature()
    first.save()
    revocation = ExitDecision.objects.create(
        phase="phase_12",
        decision="rejected",
        rationale="Withdrawing approval pending legal review of incident reports.",
        signed_by=admin,
        supersedes=first,
    )
    revocation.signature_hmac = revocation.compute_signature()
    revocation.save()
    assert revocation.supersedes_id == first.id
    # Both decisions remain queryable, but only the most recent is the
    # authoritative one.
    latest = ExitDecision.objects.filter(phase="phase_12").order_by("-signed_at").first()
    assert latest.id == revocation.id
    assert latest.decision == "rejected"


def test_phase12_decision_no_longer_requires_pilot_program():
    admin = _make_platform_admin("p12-admin")
    client = Client()
    client.force_login(admin, backend="django.contrib.auth.backends.ModelBackend")

    # Phase12 no longer requires pilot_program_id — succeeds without it
    response = client.post(
        "/api/v1/platform/exit-decisions/phase12",
        data={"decision": "approved", "rationale": "All gates green and evidence complete."},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    assert response.json()["decision"] == "approved"
