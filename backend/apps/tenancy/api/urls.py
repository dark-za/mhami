from __future__ import annotations

from django.urls import path

from .views import (
    AcceptanceView,
    BranchMembershipView,
    CompanyMembersView,
    CompanyUsersView,
    LoginView,
    LogoutView,
    MeView,
)

urlpatterns = [
    path("login", LoginView.as_view()),
    path("logout", LogoutView.as_view()),
    path("me", MeView.as_view()),
    path("company/members", CompanyMembersView.as_view()),
    path("company/users", CompanyUsersView.as_view()),
    path("company/branch-memberships", BranchMembershipView.as_view()),
    path("company/acceptances", AcceptanceView.as_view()),
]
