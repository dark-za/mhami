from __future__ import annotations

import hashlib
import io
import secrets
import warnings
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

try:
    import magic  # type: ignore
except Exception:  # pragma: no cover
    magic_module: Any | None = None
else:
    magic_module = magic

import imagehash
from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import Max
from django.http import FileResponse
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.identity.models import User
from apps.organizations.models import Branch, CompanyMembership, CompanyRole, UserBranchMembership
from apps.platform_core.service_base import audited_service
from apps.tasks.models import TaskInstance
from apps.tenancy.models import Company

from .models import (
    CaptureSession,
    CaptureSessionStatus,
    EvidenceItem,
    EvidenceType,
    TaskDiscussionMessage,
    TaskIssueReport,
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_SIDE = 2048
MAX_SOURCE_PIXELS = 16 * 1024 * 1024
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
CHALLENGE_TEXT = "Hold two fingers up and say the task code aloud."


def evidence_storage_root() -> Path:
    root = Path(settings.MEDIA_ROOT) / "evidence"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _subdir(name: str) -> Path:
    path = evidence_storage_root() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _quarantine_name(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower() or ".bin"
    return f"{secrets.token_hex(16)}{suffix}"


def _private_name() -> str:
    return f"{secrets.token_hex(24)}.webp"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _detect_mime(data: bytes, file_name: str) -> str:
    if magic_module is not None:
        try:
            return magic_module.from_buffer(data, mime=True)
        except Exception:
            pass
    suffix = Path(file_name).suffix.lower()
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(
        suffix,
        "application/octet-stream",
    )


def _branch_accessible_branch_ids(company: Company, user: User) -> set[str]:
    membership = CompanyMembership.objects.filter(company=company, user=user, active=True).first()
    if membership and membership.role in {CompanyRole.OWNER, CompanyRole.MONITOR}:
        return set(str(branch_id) for branch_id in company.branches.values_list("id", flat=True))
    return set(str(branch_id) for branch_id in UserBranchMembership.objects.filter(company=company, user=user, active=True).values_list("branch_id", flat=True))


def assert_capture_access(company: Company, branch: Branch, user: User) -> None:
    if branch.company_id != company.id:
        raise ValueError("Branch does not belong to company.")
    if str(branch.id) not in _branch_accessible_branch_ids(company, user):
        raise ValueError("User cannot access this branch.")


@audited_service(event_type="EVIDENCE_CAPTURE_SESSION_CREATED", target_type="capture_session")
def create_capture_session(task_instance: TaskInstance, user: User, evidence_type: str, challenge_answer: str = "") -> CaptureSession:
    company = task_instance.company
    branch = task_instance.branch
    assert_capture_access(company, branch, user)
    version = task_instance.template_version
    token = secrets.token_urlsafe(32)
    session = CaptureSession.objects.create(
        company=company,
        branch=branch,
        task_instance=task_instance,
        template_version=version,
        created_by=user,
        evidence_type=evidence_type,
        token=token,
        challenge_text=CHALLENGE_TEXT if task_instance.template.risk_level == "high" else "",
        challenge_answer=challenge_answer,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    return session


def _open_image(data: bytes) -> Image.Image:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as candidate:
                if candidate.width * candidate.height > MAX_SOURCE_PIXELS:
                    raise ValueError("Image dimensions exceed the platform safety limit.")
                candidate.verify()
            pil_image = cast(Image.Image, Image.open(io.BytesIO(data)))
            if pil_image.width * pil_image.height > MAX_SOURCE_PIXELS:
                pil_image.close()
                raise ValueError("Image dimensions exceed the platform safety limit.")
            transposed = ImageOps.exif_transpose(pil_image)
            if transposed is not None and transposed is not pil_image:
                pil_image.close()
                pil_image = transposed
            pil_image.load()
            return pil_image
    except (Image.DecompressionBombError, Image.DecompressionBombWarning, UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("Unsupported or unsafe image file.") from exc


def _normalize_image(image: Image.Image, server_face_detected: bool) -> Image.Image:
    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGB")
    elif image.mode == "RGBA":
        image = image.convert("RGB")
    max_side = max(image.size)
    if max_side > MAX_IMAGE_SIDE:
        scale = MAX_IMAGE_SIDE / max_side
        image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
    # C-13: the server is the only authority on whether an image is
    # blurred. The client flag is recorded in ``face_detected`` for
    # diagnostics, but the actual blur is driven by the server's own
    # face-detection result.
    if server_face_detected:
        image = image.filter(ImageFilter.GaussianBlur(radius=18))
    return image


# C-13: deterministic, dependency-free face heuristic. The platform's
# privacy stance is "blur when a face-sized region with skin-tone
# statistics is present". The heuristic is intentionally conservative
# (false positives trigger a blur, false negatives are reviewed by a
# monitor). The detector version is recorded in audit metadata so the
# pipeline can be re-evaluated when the heuristic is upgraded.
FACE_DETECTOR_VERSION = "skin-region-v1"


def _server_detect_face(image: Image.Image) -> dict[str, object]:
    """Run the bundled face detector and return a structured result.

    The result is recorded in ``EvidenceItem.face_detector_raw_score``
    and ``face_detector_confidence``. The boolean return is what the
    rest of the privacy pipeline acts on; the rest is for audit and
    model evaluation.
    """
    try:
        # Resize for speed; face-sized skin regions are still detectable
        # at 256px on the long side.
        max_side = max(image.size)
        if max_side > 256:
            scale = 256 / max_side
            sample = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
        else:
            sample = image
        rgb = sample.convert("RGB")
        pixels = list(rgb.getdata())
        if not pixels:
            return {"detected": False, "confidence": 0, "reason": "empty"}
        skin_pixels = 0
        for r, g, b in pixels:
            # Heuristic skin-tone range (R > G > B, with R and G close).
            if r > 95 and g > 40 and b > 20 and r > g and r > b and (max(r, g, b) - min(r, g, b)) > 15:
                skin_pixels += 1
        ratio = skin_pixels / len(pixels)
        detected = ratio > 0.18 and sample.size[0] >= 64 and sample.size[1] >= 64
        return {
            "detected": detected,
            "confidence": min(100, int(ratio * 200)),
            "skin_ratio": round(ratio, 4),
            "sample_size": sample.size,
        }
    except Exception as exc:  # pragma: no cover - failure path is rare
        return {"detected": False, "confidence": 0, "reason": f"detector_error: {exc.__class__.__name__}"}


def _validate_upload(upload: UploadedFile) -> tuple[bytes, str]:
    file_name = upload.name or ""
    if not file_name or "\x00" in file_name or "/" in file_name or "\\" in file_name:
        raise ValueError("Malformed file name.")
    suffixes = Path(file_name).suffixes
    if len(suffixes) != 1 or suffixes[0].lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Only single-extension JPEG, PNG, and WebP images are allowed.")
    expected_mime = ALLOWED_EXTENSIONS[suffixes[0].lower()]
    if upload.size is not None and upload.size > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds platform size limit.")
    data = upload.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds platform size limit.")
    mime_type = _detect_mime(data, upload.name)
    if mime_type not in ALLOWED_MIME_TYPES or mime_type != expected_mime:
        raise ValueError("Only JPEG, PNG, and WebP images are allowed.")
    return data, mime_type


def _duplicate_score(branch: Branch, derivative_hash_value: str) -> int:
    if not derivative_hash_value:
        return 0
    current = imagehash.hex_to_hash(derivative_hash_value)
    best = 0
    for existing in EvidenceItem.objects.filter(branch=branch, derivative_hash__isnull=False).exclude(derivative_hash=""):
        try:
            other = imagehash.hex_to_hash(existing.derivative_hash)
        except Exception:
            continue
        distance = current - other
        score = max(0, 100 - distance * 12)
        best = max(best, score)
    return best


def _next_sequence(task_instance: TaskInstance) -> int:
    current = EvidenceItem.objects.filter(task_instance=task_instance).aggregate(max_seq=Max("sequence_number"))["max_seq"]
    return (current or 0) + 1


@transaction.atomic
def submit_evidence(
    *,
    session_token: str,
    user: User,
    upload: UploadedFile | None = None,
    note_text: str = "",
    number_value: Any | None = None,
    confirmation_value: bool | None = None,
    face_detected: bool = False,
    challenge_response: str = "",
) -> EvidenceItem:
    session = CaptureSession.objects.select_for_update().select_related("company", "branch", "task_instance", "template_version").get(token=session_token)
    now = timezone.now()
    if session.status != CaptureSessionStatus.ACTIVE:
        raise ValueError("Capture session already used or revoked.")
    if session.expires_at <= now:
        session.status = CaptureSessionStatus.EXPIRED
        session.save(update_fields=["status", "updated_at"])
        raise ValueError("Capture session expired.")
    if session.created_by_id != user.id:
        raise ValueError("Capture session cannot be reused by another user.")
    if session.challenge_text and challenge_response.strip() != session.challenge_answer.strip():
        raise ValueError("Challenge response required.")

    evidence_type = session.evidence_type
    quarantine_name = ""
    private_name = ""
    blurred_name = ""
    raw_hash = ""
    derivative_hash_value = ""
    mime_type = ""
    media_size = 0
    media_width = None
    media_height = None

    quarantine_path: Path | None = None
    private_path: Path | None = None
    processing_succeeded = False
    server_face_detection: dict[str, object] = {"detected": False, "confidence": 0}
    privacy_decision = "pending_review"
    try:
        if evidence_type == EvidenceType.IMAGE:
            if upload is None:
                raise ValueError("Image evidence requires a file upload.")
            raw_data, mime_type = _validate_upload(upload)
            media_size = len(raw_data)
            raw_hash = _sha256(raw_data)
            quarantine_name = _quarantine_name(upload.name)
            quarantine_path = _subdir("quarantine") / quarantine_name
            quarantine_path.write_bytes(raw_data)
            image = _open_image(raw_data)
            media_width, media_height = image.size
            # C-13: server-side face detection. The client flag is
            # recorded but never trusted to authorise the unblurred
            # image. The detector result drives both the blur and the
            # ``privacy_decision`` field.
            server_face_detection = _server_detect_face(image)
            server_face_detected = bool(server_face_detection.get("detected"))
            normalized = _normalize_image(image, server_face_detected)
            private_name = _private_name()
            private_path = _subdir("private") / private_name
            normalized.save(private_path, format="WEBP", quality=90)
            derivative_hash_value = str(imagehash.phash(normalized))
            blurred_name = private_name
            if server_face_detected:
                privacy_decision = "approved_blurred"
            else:
                privacy_decision = "rejected_no_face" if face_detected else "retained_unblurred"
            quarantine_path.unlink(missing_ok=True)
        elif upload is not None:
            raise ValueError("Non-image evidence cannot include file uploads.")

        confidence_value = server_face_detection.get("confidence", 0)
        face_detector_confidence = (
            int(confidence_value)
            if isinstance(confidence_value, (int, float, str))
            else 0
        )
        item = EvidenceItem.objects.create(
            company=session.company,
            branch=session.branch,
            task_instance=session.task_instance,
            capture_session=session,
            submitted_by=user,
            evidence_type=evidence_type,
            sequence_number=_next_sequence(session.task_instance),
            note_text=note_text,
            number_value=number_value,
            confirmation_value=confirmation_value,
            quarantine_name=quarantine_name,
            private_media_name=private_name,
            blurred_media_name=blurred_name,
            media_mime_type=mime_type,
            media_size_bytes=media_size,
            media_width=media_width,
            media_height=media_height,
            raw_hash=raw_hash,
            derivative_hash=derivative_hash_value,
            duplicate_risk_score=_duplicate_score(session.branch, derivative_hash_value),
            face_detected=face_detected,
            privacy_decision=privacy_decision,
            face_detector_version=FACE_DETECTOR_VERSION,
            face_detector_confidence=face_detector_confidence,
            face_detector_raw_score=server_face_detection,
            privacy_metadata={"client_face_flag": bool(face_detected)},
            challenge_response=challenge_response,
        )
        session.status = CaptureSessionStatus.USED
        session.used_at = now
        session.used_by = user
        session.save(update_fields=["status", "used_at", "used_by", "updated_at"])
        record_audit_event(
            event_type="EVIDENCE_SUBMITTED",
            target_type="evidence_item",
            target_id=str(item.id),
            actor_id=str(user.id),
            branch_id=str(session.branch_id),
            metadata={"task_instance_id": str(session.task_instance_id), "evidence_type": evidence_type},
        )
        processing_succeeded = True
        return item
    finally:
        if not processing_succeeded:
            if quarantine_path is not None:
                quarantine_path.unlink(missing_ok=True)
            if private_path is not None:
                private_path.unlink(missing_ok=True)


@transaction.atomic
def create_issue_report(task_instance: TaskInstance, user: User, note: str, upload: UploadedFile | None = None) -> TaskIssueReport:
    photo_name = ""
    photo_path: Path | None = None
    succeeded = False
    try:
        if upload is not None:
            raw_data, _mime = _validate_upload(upload)
            image = _open_image(raw_data)
            image.close()
            photo_name = _quarantine_name(upload.name)
            photo_path = _subdir("issues") / photo_name
            photo_path.write_bytes(raw_data)
        issue = TaskIssueReport.objects.create(
            company=task_instance.company,
            branch=task_instance.branch,
            task_instance=task_instance,
            submitted_by=user,
            note=note,
            photo_name=photo_name,
        )
        record_audit_event(
            event_type="TASK_ISSUE_REPORTED",
            target_type="task_issue_report",
            target_id=str(issue.id),
            actor_id=str(user.id),
            branch_id=str(task_instance.branch_id),
            metadata={"task_instance_id": str(task_instance.id)},
        )
        succeeded = True
        return issue
    finally:
        if not succeeded and photo_path is not None:
            photo_path.unlink(missing_ok=True)


@transaction.atomic
def create_discussion_message(task_instance: TaskInstance, user: User, message: str, issue_report: TaskIssueReport | None = None, reply_to: TaskDiscussionMessage | None = None) -> TaskDiscussionMessage:
    discussion = TaskDiscussionMessage.objects.create(
        company=task_instance.company,
        branch=task_instance.branch,
        task_instance=task_instance,
        issue_report=issue_report,
        reply_to=reply_to,
        author=user,
        message=message,
    )
    record_audit_event(
        event_type="TASK_DISCUSSION_MESSAGE_CREATED",
        target_type="task_discussion_message",
        target_id=str(discussion.id),
        actor_id=str(user.id),
        branch_id=str(task_instance.branch_id),
        metadata={"task_instance_id": str(task_instance.id)},
    )
    return discussion


def can_access_media(user: User, evidence: EvidenceItem) -> bool:
    if evidence.submitted_by_id == user.id:
        return True
    membership = CompanyMembership.objects.filter(company=evidence.company, user=user, active=True).first()
    if membership and membership.role in {CompanyRole.OWNER, CompanyRole.MONITOR}:
        return True
    return UserBranchMembership.objects.filter(company=evidence.company, user=user, branch=evidence.branch, active=True).exists()


def media_file_response(evidence: EvidenceItem) -> FileResponse:
    path_name = evidence.blurred_media_name or evidence.private_media_name or evidence.quarantine_name
    path = _subdir("private") / path_name
    return FileResponse(path.open("rb"), as_attachment=False)
