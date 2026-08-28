from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="backups",
    dependencies=("audit", "identity", "tenancy", "organizations", "tasks", "evidence", "reviews", "exports", "ai_gateway", "connector_control"),
    permissions=("backups.read", "backups.write", "backups.restore"),
    events_published=("backup.requested", "backup.completed", "backup.restore.completed"),
)

