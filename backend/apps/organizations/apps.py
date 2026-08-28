from __future__ import annotations

from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class OrganizationsConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.organizations"
    manifest = quick_manifest(
        slug="organizations",
        dependencies=("platform_core", "identity", "tenancy"),
        permissions=("organizations.manage_branches", "organizations.manage_memberships"),
        events_published=("organizations.branch.created", "organizations.membership.updated"),
    )
