from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.identity.models import MfaEnrollment, MfaMethodType
from apps.organizations.models import Branch, CompanyMembership, CompanyRole, JobRole

from .models import Company, IndustryChoice, LegalAcceptance, LegalDocumentType, SupportAuthorization


class RegisterSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    company_code = serializers.CharField(max_length=64)
    industry = serializers.ChoiceField(choices=IndustryChoice.choices)
    owner_login_id = serializers.CharField(max_length=150)
    owner_password = serializers.CharField(min_length=12, write_only=True)
    owner_display_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(required=False, allow_blank=True)

    def validate_owner_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class RegisterResponseSerializer(serializers.Serializer):
    company = serializers.DictField()
    owner = serializers.DictField()


class LoginSerializer(serializers.Serializer):
    company_code = serializers.CharField(max_length=64)
    login_id = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    mfa_code = serializers.CharField(required=False, allow_blank=True)


class AuthSessionSerializer(serializers.Serializer):
    user = serializers.DictField()
    company = serializers.DictField()


class UserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    login_id = serializers.CharField()
    display_name = serializers.CharField()


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "code",
            "industry",
            "status",
            "trial_ends_at",
            "read_only_until",
            "deletion_due_at",
        ]


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "code", "timezone", "operational_day_cutoff", "active"]


class JobRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRole
        fields = ["id", "name", "code", "active"]


class CompanyMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyMembership
        fields = ["user", "role", "active", "active_from", "active_until"]


class LegalAcceptanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalAcceptance
        fields = ["document_type", "document_version", "accepted_at"]


class SupportAuthorizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportAuthorization
        fields = ["id", "support_user", "granted_at", "expires_at", "revoked_at", "reason", "active"]


class SupportAuthorizationCreateSerializer(serializers.Serializer):
    support_user_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=255, trim_whitespace=True)
    expires_at = serializers.DateTimeField()


class MfaEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MfaEnrollment
        fields = ["id", "method_type", "label", "credential_id", "public_key", "verified_at", "active"]
        read_only_fields = ["verified_at"]


class MfaEnrollmentCreateSerializer(MfaEnrollmentSerializer):
    secret = serializers.CharField(read_only=True)

    class Meta(MfaEnrollmentSerializer.Meta):
        fields = [*MfaEnrollmentSerializer.Meta.fields, "secret"]


class MfaEnrollRequestSerializer(serializers.Serializer):
    method_type = serializers.ChoiceField(choices=MfaMethodType.choices)
    label = serializers.CharField(max_length=120, required=False, allow_blank=True)


class MfaVerifySerializer(serializers.Serializer):
    enrollment_id = serializers.UUIDField()
    code = serializers.CharField(max_length=16)


class MemberCreateSerializer(serializers.Serializer):
    login_id = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=12, write_only=True)
    display_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=CompanyRole.choices)

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class BranchCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=64)
    timezone = serializers.CharField(max_length=64)
    operational_day_cutoff = serializers.TimeField()


class BranchMembershipCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    branch_id = serializers.UUIDField()
    job_role_id = serializers.UUIDField()
    membership_type = serializers.CharField(max_length=32, required=False, default="primary")


class RoleCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=64)


class AcceptanceCreateSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(choices=LegalDocumentType.choices)
    document_version = serializers.CharField(max_length=64)
