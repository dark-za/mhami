from django.urls import path

from .views import BackupDownloadView, BackupPolicyView, BackupRestoreView, BackupRunListView, BackupRunView

urlpatterns = [
    path("policy", BackupPolicyView.as_view()),
    path("runs", BackupRunView.as_view()),
    path("runs/list", BackupRunListView.as_view()),
    path("restore", BackupRestoreView.as_view()),
    path("download/<uuid:backup_run_id>", BackupDownloadView.as_view()),
]
