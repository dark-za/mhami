"""Organizations module health check, generated from the shared base.

The previous implementation exposed a ``status`` callable, but the manifest
contract and registry use ``module.health``. This file keeps a thin
``status`` alias for any out-of-tree consumer during the deprecation window.
"""
from apps.platform_core.health_base import make_health

health = make_health("organizations")
status = health  # backward compatibility alias

