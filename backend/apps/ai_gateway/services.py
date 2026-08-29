from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db import models

from apps.audit.services import record_audit_event
from apps.evidence.models import EvidenceItem
from apps.identity.models import User
from apps.organizations.models import CompanyMembership, CompanyRole, UserBranchMembership
from apps.platform_core.service_base import audited_service
from apps.reviews.models import ReviewDecision, ReviewDecisionType
from apps.tenancy.models import Company

from .models import AIAnalysisCriterion, AIAnalysisRun, AIAnalysisStatus, AIProviderConfig
from .providers import FakeProvider, OpenAIProvider, build_provider, validate_provider_result


def accessible_branch_ids(company: Company, user: User) -> list[str]:
    membership = CompanyMembership.objects.filter(company=company, user=user, active=True).only("role").first()
    if membership and membership.role == CompanyRole.OWNER:
        return [str(branch_id) for branch_id in company.branches.values_list("id", flat=True)]
    return [str(branch_id) for branch_id in UserBranchMembership.objects.filter(company=company, user=user, active=True).values_list("branch_id", flat=True)]


def provider_config_for_company(company: Company) -> AIProviderConfig:
    config, _created = AIProviderConfig.objects.get_or_create(company=company)
    return config


def active_criterion(company: Company) -> AIAnalysisCriterion | None:
    return AIAnalysisCriterion.objects.filter(company=company, active=True).order_by("-version_number").first()


def criteria_summary(company: Company) -> list[dict[str, object]]:
    return [
        {
            "id": str(item.id),
            "version_number": item.version_number,
            "title": item.title,
            "shadow_mode": item.shadow_mode,
            "auto_pass_enabled": item.auto_pass_enabled,
            "auto_pass_risk_threshold": item.auto_pass_risk_threshold,
            "active": item.active,
            "created_at": item.created_at.isoformat(),
        }
        for item in AIAnalysisCriterion.objects.filter(company=company).order_by("-version_number")
    ]


def shadow_summary(company: Company, user: User) -> dict[str, object]:
    branch_ids = accessible_branch_ids(company, user)
    runs = AIAnalysisRun.objects.filter(company=company, branch_id__in=branch_ids)
    completed = runs.filter(status=AIAnalysisStatus.COMPLETED)
    review = runs.filter(status=AIAnalysisStatus.NEEDS_REVIEW)
    total = runs.count()
    compared = runs.filter(agreement_with_human__isnull=False)
    agreement = compared.filter(agreement_with_human=True).count()
    return {
        "company": {"id": str(company.id), "name": company.name, "code": company.code},
        "summary": {
            "total_runs": total,
            "completed": completed.count(),
            "needs_review": review.count(),
            "human_reviewed_runs": runs.filter(review_decision__isnull=False).count(),
            "compared_runs": compared.count(),
            "agreement_rate": round((agreement / compared.count()) * 100, 1) if compared.exists() else 0,
        },
        "runs": [
            {
                "id": str(run.id),
                "evidence_item_id": str(run.evidence_item_id) if run.evidence_item_id else None,
                "status": run.status,
                "risk_level": run.risk_level,
                "shadow_mode": run.shadow_mode,
                "auto_pass_eligible": run.auto_pass_eligible,
                "auto_pass_activated": run.auto_pass_activated,
                "created_at": run.created_at.isoformat(),
            }
            for run in runs.order_by("-created_at")
        ],
    }


@transaction.atomic
def upsert_provider_config(company: Company, user: User, payload: dict[str, Any]) -> AIProviderConfig:
    config = provider_config_for_company(company)
    before = {
        "provider_name": config.provider_name,
        "endpoint_url": config.endpoint_url,
        "model_name": config.model_name,
        "enabled": config.enabled,
    }
    for field, value in payload.items():
        setattr(config, field, value)
    config.updated_by = user
    config.save()
    record_audit_event(
        event_type="AI_PROVIDER_UPDATED",
        target_type="ai_provider_config",
        target_id=str(config.id),
        actor_id=str(user.id),
        branch_id="",
        before=before,
        after={"provider_name": config.provider_name, "endpoint_url": config.endpoint_url, "model_name": config.model_name, "enabled": config.enabled},
    )
    return config


@audited_service(event_type="AI_CRITERIA_UPDATED", target_type="ai_analysis_criterion")
def create_criterion(company: Company, user: User, payload: dict[str, Any]) -> AIAnalysisCriterion:
    version = (AIAnalysisCriterion.objects.filter(company=company).aggregate(max_version=models.Max("version_number"))["max_version"] or 0) + 1
    criterion = AIAnalysisCriterion.objects.create(
        company=company,
        version_number=version,
        title=payload["title"],
        criteria_json=payload.get("criteria_json", {}),
        reference_media_names=payload.get("reference_media_names", []),
        shadow_mode=True,
        auto_pass_enabled=False,
        auto_pass_risk_threshold=payload.get("auto_pass_risk_threshold", 70),
        created_by=user,
    )
    return criterion


def _provider_for(config: AIProviderConfig) -> FakeProvider | OpenAIProvider:
    return build_provider(config)


def _qualifying_human_decision(decision: ReviewDecision) -> bool:
    return decision.evidence_item_id is not None and decision.decision_type in {
        ReviewDecisionType.APPROVE,
        ReviewDecisionType.APPROVE_DESPITE_ALERT,
        ReviewDecisionType.MARK_MISSED,
    }


