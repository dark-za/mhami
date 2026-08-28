from __future__ import annotations

from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class NotificationsConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    manifest = quick_manifest(
        slug="notifications",
        dependencies=("platform_core", "audit", "identity", "tenancy"),
        permissions=("notifications.read", "notifications.write"),
        events_published=("notification.created", "notification.read"),
        events_consumed=("backup.completed", "backup.restore.completed", "exports.completed"),
    )