from __future__ import annotations

from secrets import compare_digest

from django.conf import settings
from django.contrib.auth import login, logout
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.audit.services import record_audit_event
from apps.identity.models import User
from apps.organizations.models import Branch, CompanyMembership, CompanyRole, JobRole, UserBranchMembership
from apps.platform_core.errors import PlatformAPIException, PlatformPermissionException, platform_service_call
from apps.platform_core.mixins import TenantAPIView

from ..access import active_membership_q, require_company_user
from ..auth_backends import LocalInstallationBackend
from ..models import Company, LegalAcceptance
from ..serializers import (
    AcceptanceCreateSerializer,
    AuthSessionSerializer,
    BranchMembershipCreateSerializer,
    CompanyMembershipSerializer,
    CompanySerializer,
    InitialSetupSerializer,
    LoginSerializer,
    MemberCreateSerializer,
    UserSerializer,
)
from ..services import ensure_company_operational, initial_setup_required, provision_initial_owner
from ..throttles import (
    LoginAccountThrottle,
    LoginIPThrottle,
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
    compliance app is unavailable, the check is permissive so an
    operator can install the compliance app before production use.
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


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []
    throttle_classes = [LoginIPThrottle, LoginAccountThrottle]

    @extend_schema(request=LoginSerializer, responses=AuthSessionSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = LocalInstallationBackend().authenticate(
            request,
            login_id=serializer.validated_data["login_id"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            raise PlatformAPIException("Invalid credentials.")
        # Fail closed if sole organization cannot be resolved (0 or >1).
        company_qs = Company.objects.all()
        if company_qs.count() != 1:
            raise PlatformAPIException("Invalid credentials.")
        company = company_qs.first()
        assert company is not None
        if not company.is_operational():
            raise PlatformAPIException("Invalid credentials.")
        login(request, user, backend="apps.tenancy.auth_backends.LocalInstallationBackend")
        request.session["company_id"] = str(company.id)
        record_audit_event(
            event_type="USER_LOGIN",
            target_type="user",
            target_id=str(user.id),
            actor_id=str(user.id),
            metadata={"company_id": str(company.id)},
        )
        return Response({"user": UserSerializer(user).data, "company": CompanySerializer(company).data})


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class InitialSetupView(APIView):
    """Create the first owner only while the installation is empty."""

    authentication_classes: list[type] = []
    permission_classes: list[type] = []
    throttle_classes = [RegistrationIPThrottle]

    @extend_schema(request=InitialSetupSerializer, responses={201: AuthSessionSerializer})
    @platform_service_call
    def post(self, request):
        serializer = InitialSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        configured_token = settings.INITIAL_SETUP_TOKEN
        supplied_token = serializer.validated_data["setup_token"]
        if not configured_token or not compare_digest(configured_token, supplied_token):
            raise PlatformAPIException("Initial setup is unavailable.")

        if not initial_setup_required():
            raise PlatformAPIException("Initial setup is unavailable.")

        company, owner = provision_initial_owner(
            organization_name=serializer.validated_data["organization_name"],
            owner_login_id=serializer.validated_data["owner_login_id"],
            owner_display_name=serializer.validated_data.get("owner_display_name", ""),
            password=serializer.validated_data["password"],
            initiated_via="browser_setup",
        )
        login(request, owner, backend="apps.tenancy.auth_backends.LocalInstallationBackend")
        request.session["company_id"] = str(company.id)
        return Response({"user": UserSerializer(owner).data, "company": CompanySerializer(company).data}, status=201)

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


class CompanyMembersView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(responses=OpenApiResponse(description="List of company memberships."))
    def get(self, request):
        context = self.get_tenant()
        company = context.company
        if context.role == CompanyRole.OWNER:
            memberships = CompanyMembership.objects.filter(company=company).select_related("user")
        else:
            # Monitor gets only active employee memberships that have an active branch assignment
            # in a branch assigned to the monitor. Use server-side filters only.
            branch_ids = context.branch_ids
            if not branch_ids:
                memberships = CompanyMembership.objects.none()
            else:
                from django.db.models import Exists, OuterRef

                from apps.organizations.models import UserBranchMembership

                memberships = (
                    CompanyMembership.objects.filter(company=company, role=CompanyRole.EMPLOYEE, active=True)
                    .filter(active_membership_q())
                    .filter(
                        Exists(
                            UserBranchMembership.objects.filter(
                                company=company,
                                user_id=OuterRef("user_id"),
                                active=True,
                                branch_id__in=branch_ids,
                                branch__active=True,
                            ).filter(active_membership_q())
                        )
                    )
                    .select_related("user")
                )
        return Response({"memberships": CompanyMembershipSerializer(memberships, many=True).data})


class CompanyUsersView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(request=MemberCreateSerializer, responses={201: OpenApiResponse(response=dict, description="Created company user.")})
    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        company = context.company
        ensure_company_operational(company)
        serializer = MemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        requested_role = serializer.validated_data["role"]
        branch = None
        job_role = None
        if context.role == CompanyRole.MONITOR and requested_role != CompanyRole.EMPLOYEE:
            raise PlatformPermissionException("Monitors may create only employee users.")
        if context.role == CompanyRole.MONITOR:
            branch_id = serializer.validated_data.get("branch_id")
            job_role_id = serializer.validated_data.get("job_role_id")
            if not branch_id or not job_role_id:
                raise PlatformPermissionException(
                    "Monitors must assign a branch and job role when creating an employee."
                )
            if branch_id not in context.branch_ids:
                raise PlatformPermissionException("This branch is outside your access scope.")
            branch = Branch.objects.filter(id=branch_id, company=company, active=True).first()
            job_role = JobRole.objects.filter(id=job_role_id, company=company, active=True).first()
            if branch is None or job_role is None:
                raise PlatformPermissionException("The selected branch or job role is unavailable.")

        with transaction.atomic():
            user = User.objects.create_user(
                login_id=serializer.validated_data["login_id"],
                password=serializer.validated_data["password"],
                display_name=serializer.validated_data.get("display_name", ""),
            )
            CompanyMembership.objects.create(
                company=company,
                user=user,
                role=requested_role,
            )
            if branch is not None and job_role is not None:
                UserBranchMembership.objects.create(
                    company=company,
                    user=user,
                    branch=branch,
                    job_role=job_role,
                    membership_type="primary",
                )
        record_audit_event(
            event_type="COMPANY_USER_CREATED",
            target_type="company",
            target_id=str(company.id),
            actor_id=str(request.user.id),
            metadata={"user_id": str(user.id), "role": requested_role},
        )
        return Response({"user": UserSerializer(user).data}, status=201)


class BranchMembershipView(TenantAPIView):
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR)

    @extend_schema(request=BranchMembershipCreateSerializer, responses={201: OpenApiResponse(response=dict, description="Created branch membership.")})
    @platform_service_call
    def post(self, request):
        context = self.get_tenant()
        company = context.company
        ensure_company_operational(company)
        serializer = BranchMembershipCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data["user_id"]
        branch_id = serializer.validated_data["branch_id"]
        require_company_user(context, user_id)
        user = User.objects.get(id=user_id)
        branch = Branch.objects.get(id=branch_id, company=company)
        job_role = JobRole.objects.get(id=serializer.validated_data["job_role_id"], company=company)
        if context.role == CompanyRole.MONITOR:
            target_membership = (
                CompanyMembership.objects.filter(company=company, user_id=user_id, active=True)
                .filter(active_membership_q())
                .first()
            )
            target_role = target_membership.role if target_membership else None
            if target_role != CompanyRole.EMPLOYEE:
                raise PlatformPermissionException("Monitors may assign branches only for employee users.")
            if branch.id not in context.branch_ids:
                raise PlatformPermissionException("This branch is outside your access scope.")
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
