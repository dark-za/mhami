# Data Breach Response Plan — v1.0

## Status

**Living document, platform-side. Requires sign-off by the Data Protection Officer and Platform Owner before production promotion.**

This plan covers personal-data breaches that affect the platform or
its tenants. It is the documented counterpart to
`docs/runbooks/incident-response.md` and the audit-event
`SUPPORT_ACCESS_USED` and tenant-lifecycle events.

## Versioning

| Field | Value |
| --- | --- |
| Document type | Data Breach Response Plan |
| Document version | v1.0 |
| Effective date | _pending legal review_ |
| Approved by | _pending_ |
| Review cadence | Annual or on material change |

## 1. Definition

A **personal-data breach** is any incident leading to:

- Unauthorised access to personal data stored on the platform.
- Loss or alteration of personal data stored on the platform.
- Unauthorised disclosure of personal data stored on the platform.
- A failure of confidentiality, integrity, or availability of
  personal data that is likely to result in a risk to the rights
  and freedoms of a data subject.

The plan is triggered by any of the above, regardless of cause
(internal error, supplier compromise, malicious action, accidental
exposure).

## 2. Severity Levels

| Level | Data-subject count | Notification |
| --- | --- | --- |
| **Critical (P0)** | > 1,000 data subjects | SDAIA within 24 hours; data subjects within 72 hours |
| **High (P1)** | 100–1,000 data subjects | SDAIA within 24 hours; data subjects within 72 hours when high risk |
| **Medium (P2)** | < 100 data subjects | Internal escalation; data-subject notification at the platform's discretion |
| **Low (P3)** | No identifiable personal data | Internal review only |

The thresholds are derived from common practice under the PDPL and
the GDPR; the legal reviewer is responsible for confirming them
against the local regulatory text.

## 3. Response Procedure

### 0–1 hour: Containment

- The on-call engineer confirms the incident and the scope.
- The CISO and the DPO are paged through the alert routing in
  `infra/monitoring/alert-rules.yml`.
- Containment steps are taken **without bypassing audit**: every
  support action is logged through the existing
  `SupportAuthorization` path; every state change is recorded
  through the existing audit chain.
- If the breach involves leaked credentials, follow
  `docs/SECRET_MANAGEMENT.md` to rotate and revoke.

### 1–24 hours: Investigation and impact assessment

- Reconstruct the incident from the audit chain (every operational
  event has a HMAC-protected `event_hash`).
- Identify the data subjects affected and the data categories
  involved.
- Identify whether the breach crosses borders; if so, identify
  the destination.
- The DPO drafts the initial incident note with the data-subject
  count, the categories involved, the likely consequences, and the
  measures taken or proposed.

### 24–72 hours: Regulator notification

- For P0 and P1, the DPO notifies the regulator (SDAIA under the
  PDPL) within the documented window.
- The notification is a written record that includes the data
  categories, the approximate number of data subjects, the likely
  consequences, the measures taken or proposed, and the DPO
  contact details.
- The notification is logged in the audit chain through a
  dedicated event type (`compliance.breach.notified`).

### 72 hours–7 days: Data subject notification

- For P0 and P1 incidents, the DPO coordinates the data subject
  notification through the company owners of the affected tenants.
- The notification describes the breach in clear language, the
  likely consequences, the measures taken, and the contact point
  for further information.
- The platform does not contact data subjects directly without
  controller approval; the controller remains the primary contact.

### 7–30 days: Root cause analysis and improvements

- The post-incident review records the timeline, the contributing
  factors, the detection mechanism, and the corrective actions.
- The corrective actions are tracked in the issue backlog with an
  owner and a deadline; the backlog is
  `docs/PHASE12_DEFECT_BACKLOG.md` and the issue tracker.
- The DPIA (`09_DPIA`) and the ROPA are updated if the breach
  reveals a new processing risk or a change to the documented
  measures.
- The legal documents under `docs/legal/` are re-reviewed if the
  breach changes the documented risk profile.

## 4. Response Team

| Role | Responsibility |
| --- | --- |
| **Incident Commander** | Coordinates the response; final escalation point. |
| **Security Lead** | Owns containment, investigation, and root cause. |
| **Data Protection Officer** | Owns the regulatory and data-subject notification. |
| **Legal Counsel** | Owns the legal review of the notification and the post-incident report. |
| **Communications** | Owns the tenant-owner and data-subject communications. |
| **Platform Owner** | Owns the platform decision-making and the post-incident corrective actions. |

## 5. Communication Templates

The DPO maintains a set of communication templates in
`docs/legal/10_BREACH_RESPONSE/templates/` (added during legal
review). Until the templates are approved, the DPO drafts the
notification from scratch with the DPO and Legal Counsel, and the
draft is reviewed by the Platform Owner before sending.

## 6. Tabletop Exercises

The response plan is exercised at least once per year in a tabletop
exercise with the response team. The exercise record is filed in
`docs/legal/10_BREACH_RESPONSE/exercises/` and summarised in the
release dossier.

## 7. References

- `docs/runbooks/incident-response.md` — operational incident
  runbook.
- `docs/SECURITY_AND_DATA_BASELINE.md` — security and data
  baseline.
- `docs/SECRET_MANAGEMENT.md` — secret rotation and revocation.
- `docs/PHASE11_SECURITY_REVIEW.md` — security review record.
- `docs/PHASE11_RELEASE_RISK_REGISTER.md` — risk register.

## 8. Approval

This plan requires sign-off by the DPO and the Platform Owner
before any production promotion. The sign-off is recorded in
`docs/PHASE12_AI_AGREEMENT_REPORT.md` and the release dossier.
