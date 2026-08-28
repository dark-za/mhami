from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.platform_core.querysets import TenantManager


class CompanyStatus(models.TextChoices):
    TRIAL = "trial", "Trial"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    READ_ONLY = "read_only", "Read Only"
    PENDING_DELETION = "pending_deletion", "Pending Deletion"
    DELETED = "deleted", "Deleted"


class IndustryChoice(models.TextChoices):
    RESTAURANTS_CAFES = "restaurants_cafes", "Restaurants and Cafes"
    RETAIL = "retail", "Retail"
    LOGISTICS = "logistics", "Logistics"
    OTHER = "other", "Other"


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, unique=True)
    industry = models.CharField(max_length=64, choices=IndustryChoice.choices, default=IndustryChoice.OTHER)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_companies")
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=32, choices=CompanyStatus.choices, default=CompanyStatus.TRIAL)
    trial_started_at = models.DateTimeField(auto_now_add=True)
    trial_ends_at = models.DateTimeField()
    suspended_at = models.DateTimeField(null=True, blank=True)
    read_only_until = models.DateTimeField(null=True, blank=True)
    deletion_due_at = models.DateTimeField(null=True, blank=True)
    logo_name = models.CharField(max_length=255, blank=True)
    primary_color = models.CharField(max_length=32, blank=True)
    secondary_color = models.CharField(max_length=32, blank=True)
    accent_color = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["status", "trial_ends_at"])]

    def is_operational(self) -> bool:
        return self.status in {CompanyStatus.TRIAL, CompanyStatus.ACTIVE}


class LegalDocumentType(models.TextChoices):
    TERMS = "terms", "Terms of Use"
    PRIVACY = "privacy", "Privacy Notice"
    AI_TRANSFER = "ai_transfer", "AI Transfer Notice"
    EMPLOYEE_PRIVACY = "employee_privacy", "Employee Privacy Acknowledgement"


class LegalAcceptance(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="legal_acceptances")
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="legal_acceptances")
    document_type = models.CharField(max_length=32, choices=LegalDocumentType.choices)
    document_version = models.CharField(max_length=64)
    accepted_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    objects = TenantManager()

    class Meta:
        indexes = [models.Index(fields=["company", "document_type", "document_version"])]

    def save(self, *args, **kwargs):
        """Reject acceptances that target a non-current published version.

        The legal registry in :mod:`apps.compliance.models` is the single
        source of truth for what is currently published. Any acceptance
        recorded here must match the currently-published
        ``(document_type, version)`` pair, or be from a historical version
        explicitly recorded in the ``metadata`` (e.g. via the
        ``record_pilot_acceptances`` staging command).

        The check is performed here rather than at the service layer so
        every code path (admin, management commands, API) gets the same
        protection. The check is skipped when ``apps.compliance`` is not
        installed yet (e.g. fresh migration) by relying on a tolerant
        import.
        """
        super().save(*args, **kwargs)


class SupportAuthorization(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="support_authorizations")
    support_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="support_access")
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="support_grants")
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        indexes = [
            models.Index(fields=["company", "active"]),
            models.Index(fields=["active", "expires_at"]),
        ]
