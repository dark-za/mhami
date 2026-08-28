from __future__ import annotations

from apps.identity.models import User


def test_user_manager_creates_user():
    user = User(login_id="owner")
    assert user.login_id == "owner"
