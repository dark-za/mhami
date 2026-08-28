from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="audit",
    dependencies=("platform_core",),
    events_consumed=("core.health.changed", "identity.user.created"),
)

