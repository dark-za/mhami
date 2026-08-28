from __future__ import annotations

import structlog


def get_logger(module: str):
    return structlog.get_logger(module=module)
