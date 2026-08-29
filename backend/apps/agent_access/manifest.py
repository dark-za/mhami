from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="agent_access",
    dependencies=("audit", "identity", "tenancy"),
    permissions=("agent.grant", "agent.read", "agent.revoke"),
    events_published=("agent.grant.created", "agent.grant.revoked", "agent.action.recorded"),
)