def _agreement_with_decision(run: AIAnalysisRun, decision: ReviewDecision) -> bool | None:
    verdict = run.provider_result.get("verdict")
    if verdict not in {"approve", "review", "reject"}:
        return None
    human_approved = decision.decision_type in {
        ReviewDecisionType.APPROVE,
        ReviewDecisionType.APPROVE_DESPITE_ALERT,
    }
    return (verdict == "approve") == human_approved


@transaction.atomic
def link_analysis_runs_to_review_decision(decision: ReviewDecision) -> None:
    if not _qualifying_human_decision(decision):
        return
    runs = AIAnalysisRun.objects.select_for_update().filter(
        company=decision.company,
        branch=decision.branch,
        evidence_item_id=decision.evidence_item_id,
        review_decision__isnull=True,
    )
    for run in runs:
        run.review_decision = decision
        run.human_decision = decision.decision_type
        run.agreement_with_human = _agreement_with_decision(run, decision)
        run.reviewed_at = decision.created_at
        run.save(update_fields=["review_decision", "human_decision", "agreement_with_human", "reviewed_at"])
        record_audit_event(
            event_type="AI_ANALYSIS_REVIEW_LINKED",
            target_type="ai_analysis_run",
            target_id=str(run.id),
            actor_id=str(decision.decided_by_id),
            branch_id=str(decision.branch_id),
            metadata={"review_decision_id": str(decision.id), "decision_type": decision.decision_type},
        )


def _latest_qualifying_review_decision(evidence: EvidenceItem) -> ReviewDecision | None:
    decisions = ReviewDecision.objects.filter(
        company=evidence.company,
        branch=evidence.branch,
        evidence_item=evidence,
        decision_type__in=[
            ReviewDecisionType.APPROVE,
            ReviewDecisionType.APPROVE_DESPITE_ALERT,
            ReviewDecisionType.MARK_MISSED,
        ],
    )
    return decisions.order_by("-created_at").first()


@transaction.atomic
def run_analysis(company: Company, user: User, evidence_item_id: str, criterion_id: str | None = None) -> AIAnalysisRun:
    config = provider_config_for_company(company)
    if not config.enabled:
        raise ValueError("AI provider is disabled.")
    evidence = EvidenceItem.objects.select_related("branch").get(id=evidence_item_id, company=company)
    if str(evidence.branch_id) not in accessible_branch_ids(company, user):
        raise ValueError("User cannot access this branch.")
    criterion = AIAnalysisCriterion.objects.get(id=criterion_id, company=company) if criterion_id else active_criterion(company)
    if criterion is None:
        raise ValueError("AI criteria not configured.")
    provider = _provider_for(config)
    evidence_summary = {
        "duplicate_risk_score": evidence.duplicate_risk_score,
        "face_detected": evidence.face_detected,
        "evidence_type": evidence.evidence_type,
    }
    provider_payload = {"criteria": criterion.criteria_json, "evidence": evidence_summary}
    try:
        result = validate_provider_result(provider.analyze(evidence_summary=evidence_summary, criteria={**criterion.criteria_json, "auto_pass_enabled": criterion.auto_pass_enabled, "auto_pass_risk_threshold": criterion.auto_pass_risk_threshold}))
        status = AIAnalysisStatus.COMPLETED if result["verdict"] == "approve" else AIAnalysisStatus.NEEDS_REVIEW
        run = AIAnalysisRun.objects.create(
            company=company,
            branch=evidence.branch,
            evidence_item=evidence,
            provider_name=config.provider_name,
            model_name=config.model_name,
            prompt_version=criterion.version_number,
            status=status,
            shadow_mode=True,
            auto_pass_eligible=bool(result["auto_pass_eligible"]),
            auto_pass_activated=False,
            risk_level=str(result["risk_level"]),
            provider_payload=provider_payload,
            provider_result=result,
            created_by=user,
        )
        record_audit_event(
            event_type="AI_ANALYSIS_CREATED",
            target_type="ai_analysis_run",
            target_id=str(run.id),
            actor_id=str(user.id),
            branch_id=str(evidence.branch_id),
            metadata={"evidence_item_id": str(evidence.id), "criterion_id": str(criterion.id)},
        )
        decision = _latest_qualifying_review_decision(evidence)
        if decision is not None:
            link_analysis_runs_to_review_decision(decision)
            run.refresh_from_db()
        return run
    except Exception as exc:
        run = AIAnalysisRun.objects.create(
            company=company,
            branch=evidence.branch,
            evidence_item=evidence,
            provider_name=config.provider_name,
            model_name=config.model_name,
            prompt_version=criterion.version_number,
            status=AIAnalysisStatus.FAILED,
            shadow_mode=True,
            provider_payload=provider_payload,
            provider_result={},
            error_message=str(exc),
            created_by=user,
        )
        record_audit_event(
            event_type="AI_ANALYSIS_FAILED",
            target_type="ai_analysis_run",
            target_id=str(run.id),
            actor_id=str(user.id),
            branch_id=str(evidence.branch_id),
            metadata={"evidence_item_id": str(evidence.id), "criterion_id": str(criterion.id), "error": str(exc)},
        )
        decision = _latest_qualifying_review_decision(evidence)
        if decision is not None:
            link_analysis_runs_to_review_decision(decision)
            run.refresh_from_db()
        return run
