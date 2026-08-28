import os

from cryptography.fernet import Fernet

from .base import *  # noqa: F401,F403
from django.core.exceptions import ImproperlyConfigured

DEBUG = False
ALLOWED_HOSTS = list(
    dict.fromkeys(
        [
            *(host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if host.strip()),
            "localhost",
            "127.0.0.1",
            "api",
        ]
    )
)
if not any(host not in {"localhost", "127.0.0.1", "api"} for host in ALLOWED_HOSTS):
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must include the public hostname.")
if not os.getenv("MFA_ENCRYPTION_KEYS", "").strip():
    raise ImproperlyConfigured("MFA_ENCRYPTION_KEYS must contain an independent production key.")
try:
    for encryption_key in MFA_ENCRYPTION_KEYS:  # noqa: F405
        Fernet(encryption_key.encode("ascii"))
except (TypeError, ValueError) as exc:
    raise ImproperlyConfigured("MFA_ENCRYPTION_KEYS contains an invalid Fernet key.") from exc
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
