from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from django.core.management import call_command
from django.db import connection
from django.test import override_settings

from apps.identity.fields import ENCRYPTED_VALUE_PREFIX, _cipher
from apps.identity.models import MfaEnrollment, MfaMethodType


pytestmark = pytest.mark.django_db


def _stored_secret(enrollment_id) -> str:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT secret FROM identity_mfaenrollment WHERE id = %s",
            [str(enrollment_id).replace("-", "")],
        )
        return cursor.fetchone()[0]


def test_mfa_secret_is_encrypted_at_rest_and_decrypted_by_the_model(make_user):
    user = make_user(login_id="encrypted-mfa")
    enrollment = MfaEnrollment.objects.create(
        user=user,
        method_type=MfaMethodType.TOTP,
        secret="JBSWY3DPEHPK3PXP",
    )

    stored = _stored_secret(enrollment.id)
    enrollment.refresh_from_db()

    assert stored.startswith(ENCRYPTED_VALUE_PREFIX)
    assert "JBSWY3DPEHPK3PXP" not in stored
    assert enrollment.secret == "JBSWY3DPEHPK3PXP"


def test_mfa_secret_rotation_reencrypts_with_the_active_key(make_user):
    old_key = Fernet.generate_key().decode("ascii")
    new_key = Fernet.generate_key().decode("ascii")
    user = make_user(login_id="rotated-mfa")

    with override_settings(MFA_ENCRYPTION_KEYS=[old_key]):
        _cipher.cache_clear()
        enrollment = MfaEnrollment.objects.create(
            user=user,
            method_type=MfaMethodType.TOTP,
            secret="JBSWY3DPEHPK3PXP",
        )
        old_ciphertext = _stored_secret(enrollment.id)

    with override_settings(MFA_ENCRYPTION_KEYS=[new_key, old_key]):
        _cipher.cache_clear()
        call_command("rotate_mfa_secrets", verbosity=0)
        new_ciphertext = _stored_secret(enrollment.id)

    with override_settings(MFA_ENCRYPTION_KEYS=[new_key]):
        _cipher.cache_clear()
        enrollment.refresh_from_db()
        assert enrollment.secret == "JBSWY3DPEHPK3PXP"

    _cipher.cache_clear()
    assert new_ciphertext != old_ciphertext


def test_rotation_command_encrypts_legacy_plaintext_rows(make_user):
    user = make_user(login_id="legacy-mfa")
    enrollment = MfaEnrollment.objects.create(
        user=user,
        method_type=MfaMethodType.TOTP,
        secret="JBSWY3DPEHPK3PXP",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE identity_mfaenrollment SET secret = %s WHERE id = %s",
            ["LEGACYPLAINTEXT", str(enrollment.id).replace("-", "")],
        )

    enrollment.refresh_from_db()
    assert enrollment.secret == "LEGACYPLAINTEXT"
    call_command("rotate_mfa_secrets", verbosity=0)

    stored = _stored_secret(enrollment.id)
    enrollment.refresh_from_db()
    assert stored.startswith(ENCRYPTED_VALUE_PREFIX)
    assert enrollment.secret == "LEGACYPLAINTEXT"
