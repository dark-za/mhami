from __future__ import annotations

from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class AuditConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    manifest = quick_manifest(
        slug="audit",
        dependencies=("platform_core",),
        events_consumed=("core.health.changed", "identity.user.created"),
    )
