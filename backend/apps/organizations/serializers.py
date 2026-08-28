from __future__ import annotations

from rest_framework import serializers

from apps.platform_core.errors import PlatformPermissionException

from .models import Branch, CompanyMembership, CompanyRole, JobRole, UserBranchMembership, WeeklyShift


class BranchCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=64)
    timezone = serializers.CharField(max_length=64)
    operational_day_cutoff = serializers.TimeField()


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "code", "timezone", "operational_day_cutoff", "active"]


class JobRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRole
        fields = ["id", "name", "code", "active"]


class RoleCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=64)


class WeeklyShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyShift
        fields = ["id", "branch", "user", "weekday", "start_time", "end_time", "active"]


class WeeklyShiftCreateSerializer(serializers.Serializer):
    """Validate the inputs to ``POST /organizations/weekly-shifts``.

    C-03 closed an IDOR (A01:2021 Broken Access Control) where
    ``WeeklyShiftCreateSerializer`` accepted arbitrary ``branch_id`` and
    ``user_id`` UUIDs from the request body and the view would create a
    :class:`WeeklyShift` carrying cross-tenant references. The serializer
    now requires an explicit ``company`` to scope the lookup, asserts both
    foreign keys belong to that company, verifies the user is an active
    member, and confirms the branch membership is also active.
    """

    branch_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._company = company

    def validate(self, attrs):
        if self._company is None:
            raise serializers.ValidationError(
                {"detail": "Tenant context is required to create a weekly shift."}
            )

        branch_id = attrs["branch_id"]
        user_id = attrs["user_id"]
        start_time = attrs["start_time"]
        end_time = attrs["end_time"]

        if end_time <= start_time:
            raise serializers.ValidationError(
                {"end_time": "Shift end time must be after start time."}
            )

        branch = (
            Branch.objects.filter(id=branch_id, company=self._company, active=True)
            .only("id", "company_id")
            .first()
        )
        if branch is None:
            # Return 403, not 404, so a cross-tenant probe does not learn
            # whether the branch exists in another company.
            raise PlatformPermissionException(
                "The selected branch is outside the active company."
            )

        membership = (
            CompanyMembership.objects.filter(
                company=self._company, user_id=user_id, active=True
            )
            .only("id", "active")
            .first()
        )
        if membership is None:
            raise PlatformPermissionException(
                "The selected user is not an active member of this company."
            )

        if membership.role != CompanyRole.OWNER:
            branch_membership = (
                UserBranchMembership.objects.filter(
                    company=self._company,
                    user_id=user_id,
                    branch_id=branch_id,
                    active=True,
                )
                .only("id")
                .first()
            )
            if branch_membership is None:
                raise PlatformPermissionException(
                    "The selected user does not have an active branch assignment for this branch."
                )

        # Reject obvious duplicate shifts in the same company+user+weekday.
        if (
            WeeklyShift.objects.filter(
                company=self._company,
                user_id=user_id,
                weekday=attrs["weekday"],
                start_time=start_time,
                end_time=end_time,
                active=True,
            ).exists()
        ):
            raise serializers.ValidationError(
                {"detail": "A weekly shift with the same slot already exists."}
            )

        attrs["branch"] = branch
        attrs["user_id_resolved"] = user_id
        return attrs
