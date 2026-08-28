from __future__ import annotations

from django.urls import path

from .views import (
    BootstrapView,
    ExitDecisionView,
    LiveHealthView,
    ModulesHealthView,
    ReadyHealthView,
    SystemStatusView,
    metrics_view,
)

urlpatterns = [
    path("bootstrap", BootstrapView.as_view()),
    path("bootstrap/legacy", BootstrapView.as_view()),
    path("health/live", LiveHealthView.as_view()),
    path("health/ready", ReadyHealthView.as_view()),
    path("health/modules", ModulesHealthView.as_view()),
    path("status", SystemStatusView.as_view()),
    path("metrics", metrics_view),
    # C-06: phase exit decision workflow.
    path("exit-decisions/<str:phase>", ExitDecisionView.as_view()),
]
