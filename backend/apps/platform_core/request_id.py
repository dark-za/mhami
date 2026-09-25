from __future__ import annotations

import uuid
from contextvars import ContextVar
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str:
    current = request_id_var.get()
    if current:
        return current
    generated = str(uuid4())
    request_id_var.set(generated)
    return generated


def sanitize_request_id(raw_id: str | None) -> str:
    """Return a valid UUID string for ``raw_id``, or a fresh UUID.

    Incoming ``X-Request-ID`` headers are attacker-controlled. Only a
    parseable UUID is accepted so foreign values cannot pollute the
    HMAC-protected audit trail; anything else is replaced with a
    newly generated identifier.
    """
    if not raw_id:
        return str(uuid4())
    try:
        return str(uuid.UUID(raw_id.strip()))
    except (ValueError, AttributeError):
        return str(uuid4())


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming = sanitize_request_id(request.headers.get("X-Request-ID"))
        token = request_id_var.set(incoming)
        request.request_id = incoming
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response["X-Request-ID"] = incoming
        return response
