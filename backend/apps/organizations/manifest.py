from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="organizations",
    dependencies=("platform_core", "identity", "tenancy"),
    permissions=("organizations.manage_branches", "organizations.manage_memberships"),
    events_published=("organizations.branch.created", "organizations.membership.updated"),
)

