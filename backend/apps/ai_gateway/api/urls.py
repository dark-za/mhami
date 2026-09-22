from django.urls import path

from .views import AnalysisRunView, CriteriaView, ProviderConfigView, ProviderPingView, ShadowSummaryView

urlpatterns = [
    path("provider", ProviderConfigView.as_view()),
    path("provider/ping", ProviderPingView.as_view()),
    path("criteria", CriteriaView.as_view()),
    path("analysis", AnalysisRunView.as_view()),
    path("shadow", ShadowSummaryView.as_view()),
]
