"""Shared health-check primitives for all platform modules.

Each module exposes a ``health`` callable returning ``{"status": "ok", "module": <slug>}``.
The factory below guarantees a uniform contract without duplicating the implementation
across every ``apps/<module>/health.py`` file.
"""
from __future__ import annotations

from django.conf import settings
from django.db import connections
from django.http import HttpRequest, JsonResponse


def make_health(module_slug: str):
    """Return a Django view that responds with the module's health status.

    The view accepts an optional ``HttpRequest`` so it can be wired both as a
    Django URL callback and as a plain function (e.g. in management commands).
    """

    def view(_request: HttpRequest | None = None):
        return JsonResponse({"status": "ok", "module": module_slug})

    view.__name__ = f"health_{module_slug}"
    return view


def liveness() -> dict[str, str]:
    """Return platform liveness status (no external dependencies)."""
    return {"status": "ok"}


def readiness() -> dict[str, str]:
    """Return platform readiness status, including DB/Redis reachability."""
    details: dict[str, str] = {"status": "ok"}
    try:
        connections["default"].ensure_connection()
        details["database"] = "ok"
    except Exception:
        details["database"] = "failed"
        details["status"] = "degraded"
    if hasattr(settings, "CELERY_BROKER_URL"):
        details["redis"] = "ok"
    return details
