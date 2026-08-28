# Phase 12 AI Agreement and Error Analysis

## Status

Issued by `PILOT-ASSURANCE-02`. Describes the AI Shadow Mode measurement model and current evidence for the Phase 12 exit dossier.

## Objective

Establish understood AI behavior during the internal pilot, including the agreement rate with human decisions and the nature of AI errors, while keeping AI in Shadow Mode (no automatic acceptance).

## Model and Measurement Basis

- AI runs are recorded as `AIAnalysisRun` per evidence item.
- Each run captures `provider_name`, `model_name`, `prompt_version`, `status`, `shadow_mode`, `auto_pass_eligible`, `auto_pass_activated`, `risk_level`, `provider_result`, `human_decision`, `agreement_with_human`, `error_message`, and `reviewed_at`.
- Agreement rate is computed as:

  ```
  agreement_rate = (AIAnalysisRun where agreement_with_human=True) / (all AIAnalysisRun) * 100
  ```

  Implemented in `pilot/services.py:_ai_agreement_rate` and surfaced on `PilotWeeklyReport.ai_agreement_rate` and the pilot dashboard summary.

## Shadow Mode and Auto-Acceptance Controls

- `AIAnalysisCriterion.shadow_mode` defaults to `True`.
- `AIAnalysisCriterion.auto_pass_enabled` defaults to `False`; the pilot does **not** enable auto-pass (explicit Phase 12 exclusion).
- `AIAnalysisRun.auto_pass_activated` must remain `False` throughout the pilot; any activation would trigger a stop condition.
- `AIAnalysisStatus.FAILED` is a first-class state; a failed run does not block evidence submission and does not imply acceptance.

## Agreement and Error Metrics (Template)

Final values are populated from the actual pilot observation period. The table records the measurement definition and current placeholder status:

| Metric | Definition | Evidence source | Current status |
| --- | --- | --- | --- |
| AI agreement rate | % of AI runs agreeing with human decision | `pilot/services.py:_ai_agreement_rate` | Computable; needs real runs |
| Run status distribution | counts by `completed` / `needs_review` / `failed` | `AIAnalysisRun.status` | Measurable |
| Error analysis | `PilotWeeklyReport.error_analysis` (free text) | Weekly report | To be completed each week |
| Shadow mode adherence | `shadow_mode=True` and `auto_pass_activated=False` on all runs | `AIAnalysisRun` | Verified by design + tests |
| Risk-level coverage | `risk_level` present per run | `AIAnalysisRun.risk_level` | Measurable |

## Error Categories

Error analysis is recorded as free text on each `PilotWeeklyReport` (`error_analysis` field). Categories to be tracked, derived from `AIAnalysisRun.error_message` and `status=failed`:

1. Provider availability / timeout errors.
2. Malformed provider result payloads.
3. Borderline evidence where human decision disagreed (false agreement boundary).
4. Oversensitive detection (face-blur false positives) and undersensitive detection (missed faces).

## Controls Verified by Automated Evidence

- AI analysis can be run per evidence item and returns `completed` or `needs_review` (`ai_gateway/tests/test_ai_gateway_api.py:test_ai_provider_and_criteria_and_analysis`).
- Shadow summary is visible to monitors (`test_connector_shadow_summary_visible`).
- AI provider configuration is owner-managed and validated.
- No test enables auto-pass; the stop-condition guard is enforced by design.

## Conclusion

The platform provides a complete, auditable AI agreement and error-analysis measurement path in Shadow Mode. **Final agreement-rate and error-category figures require the actual pilot AI runs captured in weekly reports.** The AI does not create automatic acceptance and AI failure does not halt evidence submission — both Phase 12 requirements are met at the capability level.
