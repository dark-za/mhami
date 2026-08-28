from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="pilot",
    dependencies=("audit", "identity", "tenancy", "organizations", "tasks", "evidence", "reviews", "ai_gateway", "connector_control", "exports", "backups"),
    permissions=("pilot.read", "pilot.write", "pilot.report.write"),
    events_published=("pilot.report.created", "pilot.change.requested"),
)

