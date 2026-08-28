from .registry import quick_manifest

module_manifest = quick_manifest(
    slug="platform_core",
    events_published=("core.health.changed",),
)

