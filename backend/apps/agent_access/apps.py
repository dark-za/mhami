from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class AgentAccessConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.agent_access"
    manifest = quick_manifest(
        slug="agent_access",
        dependencies=("audit", "identity", "tenancy"),
        permissions=("agent.grant", "agent.read", "agent.revoke"),
        events_published=("agent.grant.created", "agent.grant.revoked", "agent.action.recorded"),
    )
