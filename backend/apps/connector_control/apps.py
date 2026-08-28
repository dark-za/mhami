from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class ConnectorControlConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.connector_control"
    manifest = quick_manifest(
        slug="connector_control",
        dependencies=("audit", "identity", "tenancy"),
        permissions=("connector.enroll", "connector.read", "connector.revoke"),
        events_published=("connector.enrolled", "connector.revoked"),
    )
