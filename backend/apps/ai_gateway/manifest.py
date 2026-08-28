from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
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

