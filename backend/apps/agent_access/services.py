from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.platform_core.request_id import get_request_id
from apps.tenancy.access import has_company_role, is_active_company_user
from apps.tenancy.models import Company

from .models import AgentActionLog, AgentGrant, AgentGrantStatus, arguments_hash, validate_agent_scopes


def ensure_owner_can_manage_agent_access(*, user_id: object, company: Company) -> None:
    user = get_user_model().objects.filter(id=user_id).first()
    if user is None or not has_company_role(company, user, "owner"):
        raise PermissionDenied("Only an active company owner can manage MCP agent access.")


def ensure_grant_user_belongs_to_company(*, user_id: object, company: Company) -> None:
    user = get_user_model().objects.filter(id=user_id).first()
    if user is None or not is_active_company_user(company, user):
        raise PermissionDenied("MCP grant user must belong to the active company.")


def create_agent_grant(
    *,
    owner_id: object,
    company: Company,
    user_id: object,
    client_name: str,
    client_fingerprint: str,
    scopes: list[str],
    expires_at,
) -> AgentGrant:
    ensure_owner_can_manage_agent_access(user_id=owner_id, company=company)
    ensure_grant_user_belongs_to_company(user_id=user_id, company=company)
    validate_agent_scopes(scopes)
    grant = AgentGrant(
        company=company,
        user_id=user_id,
        client_name=client_name,
        client_fingerprint=client_fingerprint,
        scopes=scopes,
        expires_at=expires_at,
    )
    grant.full_clean()
    grant.save()
    record_audit_event(
        event_type="MCP_AGENT_GRANT_CREATED",
        actor_id=str(owner_id),
        target_type="agent_grant",
        target_id=str(grant.id),
        metadata={"scopes": scopes, "client_name": client_name},
    )
    return grant


def revoke_agent_grant(*, owner_id: object, grant: AgentGrant, reason: str = "") -> AgentGrant:
    ensure_owner_can_manage_agent_access(user_id=owner_id, company=grant.company)
    if grant.revoked_at is None:
        grant.status = AgentGrantStatus.REVOKED
        grant.revoked_at = timezone.now()
        grant.save(update_fields=["status", "revoked_at", "updated_at"])
        record_audit_event(
            event_type="MCP_AGENT_GRANT_REVOKED",
            actor_id=str(owner_id),
            target_type="agent_grant",
            target_id=str(grant.id),
            metadata={"reason": reason},
        )
    return grant


@transaction.atomic
def record_agent_action(
    *,
    grant: AgentGrant,
    tool_name: str,
    required_scope: str,
    idempotency_key: str,
    arguments: Mapping[str, object],
    request_id: UUID | None = None,
) -> tuple[AgentActionLog, bool]:
    validate_agent_scopes([required_scope])
    if not grant.active:
        raise PermissionDenied("MCP agent grant is not active.")
    if required_scope not in grant.scopes and "admin:full" not in grant.scopes:
        raise PermissionDenied("MCP agent grant does not include the required scope.")

    payload_hash = arguments_hash(dict(arguments))
    existing = (
        AgentActionLog.objects.select_for_update()
        .filter(grant=grant, tool_name=tool_name, idempotency_key=idempotency_key)
        .first()
    )
    if existing is not None:
        if existing.arguments_hash != payload_hash:
            raise ValidationError(
                {
                    "idempotency_key": (
                        "Idempotency key was already used for this tool with different arguments."
                    )
                }
            )
        return existing, False

    action_log = AgentActionLog(
        grant=grant,
        company=grant.company,
        request_id=request_id or UUID(get_request_id()),
        tool_name=tool_name,
        required_scope=required_scope,
        idempotency_key=idempotency_key,
        arguments_hash=payload_hash,
    )
    action_log.full_clean()
    action_log.save()
    return action_log, True
