from django.urls import path

from .views import ConnectorEnrollmentView, ConnectorHealthView, ConnectorHeartbeatView, ConnectorRevokeView

urlpatterns = [
    path("enrollment", ConnectorEnrollmentView.as_view()),
    path("health", ConnectorHealthView.as_view()),
    path("heartbeat", ConnectorHeartbeatView.as_view()),
    path("revoke", ConnectorRevokeView.as_view()),
]
