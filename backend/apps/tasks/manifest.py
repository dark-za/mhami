from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="tasks",
    dependencies=("audit", "identity", "tenancy", "organizations"),
    permissions=(
        "tasks.template.read",
        "tasks.template.write",
        "tasks.instance.read",
        "tasks.instance.write",
    ),
    events_published=("tasks.instance.created", "tasks.instance.updated"),
)

