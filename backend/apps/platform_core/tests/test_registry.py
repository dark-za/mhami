from __future__ import annotations

import pytest

from apps.platform_core.registry import ModuleCompatibilityError, ModuleManifest, ModuleRegistry


def test_module_registry_accepts_valid_dependency_graph():
    registry = ModuleRegistry(
        [
            ModuleManifest(
                slug="platform_core",
                name="Platform Core",
                version="0.1.0",
                requires_core=">=0.1,<1.0",
            ),
            ModuleManifest(
                slug="audit",
                name="Audit",
                version="0.1.0",
                requires_core=">=0.1,<1.0",
                dependencies=("platform_core",),
            ),
        ]
    )
    registry.validate()


def test_module_registry_rejects_circular_dependencies():
    registry = ModuleRegistry(
        [
            ModuleManifest(
                slug="alpha",
                name="Alpha",
                version="0.1.0",
                requires_core=">=0.1,<1.0",
                dependencies=("beta",),
            ),
            ModuleManifest(
                slug="beta",
                name="Beta",
                version="0.1.0",
                requires_core=">=0.1,<1.0",
                dependencies=("alpha",),
            ),
        ]
    )
    with pytest.raises(ModuleCompatibilityError):
        registry.validate()


def test_module_registry_rejects_incompatible_core():
    registry = ModuleRegistry(
        [
            ModuleManifest(
                slug="alpha",
                name="Alpha",
                version="0.1.0",
                requires_core=">=2.0,<3.0",
            ),
        ]
    )
    with pytest.raises(ModuleCompatibilityError):
        registry.validate()
