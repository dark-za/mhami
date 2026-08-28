from __future__ import annotations

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


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming = request.headers.get("X-Request-ID") or str(uuid4())
        token = request_id_var.set(incoming)
        request.request_id = incoming
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response["X-Request-ID"] = incoming
        return response
