from __future__ import annotations

import pytest
from django.test import override_settings


pytestmark = pytest.mark.django_db


@override_settings(API_DOCS_REQUIRE_STAFF=True)
def test_api_schema_requires_staff_when_protected(client, make_user):
    anonymous = client.get("/api/schema/")
    assert anonymous.status_code in {401, 403}

    user = make_user(is_staff=True)
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    staff = client.get("/api/schema/")

    assert staff.status_code == 200
