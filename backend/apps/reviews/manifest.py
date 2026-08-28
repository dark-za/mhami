from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="reviews",
    dependencies=("audit", "identity", "tenancy", "organizations", "tasks", "evidence"),
    permissions=(
        "reviews.queue.read",
        "reviews.dashboard.read",
        "reviews.policy.manage",
        "reviews.decision.create",
    ),
    events_published=("reviews.decision.created", "reviews.policy.updated"),
)

