from __future__ import annotations

from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    AgentActionLogListView,
    AgentGrantDetailView,
    AgentGrantListCreateView,
    AgentGrantRevokeView,
    AgentScopeListView,
    McpEndpointView,
)

urlpatterns: list[URLPattern] = [
    path("scopes", AgentScopeListView.as_view()),
    path("grants", AgentGrantListCreateView.as_view()),
    path("grants/<uuid:grant_id>", AgentGrantDetailView.as_view()),
    path("grants/<uuid:grant_id>/revoke", AgentGrantRevokeView.as_view()),
    path("logs", AgentActionLogListView.as_view()),
    path("mcp", McpEndpointView.as_view()),
]
