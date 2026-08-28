from django.urls import path

from .views import ReviewDashboardView, ReviewDecisionCreateView, ReviewPolicyView, ReviewQueueView

urlpatterns = [
    path("dashboard", ReviewDashboardView.as_view()),
    path("queue", ReviewQueueView.as_view()),
    path("policy", ReviewPolicyView.as_view()),
    path("decisions", ReviewDecisionCreateView.as_view()),
]
