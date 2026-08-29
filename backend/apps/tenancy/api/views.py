from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time

from django.contrib.auth import login, logout
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.audit.services import record_audit_event
from apps.identity.models import MfaEnrollment, MfaMethodType, User
from apps.organizations.models import Branch, CompanyMembership, CompanyRole, JobRole, UserBranchMembership
from apps.platform_core.errors import PlatformAPIException, platform_service_call
from apps.platform_core.mixins import TenantAPIView

from ..access import active_membership_q, require_company_user
from ..auth_backends import CompanyCodeBackend
from ..models import Company, LegalAcceptance, SupportAuthorization
from ..serializers import (
    AcceptanceCreateSerializer,
    AuthSessionSerializer,
    BranchMembershipCreateSerializer,
    CompanyMembershipSerializer,
    CompanySerializer,
    LoginSerializer,
    MfaEnrollRequestSerializer,
    MfaEnrollmentCreateSerializer,
    MfaEnrollmentSerializer,
    MfaVerifySerializer,
    MemberCreateSerializer,
    RegisterSerializer,
    RegisterResponseSerializer,
    SupportAuthorizationCreateSerializer,
    SupportAuthorizationSerializer,
    UserSerializer,
)
from ..services import (
    enroll_totp,
    current_support_authorization,
    ensure_company_operational,
    grant_support,
    normalize_company_code,
    register_company,
    revoke_support,
)
from ..throttles import (
    LoginAccountThrottle,
    LoginIPThrottle,
    MfaUserThrottle,
    RegistrationIPThrottle,
)


# ---------------------------------------------------------------------------
# LEGAL-06: legal document version enforcement
# ---------------------------------------------------------------------------


def _is_legal_version_published(document_type: str, document_version: str) -> bool:
    """Return ``True`` iff ``document_version`` matches the current published version.

    The ``LegalDocument`` registry in :mod:`apps.compliance` is the
    single source of truth for what is currently published. The
    :class:`LegalAcceptance` model stores the ``(document_type,
    version)`` pair accepted by the user; the view refuses any
    acceptance that does not match the current version, so a tampered
    or stale client cannot record an acceptance for a withdrawn
    document.

    The helper imports ``apps.compliance`` lazily so the tenancy
    module remains importable when the compliance app is not yet
    installed (e.g. fresh migrations during deployment). When the
    compliance app is unavailable, the check is permissive — the
    existing ``register_company`` flow continues to work and operators
    can install the compliance app before production promotion.
    """
    try:
        from apps.compliance.acceptance import LEGAL_TYPE_TO_KIND
        from apps.compliance.models import LegalDocumentKind
        from apps.compliance.services import current_legal_document
    except Exception:  # noqa: BLE001 - compliance app unavailable
        return True
    kind_value = LEGAL_TYPE_TO_KIND.get(document_type)
    if kind_value is None:
        # Unknown mapping: defer to the underlying choice set; the
        # serializer has already validated the value, so an unknown
        # mapping indicates a tenancy/compliance enum drift that the
        # operator should see rather than silently accept.
        return False
    try:
        kind = LegalDocumentKind(kind_value)
    except ValueError:
        return False
    document = current_legal_document(kind)
    if document is None:
        # No document is currently published. Refuse the acceptance
        # rather than allow a free-form version, so the operator sees
        # the gap explicitly.
        return False
    return document.version == document_version


