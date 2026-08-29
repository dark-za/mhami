from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from apps.identity.models import User

from .models import OutboxEvent
from .registry import get_registry

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "owner": [
        "users.manage",
        "branches.manage",
        "job_roles.manage",
        "branch_memberships.manage",
        "tasks.create",
        "tasks.execute",
        "tasks.transfer",
        "reviews.manage",
        "reviews.policy.manage",
        "exports.manage",
        "ai.manage",
        "connectors.manage",
        "mcp.manage",
        "backups.manage",
        "pilot.manage",
    ],
    "monitor": [
        "tasks.create",
        "tasks.execute",
        "tasks.transfer",
        "reviews.manage",
        "exports.request",
        "pilot.manage",
        "mcp.logs.read",
    ],
    "employee": [
        "tasks.execute",
        "tasks.transfer",
        "evidence.submit",
        "notifications.read",
    ],
}

WORKSPACE_MODULES = {
    "dashboard",
    "operations",
    "tasks",
    "evidence",
    "people",
    "reviews",
    "admin",
    "agent_access",
}


def _workspace_modules(module_slugs: set[str]) -> list[str]:
    modules: list[str] = ["dashboard"]
    if "tasks" in module_slugs:
        modules.append("tasks")
    if "evidence" in module_slugs:
        modules.append("evidence")
    if {"organizations", "tenancy"} & module_slugs:
        modules.append("people")
    if "reviews" in module_slugs:
        modules.append("reviews")
    if {"exports", "pilot", "backups"} & module_slugs:
        modules.append("operations")
    if {"ai_gateway", "connector_control"} & module_slugs:
        modules.append("admin")
    if "agent_access" in module_slugs:
        modules.append("agent_access")
    return [module for module in modules if module in WORKSPACE_MODULES]


def permissions_for_role(role: str | None) -> list[str]:
    """Return display permissions derived from the fixed company role."""
    return ROLE_PERMISSIONS.get(str(role or ""), [])


def bootstrap_payload(user: object | None = None) -> dict[str, object]:
    registry = get_registry()
    module_slugs = {module.slug for module in registry.manifests}
    current_user: dict[str, object] = {"is_authenticated": False}
    company_payload: dict[str, object] | None = None
    branches: list[dict[str, object]] = []
    branch_scope: list[dict[str, object]] = []
    permissions: list[str] = []
    if user is not None:
        is_authenticated = bool(getattr(user, "is_authenticated", False))
        current_user = {
            "is_authenticated": is_authenticated,
            "id": str(getattr(user, "id", "")) if is_authenticated else None,
            "login_id": getattr(user, "login_id", None) if is_authenticated else None,
            "display_name": getattr(user, "display_name", None) if is_authenticated else None,
            "role": None,
        }
        if is_authenticated and isinstance(user, User):
            from apps.tenancy.services import user_company
            from apps.tenancy.access import accessible_company_branch_ids, company_role_for_user

            company = user_company(user)
            if company is not None:
                role = company_role_for_user(company, user)
                current_user["role"] = role
                permissions = permissions_for_role(role)
                company_payload = {
                    "id": str(company.id),
                    "name": company.name,
                    "code": company.code,
                    "status": company.status,
                    "industry": company.industry,
                }
                from apps.organizations.models import Branch

                branches = [
                    {
                        "id": str(branch.id),
                        "name": branch.name,
                        "code": branch.code,
                        "timezone": branch.timezone,
                        "operational_day_cutoff": branch.operational_day_cutoff.isoformat(),
                        "active": branch.active,
                    }
                    for branch in Branch.objects.filter(company=company, active=True)
                ]
                scoped_ids = set(accessible_company_branch_ids(company, user))
                branch_scope = [branch for branch in branches if branch["id"] in scoped_ids]
    return {
        "current_user": current_user,
        "company": company_payload,
        "permissions": permissions,
        "branches": branches,
        "branch_scope": branch_scope,
        "enabled_modules": _workspace_modules(module_slugs),
        "feature_flags": [],
        "app_version": "0.1.0",
    }


def record_outbox_event(
    *,
    event_name: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: Mapping[str, object],
    request_id: UUID | None = None,
) -> OutboxEvent:
    """Backward-compatible shim — prefer :func:`apps.platform_core.outbox.emit`."""
    from .outbox import OutboxEventBuilder, emit as _emit

    return _emit(
        OutboxEventBuilder(
            event_name=event_name,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=dict(payload),
            request_id=request_id,
        )
    )


def broker_available(*, timeout: float = 0.75) -> bool:
    from config.celery import app

    try:
        return bool(app.control.ping(timeout=timeout))
    except Exception:
        return False


def module_health_report() -> list[dict[str, str]]:
    registry = get_registry()
    return registry.health_statuses()


def metrics_report() -> dict[str, object]:
    from apps.ai_gateway.models import AIAnalysisRun, AIAnalysisStatus
    from apps.backups.models import BackupRun, BackupStatus, RestoreRun
    from apps.connector_control.models import ConnectorStatus, TenantConnectorEnrollment
    from apps.exports.models import ExportRequest, ExportStatus

    return {
        "ai": {
            "runs": AIAnalysisRun.objects.count(),
            "needs_review": AIAnalysisRun.objects.filter(status=AIAnalysisStatus.NEEDS_REVIEW).count(),
            "failed": AIAnalysisRun.objects.filter(status=AIAnalysisStatus.FAILED).count(),
        },
        "connector": {
            "active": TenantConnectorEnrollment.objects.filter(status=ConnectorStatus.ACTIVE).count(),
            "revoked": TenantConnectorEnrollment.objects.filter(status=ConnectorStatus.REVOKED).count(),
        },
        "exports": {
            "completed": ExportRequest.objects.filter(status=ExportStatus.COMPLETED).count(),
            "expired": ExportRequest.objects.filter(status=ExportStatus.EXPIRED).count(),
        },
        "backups": {
            "completed": BackupRun.objects.filter(status=BackupStatus.COMPLETED).count(),
            "restored": BackupRun.objects.filter(status=BackupStatus.RESTORED).count(),
            "restore_runs": RestoreRun.objects.count(),
        },
    }
