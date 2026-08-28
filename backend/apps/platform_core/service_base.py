"""Service-layer decorators that bundle transactional safety and audit logging.

The platform's service functions follow a recurring pattern::

    @transaction.atomic
    def do_thing(...):
        obj = ...
        record_audit_event(event_type=..., target_id=obj.id, ...)
        return obj

The :func:`audited_service` decorator captures that pattern in a single
declaration, removing 5-7 lines of boilerplate from every write path and
making the contract (event type, target type) explicit at the function level.
"""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from django.db import transaction

from apps.audit.services import record_audit_event

_P = ParamSpec("_P")
_R = TypeVar("_R")


def _model_to_payload(obj: Any) -> dict[str, Any]:
    """Best-effort conversion of a model instance to a dict for audit logs.

    UUIDs and datetimes are coerced to JSON-friendly primitives so the result
    can be stored in the ``AuditEvent.after`` JSON column.
    """
    if obj is None:
        return {}
    if hasattr(obj, "to_dict"):
        return _jsonify(obj.to_dict())
    if hasattr(obj, "__dict__"):
        return _jsonify(
            {
                key: value
                for key, value in obj.__dict__.items()
                if not key.startswith("_") and key not in {"_state", "_django_manager"}
            }
        )
    return {}


def _jsonify(value: Any) -> Any:
    """Recursively convert UUIDs, datetimes, and other primitives to JSON-safe values."""
    import datetime
    import uuid
    from decimal import Decimal

    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonify(item) for item in value]
    return value


def audited_service(
    *,
    event_type: str,
    target_type: str,
    actor_id: str | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Wrap a service function with atomic + audit-event recording.

    The decorated function runs inside a database transaction. If it returns
    a value (single model or tuple) the decorator records an ``AuditEvent``
    with the event_type and target_type supplied here. The wrapped function
    stays focused on business logic.

    Example::

        @audited_service(event_type="tenancy.company.created", target_type="Company")
        def register_company(...):
            company = Company.objects.create(...)
            owner = User.objects.create_user(...)
            return company, owner
    """

    def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
        @wraps(func)
        @transaction.atomic
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            result = func(*args, **kwargs)
            target_id, after_payload = _extract_target(result, target_type)
            record_audit_event(
                event_type=event_type,
                target_type=target_type,
                target_id=target_id,
                actor_id=actor_id,
                after=after_payload,
            )
            return result

        return wrapper

    return decorator


def _extract_target(result: Any, target_type: str) -> tuple[str, dict[str, Any]]:
    """Pull a target id and payload from a service return value.

    Services commonly return a single model instance, a tuple of
    (model, ...), or ``None``. This helper normalises all three into the
    ``(target_id, after_payload)`` pair that :func:`record_audit_event` needs.
    """
    primary = _first_model(result)
    if primary is None:
        return "", {}
    target_id = str(getattr(primary, "id", ""))
    return target_id, _model_to_payload(primary)


def _first_model(result: Any) -> Any:
    if result is None:
        return None
    if isinstance(result, tuple):
        for item in result:
            if hasattr(item, "id"):
                return item
        return None
    if hasattr(result, "id"):
        return result
    return None
