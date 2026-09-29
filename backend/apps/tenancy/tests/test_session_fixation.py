import pytest
from django.core.management import call_command

@pytest.mark.django_db
def test_session_fixation_guard(client):
    """Ensure session key cycles after login to prevent session fixation."""
    call_command(
        "provision_owner",
        organization_name="Acme",
        owner_login_id="owner",
        owner_display_name="Owner",
        password="Mha!mi-Test-2026#",
    )
    client.session["pre_login"] = "value"
    client.session.save()
    old_session_key = client.session.session_key

    response = client.post(
        "/api/v1/auth/login",
        {"login_id": "owner", "password": "Mha!mi-Test-2026#"},
        content_type="application/json",
    )
    assert response.status_code == 200

    new_session_key = client.session.session_key
    assert old_session_key != new_session_key
    assert new_session_key is not None
