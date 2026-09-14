from .base import CSRF_TRUSTED_ORIGINS as base_csrf_trusted_origins
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend", "api"]
CSRF_TRUSTED_ORIGINS = base_csrf_trusted_origins or ["http://localhost:5173", "http://127.0.0.1:5173"]
