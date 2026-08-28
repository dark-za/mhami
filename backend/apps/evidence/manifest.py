from apps.platform_core.registry import quick_manifest

module_manifest = quick_manifest(
    slug="evidence",
    dependencies=("audit", "identity", "tenancy", "organizations", "tasks"),
    permissions=(
        "evidence.capture.create",
        "evidence.submit.create",
        "evidence.read",
        "evidence.issue.create",
        "evidence.issue.reply",
    ),
    events_published=("evidence.capture.created", "evidence.submitted", "evidence.issue.created"),
)

