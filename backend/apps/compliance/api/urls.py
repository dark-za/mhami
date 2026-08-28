"""URL routing for the compliance REST API."""

from __future__ import annotations

from django.urls import path

from .views import (
    DSRRequestListView,
    DSRRequestTransitionView,
    LegalDocumentListView,
    ProcessingActivityListView,
)


urlpatterns = [
    path("ropa", ProcessingActivityListView.as_view()),
    path("dsr", DSRRequestListView.as_view()),
    path("dsr/<uuid:pk>/verify", DSRRequestTransitionView.as_view(action="verify")),
    path("dsr/<uuid:pk>/start", DSRRequestTransitionView.as_view(action="start")),
    path("dsr/<uuid:pk>/complete", DSRRequestTransitionView.as_view(action="complete")),
    path("dsr/<uuid:pk>/reject", DSRRequestTransitionView.as_view(action="reject")),
    path("legal-documents", LegalDocumentListView.as_view()),
]
