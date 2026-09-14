from __future__ import annotations

import pytest

from apps.platform_core.errors import PlatformAPIException, format_error_payload, platform_service_call


def test_standard_error_shape_helper():
    payload = format_error_payload("CORE-ERROR-001", "This action cannot be performed.")
    assert payload["error"]["code"] == "CORE-ERROR-001"
    assert payload["error"]["message"] == "This action cannot be performed."


def test_service_contract_errors_do_not_leak_internal_details():
    class BrokenServiceView:
        @platform_service_call
        def get(self, request):
            raise KeyError("private_model_field")

    with pytest.raises(PlatformAPIException) as exc_info:
        BrokenServiceView().get(request=None)

    assert str(exc_info.value.detail) == "The action could not be completed."
