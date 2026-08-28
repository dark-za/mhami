"""C-04 regression tests: Bootstrap endpoint must issue a csrftoken cookie.

The frontend's ``fetchBootstrap`` and ``ensureCsrfToken`` helpers rely on
the Django response setting the cookie. Without it, every mutation
request from the SPA would 403 on the first session.

The tests use the Django test client (which goes through the full
middleware stack) so we exercise the same code path as a browser.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def test_bootstrap_endpoint_is_public_and_sets_csrf_cookie(client):
    response = client.get("/api/v1/bootstrap")
    assert response.status_code == 200
    csrf_cookie = response.cookies.get("csrftoken")
    assert csrf_cookie is not None, "csrftoken cookie must be issued"
    assert csrf_cookie.value, "csrftoken value must not be empty"


def test_bootstrap_legacy_alias_sets_csrf_cookie(client):
    response = client.get("/api/v1/platform/bootstrap/legacy")
    assert response.status_code == 200
    csrf_cookie = response.cookies.get("csrftoken")
    assert csrf_cookie is not None
    assert csrf_cookie.value


def test_unsafe_request_without_csrf_token_is_rejected(client):
    # Without the csrftoken cookie a POST to a CSRF-protected endpoint
    # is rejected with 403, which is the Django default behaviour. The
    # assertion pins that behaviour so a future refactor that drops the
    # protection is caught.
    response = client.post(
        "/api/v1/auth/login",
        data={"company_code": "x", "login_id": "y", "password": "z"},
        content_type="application/json",
    )
    assert response.status_code == 403
    assert "CSRF" in (response.content.decode("utf-8") or "").upper() or "csrf" in (
        response.content.decode("utf-8") or ""
    ).lower()
