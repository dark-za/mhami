from __future__ import annotations

from django.urls import path

from .views import BranchesView, JobRolesView, MembershipsView, WeeklyShiftsView

urlpatterns = [
    path("branches", BranchesView.as_view()),
    path("job-roles", JobRolesView.as_view()),
    path("memberships", MembershipsView.as_view()),
    path("weekly-shifts", WeeklyShiftsView.as_view()),
]
