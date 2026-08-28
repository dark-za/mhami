"""AppConfig for the compliance module."""

from __future__ import annotations

from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class ComplianceConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.compliance"
    verbose_name = "Compliance"
    manifest = quick_manifest(
        slug="compliance",
        dependencies=("platform_core", "tenancy", "identity"),
        permissions=("compliance.manage_ropa", "compliance.manage_dsr"),
        events_published=(
            "compliance.ropa.published",
            "compliance.dsr.submitted",
            "compliance.dsr.decided",
        ),
    )
