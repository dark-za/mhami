from django.urls import path

from .views import ExportDownloadView, ExportPolicyView, ExportRequestListView, ExportRequestView

urlpatterns = [
    path("policy", ExportPolicyView.as_view()),
    path("requests", ExportRequestView.as_view()),
    path("requests/list", ExportRequestListView.as_view()),
    path("download/<str:token>", ExportDownloadView.as_view()),
]
