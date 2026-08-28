# Constitution Amendments

## Purpose

`../distor-en.md` remains the historical engineering constitution. This file records approved decisions that override or extend it. An implementation must follow this file where the two documents conflict.

## Approved Amendments

| Area | Historical direction | Approved direction |
| --- | --- | --- |
| Product scope | Restaurant operations platform | Sector-neutral multi-tenant operations platform; restaurants are an initial sector package. |
| Tenant model | Organization and branch model without self-service SaaS lifecycle | Self-service company registration, permanent company code, trial, suspension, export window, and deletion lifecycle. |
| Web delivery | Web plus PWA | Responsive Chrome web application only in V1; no PWA or offline mode. |
| Brand colors | White, black, and red only | Each company supplies three brand colors and a logo. The design system must still enforce readable contrast and non-color status cues. |
| Languages | Arabic-first with future LTR support | Arabic and English in V1, with RTL and LTR support. |
| Calendar display | Branch timezone rules only | Store UTC and branch timezones; each user can choose Gregorian or Hijri display. |
| Scheduling | Daily and weekly only | Daily fixed-time, weekly fixed-time, and shift-relative schedules in V1. No raw cron. |
| Evidence media | Image, video, number, note, location listed for V1 | Camera-live images, numbers, notes, and confirmations only. Gallery uploads, video, GPS, and offline submission are deferred. |
| AI provider | Initial OpenAI provider permitted | Each company may select a provider through a standard structured-output contract. Private or local providers run through a tenant connector. |
| AI connector | Not defined | Linux Docker connector is required in V1 for tenant-private AI connectivity. |
| AI rollout | Shadow mode initially | Shadow mode is mandatory first. Owner-controlled auto-pass requires human-reviewed evidence thresholds by risk level. |
| Media face handling | No detailed face treatment | Persist a blurred derivative when a face is detected; do not send the original to external AI. |
| Notifications | In-app V1, external later | In-app V1 remains required. External providers remain deferred. |
| Storage integrations | Local private storage first, optional object storage later | Private platform storage is the source of truth. External archival and drive integrations are deferred. |
| Browser support | Broad browser matrix including Safari and Edge | Chrome is the only supported browser family in V1. |

## Non-Amended Rules

The following historical rules remain binding unless a future ADR changes them:

- Modular monolith architecture.
- Code-defined models and migration-controlled schema.
- PostgreSQL as source of truth and Redis only for temporary/cache/queue uses.
- Secure cookie sessions, CSRF protection, branch and tenant scoping, and no public media URLs.
- Append-only status and audit history.
- Background processing for AI and media work.
- No arbitrary code installation or executable plugins from a user interface.
- Separate development, test, staging, and production data stores.
