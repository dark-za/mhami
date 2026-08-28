from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class ReviewsConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reviews"
    manifest = quick_manifest(
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
