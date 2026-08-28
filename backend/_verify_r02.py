"""Quick verification script for R-02 manifest base."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
django.setup()

# 1) Test that quick_manifest factory works with minimal args
from apps.platform_core.registry import ModuleManifest, get_registry, quick_manifest  # noqa: E402

m = quick_manifest(slug="test_module")
assert isinstance(m, ModuleManifest)
assert m.slug == "test_module"
assert m.name == "Test Module"  # auto-inferred
assert m.version == "0.1.0"
assert m.requires_core == ">=0.1,<1.0"
assert m.healthcheck == "test_module.health"  # auto-inferred
assert m.config_schema_version == "1"
assert m.dependencies == ()
assert m.permissions == ()
print("1) quick_manifest minimal: OK")

# 2) Test that quick_manifest works with full args
m = quick_manifest(
    slug="ai_gateway",
    dependencies=("audit", "tenancy"),
    permissions=("ai.read", "ai.write"),
    events_published=("ai.test",),
    name="Custom AI Gateway Name",
    healthcheck="custom.path",
)
assert m.name == "Custom AI Gateway Name"  # explicit override
assert m.healthcheck == "custom.path"
assert m.dependencies == ("audit", "tenancy")
assert m.permissions == ("ai.read", "ai.write")
print("2) quick_manifest with full args: OK")

# 3) Test that registry discovers all 14 modules
registry = get_registry()
manifests = registry.manifests
assert len(manifests) == 14, f"expected 14, got {len(manifests)}"
slugs = sorted(m.slug for m in manifests)
expected = sorted(
    ["platform_core", "identity", "tenancy", "organizations", "tasks", "evidence",
     "reviews", "ai_gateway", "connector_control", "exports", "backups",
     "audit", "notifications", "pilot"]
)
assert slugs == expected, f"slugs mismatch: {slugs}"
print(f"3) registry.discover() returns all 14 modules: {slugs}")

# 4) Verify each manifest has correct inferred fields
for m in manifests:
    # name should equal slug.replace("_", " ").title()
    expected_name = m.slug.replace("_", " ").title()
    assert m.name == expected_name, f"{m.slug}: name={m.name!r} != {expected_name!r}"
    # healthcheck should equal "f'{slug}.health'"
    assert m.healthcheck == f"{m.slug}.health", f"{m.slug}: healthcheck={m.healthcheck!r}"
    # version default
    assert m.version == "0.1.0", f"{m.slug}: version={m.version!r}"
    # requires_core default
    assert m.requires_core == ">=0.1,<1.0", f"{m.slug}: requires_core={m.requires_core!r}"
    # config_schema_version default
    assert m.config_schema_version == "1", f"{m.slug}: config_schema_version={m.config_schema_version!r}"
print("4) All 14 manifests have correct defaults (name, healthcheck, version, etc.)")

# 5) Verify specific module properties
tenancy = next(m for m in manifests if m.slug == "tenancy")
assert tenancy.dependencies == ("platform_core", "identity")
assert tenancy.permissions == ("tenancy.manage_company",)
assert "tenancy.company.created" in tenancy.events_published
print(f"5) tenancy manifest: {tenancy}")

# 6) Verify registry health_statuses still works
statuses = registry.health_statuses()
assert len(statuses) == 14
for s in statuses:
    assert "slug" in s and "name" in s and "status" in s
print(f"6) registry.health_statuses() works: {len(statuses)} entries")

# 7) Verify registry validation passes
registry.validate()
print("7) registry.validate() passes")

print("\nALL CHECKS PASSED")
