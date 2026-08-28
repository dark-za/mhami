from __future__ import annotations

from apps.platform_core.apps import PlatformAppConfig
from apps.platform_core.registry import quick_manifest


class TasksConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tasks"
    manifest = quick_manifest(
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
