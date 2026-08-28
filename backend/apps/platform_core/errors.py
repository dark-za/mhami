from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from functools import wraps
from typing import Any, TypeVar

from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .request_id import get_request_id

logger = logging.getLogger(__name__)


class PlatformAPIException(APIException):
    status_code = 400
    default_detail = "This action cannot be performed."
    default_code = "CORE-ERROR-001"


class PlatformPermissionException(APIException):
    status_code = 403
    default_detail = "You do not have permission to perform this action."
    default_code = "CORE-FORBIDDEN-001"


class PlatformLegalBlockException(APIException):
    """Raised when an action is blocked for legal reasons (HTTP 451).

    Used by the compliance module to surface a missing current legal
    acceptance. The standard ``451 Unavailable For Legal Reasons`` status
    keeps the legal block distinct from a permission failure (403) and
    from a server error (5xx). The exception accepts a list of missing
    acceptance kinds and exposes them through :attr:`missing_kinds` so
    the client can route the user to the acceptance endpoint.
    """

    status_code = 451
    default_detail = "Action is blocked until current legal acceptances are recorded."
    default_code = "CORE-LEGAL-001"

    def __init__(self, missing_kinds: list[str] | None = None, detail: str | None = None):
        self.missing_kinds = list(missing_kinds or [])
        if detail is None and self.missing_kinds:
            detail = (
                "Action is blocked until current legal acceptances are recorded for: "
                + ", ".join(self.missing_kinds)
            )
        super().__init__(detail=detail or self.default_detail)


def format_error_payload(code: str, message: str) -> dict[str, Mapping[str, str]]:
    return {"error": {"code": code, "message": message, "request_id": get_request_id()}}


def platform_exception_handler(exc: Exception, context: dict[str, object]) -> Response | None:
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    code = "CORE-ERROR-001"
    message = "This action cannot be performed."
    if isinstance(exc, APIException):
        code = getattr(exc, "default_code", code).upper() if getattr(exc, "default_code", None) else code
        message = str(exc.detail)
    if isinstance(exc, ValidationError):
        code = "CORE-VALIDATION-001"
        message = "One or more fields are invalid."
    response.data = format_error_payload(code, message)
    return response


# Exceptions that the service layer is expected to raise and that we want to
# pass through as ``PlatformAPIException`` without losing their ``str(exc)``
# message. Anything else is treated as an unexpected error and gets a
# generic, non-leaky message.
_SERVICE_ERRORS: tuple[type[BaseException], ...] = (ValueError, KeyError, TypeError)
_UNEXPECTED_MESSAGE = "The action could not be completed."

_F = TypeVar("_F", bound=Callable[..., Any])


def platform_service_call(view_method: _F) -> _F:
    """Wrap a view method so service-layer exceptions become API errors.

    The decorator centralises the try/except pattern that almost every
    endpoint used to inline::

        @platform_service_call
        def post(self, request):
            obj = service.do(...)  # may raise ValueError → 400
            return Response(...)

    Behavior:

    * ``PlatformAPIException`` and its subclasses re-raise untouched so
      explicit 4xx handling keeps its status code.
    * ``ValueError`` / ``KeyError`` / ``TypeError`` raised by the service
      layer are converted to ``PlatformAPIException(400)`` with the original
      message — these are the "expected business" errors.
    * Any other ``Exception`` is logged with ``exc_info=True`` and re-raised
      as a generic ``PlatformAPIException`` so we never leak traceback
      details to the client.
    """

    @wraps(view_method)
    def wrapper(self: Any, request: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return view_method(self, request, *args, **kwargs)
        except (PlatformAPIException, PlatformPermissionException):
            raise
        except _SERVICE_ERRORS as exc:
            raise PlatformAPIException(str(exc)) from exc
        except Exception as exc:
            logger.exception("Unexpected error in %s", view_method.__qualname__)
            raise PlatformAPIException(_UNEXPECTED_MESSAGE) from exc

    return wrapper  # type: ignore[return-value]
