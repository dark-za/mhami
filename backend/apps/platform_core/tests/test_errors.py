from __future__ import annotations

from apps.platform_core.errors import format_error_payload


def test_standard_error_shape_helper():
    payload = format_error_payload("CORE-ERROR-001", "This action cannot be performed.")
    assert payload["error"]["code"] == "CORE-ERROR-001"
    assert payload["error"]["message"] == "This action cannot be performed."
