from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class ExportsConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.exports"
    manifest = quick_manifest(
        slug="exports",
        dependencies=("audit", "identity", "tenancy", "organizations", "tasks", "evidence", "reviews"),
        permissions=("exports.request", "exports.read", "exports.download", "exports.policy.manage"),
        events_published=("exports.requested", "exports.completed", "exports.downloaded"),
    )
