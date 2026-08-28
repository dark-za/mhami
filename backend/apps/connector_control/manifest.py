from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="connector_control",
    dependencies=("audit", "identity", "tenancy"),
    permissions=("connector.enroll", "connector.read", "connector.revoke"),
    events_published=("connector.enrolled", "connector.revoked"),
)

