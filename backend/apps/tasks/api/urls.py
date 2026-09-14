from __future__ import annotations

from django.urls import path

from .views import (
    TaskClaimView,
    TaskCancelView,
    TaskCompleteView,
    TaskInstancesView,
    ScheduledTaskCreateView,
    TaskSchedulesView,
    TaskStartView,
    TaskTemplatesView,
    TaskTemplateVersionsView,
    TaskTransfersView,
    TaskTransferRecipientsView,
    TaskTransfersListView,
    TaskTransferResolveView,
    TaskSchedulerRunView,
    TaskRequestResolveView,
    TaskRequestsView,
)

urlpatterns = [
    path("templates", TaskTemplatesView.as_view()),
    path("templates/<uuid:template_id>/versions", TaskTemplateVersionsView.as_view()),
    path("schedules", TaskSchedulesView.as_view()),
    path("scheduled-tasks", ScheduledTaskCreateView.as_view()),
    path("instances", TaskInstancesView.as_view()),
    path("instances/<uuid:instance_id>/claim", TaskClaimView.as_view()),
    path("instances/<uuid:instance_id>/start", TaskStartView.as_view()),
    path("instances/<uuid:instance_id>/complete", TaskCompleteView.as_view()),
    path("instances/<uuid:instance_id>/cancel", TaskCancelView.as_view()),
    path("instances/<uuid:instance_id>/transfers", TaskTransfersView.as_view()),
    path("transfer-recipients", TaskTransferRecipientsView.as_view()),
    path("transfers", TaskTransfersListView.as_view()),
    path("transfers/<uuid:transfer_id>/resolve", TaskTransferResolveView.as_view()),
    path("requests", TaskRequestsView.as_view()),
    path("requests/<uuid:task_request_id>/resolve", TaskRequestResolveView.as_view()),
    path("scheduler/run", TaskSchedulerRunView.as_view()),
]
