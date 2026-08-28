from __future__ import annotations

from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.organizations.models import CompanyRole
from apps.platform_core.errors import PlatformAPIException
from apps.platform_core.mixins import TenantAPIView

from ..models import Notification
from ..serializers import NotificationMarkReadSerializer, NotificationSerializer
from ..services import mark_notification_read, mark_notifications_read


class NotificationListView(TenantAPIView):
    # BE-01: Notifications are user-scoped; open to all tenant roles.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(
        responses=OpenApiResponse(description="List of the current user's notifications."),
        operation_id="notifications_list",
    )
    def get(self, request):
        company = self.get_tenant().company
        notifications = Notification.objects.filter(company=company, user=request.user).order_by("-created_at")
        return Response({"notifications": NotificationSerializer(notifications, many=True).data})


class NotificationReadView(TenantAPIView):
    # BE-01: Marking a single notification read is a tenant-wide action.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(request=None, responses={200: NotificationSerializer}, operation_id="notifications_mark_read")
    def post(self, request, notification_id):
        company = self.get_tenant().company
        try:
            notification = Notification.objects.get(id=notification_id, company=company, user=request.user)
        except Notification.DoesNotExist as exc:
            raise PlatformAPIException("Notification not found.") from exc
        return Response(NotificationSerializer(mark_notification_read(notification, actor=request.user)).data)


class NotificationBatchReadView(TenantAPIView):
    # BE-01: Marking all notifications read is a tenant-wide action.
    required_roles = (CompanyRole.OWNER, CompanyRole.MONITOR, CompanyRole.EMPLOYEE)

    @extend_schema(
        request=NotificationMarkReadSerializer,
        responses=OpenApiResponse(description="Count of notifications marked as read."),
        operation_id="notifications_mark_read_batch",
    )
    def post(self, request):
        company = self.get_tenant().company
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("all"):
            count = mark_notifications_read(
                [str(notification_id) for notification_id in Notification.objects.filter(
                    company=company, user=request.user, read_at__isnull=True
                ).values_list("id", flat=True)],
                company=company,
                user=request.user,
            )
        else:
            notification_ids = [str(notification_id) for notification_id in serializer.validated_data.get("ids", [])]
            if not notification_ids:
                raise PlatformAPIException("Notification ids are required.")
            count = mark_notifications_read(notification_ids, company=company, user=request.user)
        return Response({"marked": count})
