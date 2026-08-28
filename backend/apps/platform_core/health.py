"""Platform-core health checks, re-exported from the shared base."""
from __future__ import annotations

from .health_base import liveness, readiness, make_health

# Re-exported for backward compatibility with existing imports
# (apps.platform_core.health.live_status / ready_status).
live_status = liveness
ready_status = readiness

# This module is the platform core itself, so it also exposes a default health view.
health = make_health("platform_core")

