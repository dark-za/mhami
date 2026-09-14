from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.organizations.models import Branch, CompanyMembership, CompanyRole, JobRole

from .models import Company, LegalAcceptance, LegalDocumentType


class LoginSerializer(serializers.Serializer):
    login_id = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        rejected = set(self.initial_data) - {"login_id", "password"}
        if rejected:
            raise serializers.ValidationError(
                {f: "This field is not accepted." for f in sorted(rejected)}
            )
        return attrs


class AuthSessionSerializer(serializers.Serializer):
    user = serializers.DictField()
    company = serializers.DictField()


class InitialSetupSerializer(serializers.Serializer):
    organization_name = serializers.CharField(max_length=255)
    owner_login_id = serializers.CharField(max_length=150)
    owner_display_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(min_length=12, write_only=True, trim_whitespace=False)
    setup_token = serializers.CharField(min_length=16, max_length=512, write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        accepted = {"organization_name", "owner_login_id", "owner_display_name", "password", "setup_token"}
        rejected = set(self.initial_data) - accepted
        if rejected:
            raise serializers.ValidationError({field: "This field is not accepted." for field in sorted(rejected)})
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs


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
            "suspended_at",
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
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    login_id = serializers.CharField(source="user.login_id", read_only=True)
    display_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = CompanyMembership
        fields = ["user", "user_id", "login_id", "display_name", "role", "active", "active_from", "active_until"]


class LegalAcceptanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalAcceptance
        fields = ["document_type", "document_version", "accepted_at"]


class MemberCreateSerializer(serializers.Serializer):
    login_id = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=12, write_only=True, trim_whitespace=False)
    display_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=CompanyRole.choices)
    branch_id = serializers.UUIDField(required=False)
    job_role_id = serializers.UUIDField(required=False)

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
