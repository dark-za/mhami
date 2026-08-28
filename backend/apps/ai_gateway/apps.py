from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class AiGatewayConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_gateway"
    manifest = quick_manifest(
        slug="ai_gateway",
        dependencies=("audit", "identity", "tenancy", "organizations", "evidence", "reviews"),
        permissions=(
            "ai.provider.read",
            "ai.provider.write",
            "ai.criteria.read",
            "ai.criteria.write",
            "ai.analysis.run",
        ),
        events_published=("ai.provider.updated", "ai.criteria.updated", "ai.analysis.created"),
    )