def _totp_token(secret: str, timestamp: int | None = None) -> str:
    step = 30
    counter = int((timestamp or time.time()) // step)
    try:
        key = base64.b32decode(secret, casefold=True)
    except (ValueError, TypeError) as exc:
        raise PlatformAPIException("Invalid MFA enrollment secret.") from exc
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (
        ((digest[offset] & 0x7F) << 24)
        | ((digest[offset + 1] & 0xFF) << 16)
        | ((digest[offset + 2] & 0xFF) << 8)
        | (digest[offset + 3] & 0xFF)
    )
    return f"{code_int % 1_000_000:06d}"


def _verify_totp(secret: str, code: str) -> bool:
    candidates = (
        _totp_token(secret),
        _totp_token(secret, int(time.time()) - 30),
        _totp_token(secret, int(time.time()) + 30),
    )
    return any(hmac.compare_digest(code, candidate) for candidate in candidates)


def _matching_totp_timestep(secret: str, code: str) -> int | None:
    current_timestep = int(time.time() // 30)
    for timestep in (current_timestep, current_timestep - 1, current_timestep + 1):
        if hmac.compare_digest(code, _totp_token(secret, timestep * 30)):
            return timestep
    return None


@transaction.atomic
def _consume_totp(enrollment: MfaEnrollment, code: str) -> bool:
    locked = MfaEnrollment.objects.select_for_update().get(id=enrollment.id)
    timestep = _matching_totp_timestep(locked.secret, code)
    if timestep is None:
        return False
    if locked.last_used_timestep is not None and timestep <= locked.last_used_timestep:
        return False
    locked.last_used_timestep = timestep
    locked.save(update_fields=["last_used_timestep", "updated_at"])
    return True


class RegisterView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []
    throttle_classes = [RegistrationIPThrottle]

    @extend_schema(request=RegisterSerializer, responses=RegisterResponseSerializer)
    @platform_service_call
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company, owner = register_company(**serializer.validated_data)
        login(request, owner, backend="django.contrib.auth.backends.ModelBackend")
        request.session["company_id"] = str(company.id)
        return Response({"company": CompanySerializer(company).data, "owner": UserSerializer(owner).data}, status=201)


class LoginView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []
    throttle_classes = [LoginIPThrottle, LoginAccountThrottle]

    @extend_schema(request=LoginSerializer, responses=AuthSessionSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_code = normalize_company_code(serializer.validated_data["company_code"])
        user = CompanyCodeBackend().authenticate(
            request,
            company_code=company_code,
            login_id=serializer.validated_data["login_id"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            raise PlatformAPIException("Invalid credentials or company code.")
        company = Company.objects.get(code=company_code)
        mfa_enrollments = MfaEnrollment.objects.filter(user=user, active=True, verified_at__isnull=False)
        if mfa_enrollments.exists():
            provided = serializer.validated_data.get("mfa_code")
            if not provided or not any(
                enrollment.method_type == MfaMethodType.TOTP and _consume_totp(enrollment, provided)
                for enrollment in mfa_enrollments
            ):
                raise PlatformAPIException("MFA code is required.")
        login(request, user, backend="apps.tenancy.auth_backends.CompanyCodeBackend")
        request.session["company_id"] = str(company.id)
        record_audit_event(
            event_type="USER_LOGIN",
            target_type="user",
            target_id=str(user.id),
            actor_id=str(user.id),
            metadata={"company_id": str(company.id)},
        )
        support_grant = current_support_authorization(company, user)
        if support_grant is not None:
            record_audit_event(
                event_type="SUPPORT_ACCESS_USED",
                target_type="support_authorization",
                target_id=str(support_grant.id),
                actor_id=str(user.id),
                metadata={
                    "company_id": str(company.id),
                    "reason": support_grant.reason,
                    "expires_at": support_grant.expires_at.isoformat(),
                },
            )
        return Response({"user": UserSerializer(user).data, "company": CompanySerializer(company).data})


class LogoutView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        if getattr(request, "user", None) and request.user.is_authenticated:
            record_audit_event(
                event_type="USER_LOGOUT",
                target_type="user",
                target_id=str(request.user.id),
                actor_id=str(request.user.id),
            )
        logout(request)
        request.session.flush()
        return Response(status=204)


class MeView(TenantAPIView):
    # BE-01: ``/me`` is the post-login self-introspection endpoint; open
    # to every authenticated user regardless of role.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(responses=OpenApiResponse(description="Current user, active company, and memberships."))
    def get(self, request):
        # ``MeView`` is the one place that tolerates a missing company
        # selection (e.g. immediately after login). It still rejects forged
        # company IDs: if a ``company_id`` is present in the session, the
        # tenant lookup must succeed or we surface 403, the same way the
        # pre-mixin code did via ``_current_company`` raising.
        company = None
        if request.session.get("company_id"):
            company = self.get_tenant().company
        memberships = (
            CompanyMembership.objects.filter(company=company, user=request.user, active=True)
            .filter(active_membership_q())
            if company is not None
            else CompanyMembership.objects.none()
        )
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "company": CompanySerializer(company).data if company else None,
                "memberships": CompanyMembershipSerializer(memberships, many=True).data,
            }
        )


class MfaEnrollView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MfaUserThrottle]

    @extend_schema(request=MfaEnrollRequestSerializer, responses={201: MfaEnrollmentCreateSerializer})
    def post(self, request):
        serializer = MfaEnrollRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method_type = serializer.validated_data["method_type"]
        label = serializer.validated_data.get("label", "")
        if method_type == MfaMethodType.TOTP:
            enrollment = enroll_totp(request.user, label=label)
        else:
            raise PlatformAPIException("Passkey enrollment is not available in this release.")
        record_audit_event(
            event_type="MFA_ENROLLMENT_CREATED",
            target_type="user",
            target_id=str(request.user.id),
            actor_id=str(request.user.id),
            metadata={"method_type": enrollment.method_type, "enrollment_id": str(enrollment.id)},
        )
        return Response(MfaEnrollmentCreateSerializer(enrollment).data, status=201)


class MfaVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MfaUserThrottle]

    @extend_schema(request=MfaVerifySerializer, responses=MfaEnrollmentSerializer)
    def post(self, request):
        serializer = MfaVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = MfaEnrollment.objects.get(id=serializer.validated_data["enrollment_id"], user=request.user)
        if enrollment.method_type != MfaMethodType.TOTP:
            raise PlatformAPIException("Only TOTP verification is implemented in this phase.")
        if enrollment.verified_at is not None:
            raise PlatformAPIException("This MFA enrollment is already verified.")
        if not _consume_totp(enrollment, serializer.validated_data["code"]):
            raise PlatformAPIException("Invalid MFA code.")
        enrollment.verify()
        record_audit_event(
            event_type="MFA_ENROLLED",
            target_type="user",
            target_id=str(request.user.id),
            actor_id=str(request.user.id),
            metadata={"method_type": enrollment.method_type},
        )
        return Response(MfaEnrollmentSerializer(enrollment).data)


class CompanyMembersView(TenantAPIView):
    required_roles = (CompanyRole.OWNER,)

    @extend_schema(responses=OpenApiResponse(description="List of company memberships."))
    def get(self, request):
        company = self.get_tenant().company
        memberships = CompanyMembership.objects.filter(company=company).select_related("user")
        return Response({"memberships": CompanyMembershipSerializer(memberships, many=True).data})


class CompanyUsersView(TenantAPIView):
    required_roles = (CompanyRole.OWNER,)

    @extend_schema(request=MemberCreateSerializer, responses={201: OpenApiResponse(response=dict, description="Created company user.")})
    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        ensure_company_operational(company)
        serializer = MemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.create_user(
            login_id=serializer.validated_data["login_id"],
            password=serializer.validated_data["password"],
            display_name=serializer.validated_data.get("display_name", ""),
        )
        CompanyMembership.objects.create(
            company=company,
            user=user,
            role=serializer.validated_data["role"],
        )
        record_audit_event(
            event_type="COMPANY_USER_CREATED",
            target_type="company",
            target_id=str(company.id),
            actor_id=str(request.user.id),
            metadata={"user_id": str(user.id), "role": serializer.validated_data["role"]},
        )
        return Response({"user": UserSerializer(user).data}, status=201)


class BranchMembershipView(TenantAPIView):
    required_roles = (CompanyRole.OWNER,)

    @extend_schema(request=BranchMembershipCreateSerializer, responses={201: OpenApiResponse(response=dict, description="Created branch membership.")})
    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        ensure_company_operational(company)
        serializer = BranchMembershipCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data["user_id"]
        require_company_user(self.get_tenant(), user_id)
        user = User.objects.get(id=user_id)
        branch = Branch.objects.get(id=serializer.validated_data["branch_id"], company=company)
        job_role = JobRole.objects.get(id=serializer.validated_data["job_role_id"], company=company)
        membership = UserBranchMembership.objects.create(
            company=company,
            user=user,
            branch=branch,
            job_role=job_role,
            membership_type=serializer.validated_data.get("membership_type", "primary"),
        )
        record_audit_event(
            event_type="BRANCH_MEMBERSHIP_CREATED",
            target_type="company",
            target_id=str(company.id),
            actor_id=str(request.user.id),
            metadata={"user_id": str(user.id), "branch_id": str(branch.id)},
        )
        return Response({"branch_membership_id": membership.id}, status=201)


class AcceptanceView(TenantAPIView):
    # BE-01: Recording a legal acceptance can be done by any role in the
    # active company.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=AcceptanceCreateSerializer, responses={201: OpenApiResponse(response=dict, description="Recorded legal acceptance id.")})
    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        ensure_company_operational(company)
        serializer = AcceptanceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_type = serializer.validated_data["document_type"]
        document_version = serializer.validated_data["document_version"]
        # LEGAL-06: an acceptance can only be recorded for a currently
        # published version of the legal document. This is the
        # authoritative check; the ``LegalDocument`` registry in
        # ``apps.compliance`` is the single source of truth.
        if not _is_legal_version_published(document_type, document_version):
            record_audit_event(
                event_type="LEGAL_ACCEPTANCE_REJECTED",
                target_type="company",
                target_id=str(company.id),
                actor_id=str(request.user.id),
                metadata={
                    "document_type": document_type,
                    "document_version": document_version,
                    "reason": "not_currently_published",
                },
            )
            raise PlatformAPIException(
                f"Version {document_version!r} is not the currently published "
                f"version for document type {document_type!r}."
            )
        acceptance = LegalAcceptance.objects.create(
            company=company,
            accepted_by=request.user,
            document_type=document_type,
            document_version=document_version,
        )
        record_audit_event(
            event_type="LEGAL_ACCEPTANCE_RECORDED",
            target_type="company",
            target_id=str(company.id),
            actor_id=str(request.user.id),
            metadata={
                "document_type": acceptance.document_type,
                "document_version": acceptance.document_version,
            },
        )
        return Response({"acceptance": acceptance.id}, status=201)


class SupportAuthorizationView(TenantAPIView):
    required_roles = (CompanyRole.OWNER,)

    @extend_schema(request=None, responses={201: SupportAuthorizationSerializer})
    @platform_service_call
    def post(self, request):
        company = self.get_tenant().company
        serializer = SupportAuthorizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        support_user = User.objects.get(id=serializer.validated_data["support_user_id"])
        grant = grant_support(
            company,
            support_user,
            request.user,
            reason=serializer.validated_data["reason"],
            expires_at=serializer.validated_data["expires_at"],
        )
        return Response(SupportAuthorizationSerializer(grant).data, status=201)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request):
        company = self.get_tenant().company
        support_user_id = request.data.get("support_user_id")
        grant = SupportAuthorization.objects.filter(company=company, support_user_id=support_user_id, active=True).first()
        if grant is None:
            raise PlatformAPIException("Support authorization not found.")
        revoke_support(grant, revoked_by=request.user)
        return Response(status=204)
