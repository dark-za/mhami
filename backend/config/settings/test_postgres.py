"""Opt-in PostgreSQL tests; pytest creates and destroys the dedicated test database."""

from .test import *  # noqa: F401,F403
from .base import DATABASES as BASE_DATABASES
from .test import DATABASES as TEST_DATABASES
from typing import Any

DATABASES: dict[str, Any] = {  # type: ignore[no-redef]
    **TEST_DATABASES,
    "default": {
        **BASE_DATABASES["default"],
        "NAME": "mhami_regression",
        "TEST": {"NAME": "test_mhami_regression"},
    },
}
