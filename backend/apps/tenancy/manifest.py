from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="tenancy",
    dependencies=("platform_core", "identity"),
    permissions=("tenancy.manage_company",),
    events_published=("tenancy.company.created", "tenancy.company.updated"),
)

