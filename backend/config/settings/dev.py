from .base import CSRF_TRUSTED_ORIGINS as base_csrf_trusted_origins
from .base import ALLOWED_HOSTS as base_allowed_hosts
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = list(dict.fromkeys((base_allowed_hosts or []) + ["localhost", "127.0.0.1", "backend", "api", "192.168.8.3", "*"]))
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys((base_csrf_trusted_origins or []) + [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.8.3:5173",
]))

