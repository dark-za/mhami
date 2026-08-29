from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny, IsAdminUser


class ProtectedSpectacularAPIView(SpectacularAPIView):
    def get_permissions(self):
        permission_classes = [IsAdminUser] if settings.API_DOCS_REQUIRE_STAFF else [AllowAny]
        return [permission() for permission in permission_classes]


class ProtectedSpectacularSwaggerView(SpectacularSwaggerView):
    def get_permissions(self):
        permission_classes = [IsAdminUser] if settings.API_DOCS_REQUIRE_STAFF else [AllowAny]
        return [permission() for permission in permission_classes]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", include("apps.platform_core.health_urls")),
    path("api/v1/", include("apps.platform_core.api.urls")),
    path("api/v1/platform/", include("apps.platform_core.api.urls")),
    path("api/v1/auth/", include("apps.tenancy.api.urls")),
    path("api/v1/organizations/", include("apps.organizations.api.urls")),
    path("api/v1/tasks/", include("apps.tasks.api.urls")),
    path("api/v1/evidence/", include("apps.evidence.api.urls")),
    path("api/v1/reviews/", include("apps.reviews.api.urls")),
    path("api/v1/ai/", include("apps.ai_gateway.api.urls")),
    path("api/v1/connectors/", include("apps.connector_control.api.urls")),
    path("api/v1/agent/", include("apps.agent_access.api.urls")),
    path("api/v1/exports/", include("apps.exports.api.urls")),
    path("api/v1/backups/", include("apps.backups.api.urls")),
    path("api/v1/notifications/", include("apps.notifications.api.urls")),
    path("api/v1/pilot/", include("apps.pilot.api.urls")),
    path("api/v1/compliance/", include("apps.compliance.api.urls")),
    path("api/schema/", ProtectedSpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", ProtectedSpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
