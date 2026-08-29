from __future__ import annotations

from django.urls import path
from django.urls.resolvers import URLPattern

from .views import McpEndpointView

urlpatterns: list[URLPattern] = [
    path("mcp", McpEndpointView.as_view()),
]
