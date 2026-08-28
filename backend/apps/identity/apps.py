from __future__ import annotations

from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class IdentityConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.identity"
    manifest = quick_manifest(
        slug="identity",
        dependencies=("platform_core",),
        permissions=("identity.manage_users",),
        events_published=("identity.user.created",),
    )
