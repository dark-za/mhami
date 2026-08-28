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
    MfaEnrollView,
    MfaVerifyView,
    RegisterView,
    SupportAuthorizationView,
)

urlpatterns = [
    path("register", RegisterView.as_view()),
    path("login", LoginView.as_view()),
    path("logout", LogoutView.as_view()),
    path("me", MeView.as_view()),
    path("mfa/enroll", MfaEnrollView.as_view()),
    path("mfa/verify", MfaVerifyView.as_view()),
    path("company/members", CompanyMembersView.as_view()),
    path("company/users", CompanyUsersView.as_view()),
    path("company/branch-memberships", BranchMembershipView.as_view()),
    path("company/acceptances", AcceptanceView.as_view()),
    path("company/support", SupportAuthorizationView.as_view()),
]
