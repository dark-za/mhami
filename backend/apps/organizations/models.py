from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.platform_core.querysets import TenantManager
from apps.tenancy.models import Company


class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64)
    timezone = models.CharField(max_length=64, default="Asia/Riyadh")
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    geofence_radius = models.PositiveIntegerField(default=0)
    operational_day_cutoff = models.TimeField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "code"], name="organization_branch_unique_code")]


class JobRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="job_roles")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "code"], name="organization_job_role_unique_code")]


class CompanyRole(models.TextChoices):
    OWNER = "owner", "Owner"
    MONITOR = "monitor", "Quality Monitor"
    EMPLOYEE = "employee", "Employee"


class CompanyMembership(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_memberships")
    role = models.CharField(max_length=32, choices=CompanyRole.choices)
    active = models.BooleanField(default=True)
    active_from = models.DateTimeField(auto_now_add=True)
    active_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "user"], name="organization_company_membership_unique")]

    objects = TenantManager()


class UserBranchMembership(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="branch_memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="branch_memberships")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="memberships")
    job_role = models.ForeignKey(JobRole, on_delete=models.PROTECT, related_name="memberships")
    membership_type = models.CharField(max_length=32, default="primary")
    active = models.BooleanField(default=True)
    active_from = models.DateTimeField(auto_now_add=True)
    active_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(active=True),
                name="organization_one_active_branch_per_user",
            ),
        ]

    objects = TenantManager()


class WeeklyShift(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="weekly_shifts")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="weekly_shifts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weekly_shifts")
    weekday = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    active = models.BooleanField(default=True)

    objects = TenantManager()
