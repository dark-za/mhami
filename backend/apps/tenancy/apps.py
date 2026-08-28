from __future__ import annotations

from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class TenancyConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tenancy"
    manifest = quick_manifest(
        slug="tenancy",
        dependencies=("platform_core", "identity"),
        permissions=("tenancy.manage_company",),
        events_published=("tenancy.company.created", "tenancy.company.updated"),
    )
