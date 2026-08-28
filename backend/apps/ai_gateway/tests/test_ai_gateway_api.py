from __future__ import annotations

import hashlib
from datetime import datetime, time

import pytest
from django.test import Client
from django.utils import timezone

from apps.ai_gateway.models import AIAnalysisRun, AIAnalysisStatus
from apps.connector_control.services import enroll_connector
from apps.evidence.models import EvidenceStatus, EvidenceType
from apps.organizations.models import CompanyRole
from apps.tasks.services import schedule_due_tasks


pytestmark = pytest.mark.django_db


def _context(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_capture_session, make_evidence_item,
):
    """Build owner+monitor with one branch, one scheduled task, one submitted image evidence."""
    owner = make_user(login_id="ai-owner", display_name="Owner")
    monitor = make_user(login_id="ai-monitor", display_name="Monitor")
    company = make_company(name="AI Co", code="ai-co", industry="other", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=monitor, company=company, role=CompanyRole.MONITOR)
    branch = make_branch(company=company, code="main", name="Main")
    template = make_template(
        company=company, branch=branch, slug="daily", name="Daily", assigned_user=owner,
    )
    make_template_version(
        template=template,
        instructions="Do work",
        evidence_requirements=[{"type": "image"}],
    )
    make_schedule(company=company, branch=branch, template=template, scheduled_time=time(9, 0))
    instance = schedule_due_tasks(moment=timezone.make_aware(datetime(2026, 1, 5, 9, 30)))[0]
    capture = make_capture_session(
        company=company, branch=branch, task_instance=instance, created_by=owner,
        token="token-123", expires_at=timezone.make_aware(datetime(2026, 1, 5, 10, 0)),
    )
    evidence = make_evidence_item(
        company=company, branch=branch, task_instance=instance,
        capture_session=capture, submitted_by=owner, evidence_type=EvidenceType.IMAGE,
    )
    evidence.status = EvidenceStatus.SUBMITTED
    evidence.duplicate_risk_score = 15
    evidence.face_detected = False
    evidence.save(update_fields=["status", "duplicate_risk_score", "face_detected", "updated_at"])
    return owner, monitor, company, evidence


def test_ai_provider_and_criteria_and_analysis(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_capture_session, make_evidence_item,
):
    owner, _monitor, company, evidence = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        make_capture_session, make_evidence_item,
    )
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    provider = client.patch("/api/v1/ai/provider", data={"provider_name": "fake", "model_name": "demo"}, content_type="application/json")
    assert provider.status_code == 200

    criteria = client.post("/api/v1/ai/criteria", data={"title": "Face blur", "criteria_json": {"auto_pass_risk_threshold": 60}}, content_type="application/json")
    assert criteria.status_code == 201

    run = client.post("/api/v1/ai/analysis", data={"evidence_item_id": str(evidence.id)}, content_type="application/json")
    assert run.status_code == 201
    assert run.json()["status"] in {AIAnalysisStatus.COMPLETED, AIAnalysisStatus.NEEDS_REVIEW}
    assert run.json()["review_decision"] is None
    assert run.json()["agreement_with_human"] is None

    decision = client.post(
        "/api/v1/reviews/decisions",
        data={"decision_type": "approve", "evidence_item_id": str(evidence.id), "reason": "Reviewed"},
        content_type="application/json",
    )
    assert decision.status_code == 201
    analysis = AIAnalysisRun.objects.get(id=run.json()["id"])
    assert str(analysis.review_decision_id) == decision.json()["id"]
    assert analysis.human_decision == "approve"
    assert analysis.agreement_with_human is True

    summary = client.get("/api/v1/ai/shadow")
    assert summary.json()["summary"]["human_reviewed_runs"] == 1
    assert summary.json()["summary"]["compared_runs"] == 1
    assert summary.json()["summary"]["agreement_rate"] == 100.0


def test_ai_shadow_mode_rejects_auto_pass_and_never_activates_it(
    monkeypatch,
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_capture_session, make_evidence_item,
):
    owner, _monitor, company, evidence = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        make_capture_session, make_evidence_item,
    )
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    rejected = client.post(
        "/api/v1/ai/criteria",
        data={"title": "Unsafe", "shadow_mode": False, "auto_pass_enabled": True},
        content_type="application/json",
    )
    assert rejected.status_code == 400

    criteria = client.post(
        "/api/v1/ai/criteria",
        data={"title": "Shadow only"},
        content_type="application/json",
    )
    assert criteria.status_code == 201

    class EligibleProvider:
        def analyze(self, **_kwargs):
            return {
                "verdict": "approve",
                "risk_level": "low",
                "confidence": 100,
                "explanation": "Eligible but still shadowed.",
                "auto_pass_eligible": True,
            }

    monkeypatch.setattr("apps.ai_gateway.services._provider_for", lambda _config: EligibleProvider())
    run = client.post("/api/v1/ai/analysis", data={"evidence_item_id": str(evidence.id)}, content_type="application/json")
    assert run.status_code == 201
    assert run.json()["shadow_mode"] is True
    assert run.json()["auto_pass_eligible"] is True
    assert run.json()["auto_pass_activated"] is False


def test_provider_and_offline_connector_failure_leave_evidence_usable(
    monkeypatch,
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_capture_session, make_evidence_item,
):
    owner, _monitor, company, evidence = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        make_capture_session, make_evidence_item,
    )
    enroll_connector(company, owner, "1.0.0", hashlib.sha256(b"offline-secret").hexdigest())
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()
    criteria = client.post("/api/v1/ai/criteria", data={"title": "Failure test"}, content_type="application/json")
    assert criteria.status_code == 201

    class FailingProvider:
        def analyze(self, **_kwargs):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr("apps.ai_gateway.services._provider_for", lambda _config: FailingProvider())
    run = client.post("/api/v1/ai/analysis", data={"evidence_item_id": str(evidence.id)}, content_type="application/json")
    assert run.status_code == 201
    assert run.json()["status"] == AIAnalysisStatus.FAILED
    evidence.refresh_from_db()
    assert evidence.status == EvidenceStatus.SUBMITTED


def test_connector_shadow_summary_visible(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_capture_session, make_evidence_item,
):
    _owner, monitor, company, _evidence = _context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        make_capture_session, make_evidence_item,
    )
    client = Client()
    client.force_login(monitor, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    summary = client.get("/api/v1/ai/shadow")
    assert summary.status_code == 200
