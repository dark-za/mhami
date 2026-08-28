from __future__ import annotations

import io
import struct
import zlib
from datetime import datetime, time

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone
from PIL import Image

from apps.organizations.models import CompanyRole
from apps.tasks.services import schedule_due_tasks
from apps.evidence import services as evidence_services


pytestmark = pytest.mark.django_db


def _image_upload(color: str = "red", name: str = "camera.png") -> SimpleUploadedFile:
    image = Image.new("RGB", (128, 128), color=color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def _base_context(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    branch_code: str = "main",
):
    owner = make_user(login_id=f"owner-{branch_code}", display_name="Owner")
    company = make_company(
        name=f"Evidence Co {branch_code}", code=f"evidence-{branch_code}", owner=owner,
    )
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    branch = make_branch(company=company, code=branch_code, name="Main")
    template = make_template(
        company=company, branch=branch,
        slug=f"clean-{branch_code}", name=f"Clean {branch_code}", assigned_user=owner,
    )
    make_template_version(
        template=template,
        instructions="Clean the store",
        evidence_requirements=[{"type": "image"}],
    )
    make_schedule(company=company, branch=branch, template=template, scheduled_time=time(9, 0))
    instance = schedule_due_tasks(moment=timezone.make_aware(datetime(2026, 1, 5, 9, 30)))[0]
    return owner, company, branch, instance


def test_capture_submit_and_reuse_blocked(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    owner, company, branch, instance = _base_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
    )
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    session_response = client.post(
        "/api/v1/evidence/capture-sessions",
        data={"task_instance_id": str(instance.id), "evidence_type": "image"},
        content_type="application/json",
    )
    assert session_response.status_code == 201
    token = session_response.json()["token"]

    submit_response = client.post(
        "/api/v1/evidence/submit",
        data={"capture_token": token, "face_detected": True, "note_text": "front desk", "file": _image_upload("red")},
    )
    assert submit_response.status_code == 201
    payload = submit_response.json()
    assert payload["face_detected"] is True
    assert payload["duplicate_risk_score"] == 0

    session = client.post(
        "/api/v1/evidence/submit",
        data={"capture_token": token, "face_detected": True, "note_text": "retry", "file": _image_upload("red")},
    )
    assert session.status_code == 400


def test_duplicate_risk_is_branch_scoped_and_media_is_private(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
    make_job_role, make_branch_membership,
):
    owner, employee, company, branch_one, branch_two = (
        make_user(login_id="owner-dup", display_name="Owner"),
        make_user(login_id="employee-dup", display_name="Employee"),
        None, None, None,
    )
    company = make_company(name="Evidence Co dup", code="evidence-dup", owner=owner)
    make_membership(user=owner, company=company, role=CompanyRole.OWNER)
    make_membership(user=employee, company=company, role=CompanyRole.EMPLOYEE)
    branch_one = make_branch(company=company, code="a", name="A")
    branch_two = make_branch(company=company, code="b", name="B")
    role = make_job_role(company=company, name="Staff", code="staff")
    make_branch_membership(company=company, user=employee, branch=branch_one, job_role=role)

    for branch, slug in ((branch_one, "clean-a"), (branch_two, "clean-b")):
        template = make_template(
            company=company, branch=branch, slug=slug, name=slug, assigned_user=owner,
        )
        make_template_version(
            template=template,
            instructions="Do work",
            evidence_requirements=[{"type": "image"}],
        )
        make_schedule(company=company, branch=branch, template=template, scheduled_time=time(9, 0))

    instances = schedule_due_tasks(moment=timezone.make_aware(datetime(2026, 1, 5, 9, 30)))
    instance_one = next(instance for instance in instances if instance.branch_id == branch_one.id)
    instance_two = next(instance for instance in instances if instance.branch_id == branch_two.id)

    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    session_one = client.post("/api/v1/evidence/capture-sessions", data={"task_instance_id": str(instance_one.id), "evidence_type": "image"}, content_type="application/json")
    assert session_one.status_code == 201
    token_one = session_one.json()["token"]

    submit_one = client.post(
        "/api/v1/evidence/submit",
        data={"capture_token": token_one, "face_detected": False, "file": _image_upload("blue")},
    )
    assert submit_one.status_code == 201
    evidence_one_id = submit_one.json()["id"]

    session_two = client.post("/api/v1/evidence/capture-sessions", data={"task_instance_id": str(instance_two.id), "evidence_type": "image"}, content_type="application/json")
    assert session_two.status_code == 201
    token_two = session_two.json()["token"]
    submit_two = client.post(
        "/api/v1/evidence/submit",
        data={"capture_token": token_two, "face_detected": False, "file": _image_upload("blue")},
    )
    assert submit_two.status_code == 201
    assert submit_two.json()["duplicate_risk_score"] == 0

    second_session = client.post("/api/v1/evidence/capture-sessions", data={"task_instance_id": str(instance_one.id), "evidence_type": "image"}, content_type="application/json")
    assert second_session.status_code == 201
    third_submit = client.post(
        "/api/v1/evidence/submit",
        data={"capture_token": second_session.json()["token"], "face_detected": False, "file": _image_upload("blue")},
    )
    assert third_submit.status_code == 201
    assert third_submit.json()["duplicate_risk_score"] > 0

    employee_client = Client()
    employee_client.force_login(employee, backend="django.contrib.auth.backends.ModelBackend")
    session = employee_client.session
    session["company_id"] = str(company.id)
    session.save()

    media_denied = employee_client.get(f"/api/v1/evidence/items/{evidence_one_id}/media")
    assert media_denied.status_code == 200

    denied_other_branch = employee_client.get(f"/api/v1/evidence/items/{submit_two.json()['id']}/media")
    assert denied_other_branch.status_code == 400


def test_issue_report_and_discussion(
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    owner, company, branch, instance = _base_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        branch_code="c",
    )
    client = Client()
    client.force_login(owner, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session["company_id"] = str(company.id)
    session.save()

    issue_response = client.post(
        "/api/v1/evidence/issues",
        data={"task_instance_id": str(instance.id), "note": "Need extra supplies"},
        content_type="application/json",
    )
    assert issue_response.status_code == 201
    issue_id = issue_response.json()["id"]

    message_response = client.post(
        f"/api/v1/evidence/issues/{issue_id}/messages",
        data={"task_instance_id": str(instance.id), "issue_report_id": issue_id, "message": "Monitor replied"},
        content_type="application/json",
    )
    assert message_response.status_code == 201

    task_view = client.get(f"/api/v1/evidence/tasks/{instance.id}")
    assert task_view.status_code == 200
    assert len(task_view.json()["issues"]) == 1
    assert len(task_view.json()["messages"]) == 1


def _png_header(width: int, height: int) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data
    ihdr += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    return signature + ihdr + b"\x00\x00\x00\x00IEND\xaeB`\x82"


def test_upload_rejects_multi_extension_and_bomb_dimensions(
    tmp_path, settings,
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    owner, _company, _branch, instance = _base_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        branch_code="unsafe",
    )
    settings.MEDIA_ROOT = tmp_path
    session = evidence_services.create_capture_session(instance, owner, "image")

    with pytest.raises(ValueError, match="single-extension"):
        evidence_services.submit_evidence(
            session_token=session.token,
            user=owner,
            upload=SimpleUploadedFile("photo.png.exe", _png_header(32, 32), content_type="image/png"),
        )

    session = evidence_services.create_capture_session(instance, owner, "image")
    with pytest.raises(ValueError, match="unsafe"):
        evidence_services.submit_evidence(
            session_token=session.token,
            user=owner,
            upload=SimpleUploadedFile("photo.png", _png_header(100_000, 100_000), content_type="image/png"),
        )

    assert not list((tmp_path / "evidence" / "quarantine").iterdir())


def test_quarantine_and_partial_derivative_are_removed_on_processing_failure(
    tmp_path, settings, monkeypatch,
    make_user, make_company, make_membership, make_branch,
    make_template, make_template_version, make_schedule,
):
    owner, _company, _branch, instance = _base_context(
        make_user, make_company, make_membership, make_branch,
        make_template, make_template_version, make_schedule,
        branch_code="cleanup",
    )
    settings.MEDIA_ROOT = tmp_path
    session = evidence_services.create_capture_session(instance, owner, "image")

    def fail_normalization(image, face_detected):
        raise RuntimeError("simulated processing failure")

    monkeypatch.setattr(evidence_services, "_normalize_image", fail_normalization)
    with pytest.raises(RuntimeError, match="simulated"):
        evidence_services.submit_evidence(
            session_token=session.token,
            user=owner,
            upload=_image_upload(name="photo.png"),
        )

    assert not list((tmp_path / "evidence" / "quarantine").iterdir())
    private_dir = tmp_path / "evidence" / "private"
    assert not private_dir.exists() or not list(private_dir.iterdir())
