from __future__ import annotations

import logging
import traceback
from collections.abc import Callable, Mapping
from functools import wraps
from typing import Any, TypeVar

from django.conf import settings
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db.utils import IntegrityError
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
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
    
    if isinstance(exc, IntegrityError):
        logger.error("Database integrity error", exc_info=exc, extra={"request_id": get_request_id()})
        return Response(
            format_error_payload("PLATFORM-409", "Data integrity conflict."),
            status=409
        )
        
    if response is None:
        logger.error("Unhandled API exception", exc_info=exc, extra={"request_id": get_request_id()})
        message = "Internal Server Error"
        if getattr(settings, 'DEBUG', False):
            message = str(exc) + "\n" + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        return Response(
            format_error_payload("PLATFORM-001", message),
            status=500
        )

    code = "CORE-ERROR-001"

    message = "This action cannot be performed."

    # Return 401 instead of 403 for unauthenticated access
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        code = "NOT_AUTHENTICATED"
        message = str(exc.detail) if hasattr(exc, "detail") else "Authentication credentials were not provided."
        response.status_code = 401
    elif isinstance(exc, (PermissionDenied, PlatformPermissionException)):
        request = context.get("request") if isinstance(context, dict) else None
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            code = "NOT_AUTHENTICATED"
            message = "Authentication credentials were not provided."
            response.status_code = 401
        else:
            code = getattr(exc, "default_code", "CORE-FORBIDDEN-001").upper()
            message = str(exc.detail) if hasattr(exc, "detail") else "You do not have permission to perform this action."
    elif isinstance(exc, APIException):
        code = getattr(exc, "default_code", code).upper() if getattr(exc, "default_code", None) else code
        message = str(exc.detail)
    if isinstance(exc, ValidationError):
        code = "CORE-VALIDATION-001"
        message = str(exc.detail)
    response.data = format_error_payload(code, message)
    return response


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
    * Explicit ``ValueError`` instances are converted to
      ``PlatformAPIException(400)`` with the original business-rule message.
      ``KeyError`` and ``TypeError`` are treated as unexpected defects because
      their text can expose internal field names or service contracts.
    * Any other ``Exception`` is logged with ``exc_info=True`` and re-raised
      as a generic ``PlatformAPIException`` so we never leak traceback
      details to the client.
    """

    @wraps(view_method)
    def wrapper(self: Any, request: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return view_method(self, request, *args, **kwargs)
        except (PlatformAPIException, PlatformPermissionException, ValidationError):
            raise
        except DjangoPermissionDenied as exc:
            raise PlatformPermissionException(str(exc)) from exc
        except ValueError as exc:
            raise PlatformAPIException(str(exc)) from exc
        except (KeyError, TypeError) as exc:
            logger.exception("Unexpected service contract error in %s", view_method.__qualname__)
            raise PlatformAPIException(_UNEXPECTED_MESSAGE) from exc
        except Exception as exc:
            logger.exception("Unexpected error in %s", view_method.__qualname__)
            raise PlatformAPIException(_UNEXPECTED_MESSAGE) from exc

    return wrapper  # type: ignore[return-value]
