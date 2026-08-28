from .base import *  # noqa: F401,F403

DEBUG = False
# BE-06: the test suite disables the MFA enforcement middleware so
# individual tests do not have to enroll MFA for every privileged
# user. The dedicated test module
# ``apps.identity.tests.test_mfa_enforcement`` enables the middleware
# directly via ``override_settings``.
MFA_ENFORCEMENT_ENABLED = False
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "mhami-tests",
    }
}
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "registration_ip": "1000/minute",
    "login_ip": "1000/minute",
    "login_account": "1000/minute",
    "mfa_user": "1000/minute",
}
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    "backup_restore": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}
