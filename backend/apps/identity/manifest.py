from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="identity",
    dependencies=("platform_core",),
    permissions=("identity.manage_users",),
    events_published=("identity.user.created",),
)

