from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="notifications",
    dependencies=("platform_core", "audit", "identity", "tenancy"),
    permissions=("notifications.read", "notifications.write"),
    events_published=("notification.created", "notification.read"),
    events_consumed=("backup.completed", "backup.restore.completed", "exports.completed"),
)
