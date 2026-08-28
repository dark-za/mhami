"""Platform-core ``AppConfig`` shared with every business module.

Every ``apps/<module>/apps.py`` file declares a config class that inherits
from :class:`PlatformAppConfig` and supplies a ``manifest`` attribute. The
``ready()`` hook then registers that manifest with the platform registry, so
modules no longer need a separate ``manifest.py`` file.

Example::

    from apps.platform_core.apps import PlatformAppConfig
    from apps.platform_core.registry import quick_manifest

    class TenancyConfig(PlatformAppConfig):
        name = "apps.tenancy"
        manifest = quick_manifest(
            slug="tenancy",
            dependencies=("platform_core", "identity"),
            permissions=("tenancy.manage_company",),
        )
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import AppConfig

from .registry import quick_manifest

if TYPE_CHECKING:
    from .registry import ModuleManifest


class PlatformAppConfig(AppConfig):
    """Base ``AppConfig`` for every business module.

    Subclasses override the ``manifest`` class attribute with a
    :class:`ModuleManifest` instance (typically produced by
    :func:`quick_manifest`). When Django calls :meth:`ready`, the manifest is
    published to the in-process :class:`~apps.platform_core.registry.ModuleRegistry`
    so the module becomes part of the platform as soon as its app loads.
    """

    default_auto_field = "django.db.models.BigAutoField"
    manifest: "ModuleManifest | None" = None

    def ready(self) -> None:
        super().ready()
        if self.manifest is None:
            return
        from .registry import ModuleRegistry

        ModuleRegistry.register_manifest(self.manifest)


class PlatformCoreConfig(PlatformAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.platform_core"
    verbose_name = "Platform Core"
    manifest = quick_manifest(
        slug="platform_core",
        events_published=("core.health.changed",),
    )
