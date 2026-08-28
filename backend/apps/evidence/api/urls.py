from __future__ import annotations

from django.urls import path

from .views import (
    CaptureSessionView,
    EvidenceMediaView,
    EvidenceSubmitView,
    EvidenceTaskView,
    IssueCreateView,
    IssueMessagesView,
    MediaHealthView,
)

urlpatterns = [
    path("capture-sessions", CaptureSessionView.as_view()),
    path("submit", EvidenceSubmitView.as_view()),
    path("tasks/<uuid:task_instance_id>", EvidenceTaskView.as_view()),
    path("items/<uuid:evidence_id>/media", EvidenceMediaView.as_view()),
    path("issues", IssueCreateView.as_view()),
    path("issues/<uuid:issue_id>/messages", IssueMessagesView.as_view()),
    path("health/media", MediaHealthView.as_view()),
]
