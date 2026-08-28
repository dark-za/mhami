from django.urls import path

from .views import (
    PilotChangeRequestDetailView,
    PilotChangeRequestView,
    PilotCharterView,
    PilotDashboardView,
    PilotIssueDetailView,
    PilotIssueView,
    PilotProgramView,
    PilotWeeklyReportView,
)

urlpatterns = [
    path("program", PilotProgramView.as_view()),
    path("dashboard", PilotDashboardView.as_view()),
    path("charter", PilotCharterView.as_view()),
    path("weekly-reports", PilotWeeklyReportView.as_view()),
    path("issues", PilotIssueView.as_view()),
    path("issues/<uuid:issue_id>", PilotIssueDetailView.as_view()),
    path("change-requests", PilotChangeRequestView.as_view()),
    path("change-requests/<uuid:change_id>", PilotChangeRequestDetailView.as_view()),
]
