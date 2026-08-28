from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from importlib import import_module
from typing import Iterable

from django.conf import settings


@dataclass(frozen=True, slots=True)
class ModuleManifest:
    slug: str
    name: str
    version: str
    requires_core: str
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    permissions: tuple[str, ...] = field(default_factory=tuple)
    events_published: tuple[str, ...] = field(default_factory=tuple)
    events_consumed: tuple[str, ...] = field(default_factory=tuple)
    healthcheck: str = ""
    config_schema_version: str = "1"


def quick_manifest(
    *,
    slug: str,
    name: str | None = None,
    version: str = "0.1.0",
    dependencies: tuple[str, ...] = (),
    permissions: tuple[str, ...] = (),
    events_published: tuple[str, ...] = (),
    events_consumed: tuple[str, ...] = (),
    healthcheck: str | None = None,
    config_schema_version: str = "1",
) -> ModuleManifest:
    """Build a ``ModuleManifest`` with sensible defaults.

    Defaults match the platform baseline (``requires_core=">=0.1,<1.0"``,
    ``config_schema_version="1"``) and infer the human-readable ``name`` and
    the ``healthcheck`` dotted path from ``slug`` when they are not provided
    explicitly. This removes the boilerplate from each module's ``manifest.py``.
    """
    return ModuleManifest(
        slug=slug,
        name=name or slug.replace("_", " ").title(),
        version=version,
        requires_core=">=0.1,<1.0",
        dependencies=dependencies,
        permissions=permissions,
        events_published=events_published,
        events_consumed=events_consumed,
        healthcheck=healthcheck or f"{slug}.health",
        config_schema_version=config_schema_version,
    )


class ModuleRegistryError(RuntimeError):
    pass


class ModuleCompatibilityError(ModuleRegistryError):
    pass


def _parse_core_range(range_expr: str) -> tuple[tuple[int, int], tuple[int, int]]:
    lower = (0, 0)
    upper = (999, 999)
    for piece in (part.strip() for part in range_expr.split(",") if part.strip()):
        if piece.startswith(">="):
            major, minor = piece[2:].split(".", 1)
            lower = (int(major), int(minor))
        elif piece.startswith(">"):
            major, minor = piece[1:].split(".", 1)
            lower = (int(major), int(minor) + 1)
        elif piece.startswith("<="):
            major, minor = piece[2:].split(".", 1)
            upper = (int(major), int(minor))
        elif piece.startswith("<"):
            major, minor = piece[1:].split(".", 1)
            upper = (int(major), int(minor))
    return lower, upper


def _core_version() -> tuple[int, int]:
    major, minor, *_rest = settings.PLATFORM_CORE_VERSION.split(".")
    return int(major), int(minor)


def _core_version_supported(manifest: ModuleManifest) -> bool:
    lower, upper = _parse_core_range(manifest.requires_core)
    core = _core_version()
    return lower <= core < upper


class ModuleRegistry:
    def __init__(self, manifests: Iterable[ModuleManifest]):
        self._manifests = {manifest.slug: manifest for manifest in manifests}

    @classmethod
    def discover(cls) -> "ModuleRegistry":
        manifests: list[ModuleManifest] = []
        seen: set[str] = set()
        # Primary path: discover via installed AppConfigs that carry a
        # ``manifest`` attribute. This is what :class:`PlatformAppConfig.ready`
        # populates.
        from django.apps import apps as global_apps

        for cfg in global_apps.get_app_configs():
            manifest = getattr(cfg, "manifest", None)
            if isinstance(manifest, ModuleManifest):
                manifests.append(manifest)
                seen.add(manifest.slug)
        # Fallback: legacy ``apps.<slug>.manifest`` modules. Useful while
        # modules migrate one at a time.
        for slug in settings.PLATFORM_MODULES:
            if slug in seen:
                continue
            try:
                module = import_module(f"apps.{slug}.manifest")
            except ModuleNotFoundError:
                continue
            manifest = getattr(module, "module_manifest", None)
            if not isinstance(manifest, ModuleManifest):
                raise ModuleRegistryError(f"Module {slug} does not expose module_manifest")
            manifests.append(manifest)
            seen.add(slug)
        registry = cls(manifests)
        registry.validate()
        return registry

    def register(self, manifest: ModuleManifest) -> None:
        """Add or replace a manifest in the registry (used by AppConfig.ready)."""
        self._manifests[manifest.slug] = manifest

    @classmethod
    def register_manifest(cls, manifest: ModuleManifest) -> None:
        """Register a manifest on the cached singleton.

        AppConfig.ready() runs before ``get_registry()`` is called, so we cannot
        rely on a pre-built instance. This helper makes the registration
        observable by :func:`get_registry` regardless of call order.
        """
        get_registry().register(manifest)

    @property
    def manifests(self) -> tuple[ModuleManifest, ...]:
        return tuple(self._manifests.values())

    def validate(self) -> None:
        for manifest in self._manifests.values():
            if not _core_version_supported(manifest):
                raise ModuleCompatibilityError(
                    f"Module {manifest.slug} requires incompatible core {manifest.requires_core}"
                )
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        for manifest in self._manifests.values():
            for dependency in manifest.dependencies:
                if dependency not in self._manifests:
                    raise ModuleCompatibilityError(
                        f"Module {manifest.slug} depends on missing module {dependency}"
                    )
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(slug: str) -> None:
            if slug in visited:
                return
            if slug in visiting:
                raise ModuleCompatibilityError("Circular module dependency detected")
            visiting.add(slug)
            for dependency in self._manifests[slug].dependencies:
                visit(dependency)
            visiting.remove(slug)
            visited.add(slug)

        for slug in self._manifests:
            visit(slug)

    def health_statuses(self) -> list[dict[str, str]]:
        return [
            {"slug": manifest.slug, "name": manifest.name, "status": "OK"}
            for manifest in self.manifests
        ]


@lru_cache(maxsize=1)
def get_registry() -> ModuleRegistry:
    return ModuleRegistry.discover()
