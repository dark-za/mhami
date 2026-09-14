"""Regression for drf-spectacular enum naming overrides.

Ensures the four previously hash-derived or duplicate enum names are now
stable, meaningful component names and that the schema generates without
warnings. The test intentionally checks values, not hash strings.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _generate_schema() -> dict:
    import tempfile
    from pathlib import Path

    import yaml
    from django.core.management import call_command

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        call_command("spectacular", "--file", str(tmp_path), verbosity=0)
        data = yaml.safe_load(tmp_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        return data
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def test_enum_overrides_produce_stable_names():
    schema = _generate_schema()
    schemas = schema.get("components", {}).get("schemas", {})
    assert schemas, "schema should contain components.schemas"

    # Stable names introduced via ENUM_NAME_OVERRIDES
    assert "ExitDecisionEnum" in schemas
    assert schemas["ExitDecisionEnum"]["enum"] == [
        "approved",
        "conditional",
        "rejected",
        "deferred",
    ]

    assert "BackupStatusEnum" in schemas
    assert schemas["BackupStatusEnum"]["enum"] == [
        "requested",
        "completed",
        "failed",
        "restored",
    ]

    assert "ConnectorHealthStatusEnum" in schemas
    assert schemas["ConnectorHealthStatusEnum"]["enum"] == [
        "healthy",
        "degraded",
        "offline",
    ]

    assert schemas["AgentGrantStatusEnum"]["enum"] == [
        "active",
        "revoked",
        "expired",
    ]

    assert schemas["TaskRequestKindEnum"]["enum"] == [
        "cancellation",
        "unable_to_complete",
        "task_suggestion",
        "transfer",
    ]
    assert schemas["TaskRequestStatusEnum"]["enum"] == [
        "pending",
        "approved",
        "rejected",
    ]

    # Hash-derived names must not reappear; DecisionTypeEnum is a legitimate
    # non-hash enum and is allowed.
    hash_names = {"Decision0b3Enum", "Decision4e8Enum", "Status40eEnum"}
    for name in hash_names:
        assert name not in schemas, f"hash enum {name} should be replaced by override"

    # Duplicate health enums were collapsed to the single canonical name.
    assert "HealthStatusEnum" not in schemas
    assert "ProviderStatusEnum" not in schemas

    # Verify the overridden enums are actually referenced where expected.
    assert schemas["BackupRun"]["properties"]["status"]["$ref"].endswith(
        "BackupStatusEnum"
    )
    assert schemas["RestoreRun"]["properties"]["status"]["$ref"].endswith(
        "BackupStatusEnum"
    )
    assert schemas["ExitDecision"]["properties"]["decision"]["$ref"].endswith(
        "ExitDecisionEnum"
    )
    assert schemas["TenantConnectorEnrollment"]["properties"]["health_status"][
        "$ref"
    ].endswith("ConnectorHealthStatusEnum")
    assert schemas["ConnectorHeartbeat"]["properties"]["provider_status"][
        "$ref"
    ].endswith("ConnectorHealthStatusEnum")
    assert schemas["AgentGrant"]["properties"]["status"]["$ref"].endswith(
        "AgentGrantStatusEnum"
    )
    assert schemas["TaskRequest"]["properties"]["kind"]["$ref"].endswith(
        "TaskRequestKindEnum"
    )
    assert schemas["TaskRequest"]["properties"]["status"]["$ref"].endswith(
        "TaskRequestStatusEnum"
    )


def test_schema_has_no_enum_naming_warnings(monkeypatch):
    """Ensure the enum post-processing hook does not emit the four known warnings."""

    warnings: list[str] = []

    def fake_warn(msg, *args, **kwargs):  # noqa: ANN001, ANN202
        warnings.append(str(msg))

    monkeypatch.setattr("drf_spectacular.hooks.warn", fake_warn)
    monkeypatch.setattr("drf_spectacular.plumbing.warn", fake_warn)

    _generate_schema()

    enum_warnings = [w for w in warnings if "enum naming" in w or "multiple names" in w]
    assert enum_warnings == [], f"unexpected enum warnings: {enum_warnings}"
