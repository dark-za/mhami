# Frontend Gap Assessment and Delivery Plan

## Current assessment

The frontend is a functional React web shell with bilingual design tokens, protected workspace routes, bootstrap loading, authentication entry, notifications, and typed API contracts. It already exposes navigation for dashboard, operations, tasks, evidence, people, reviews, and administration.

The backend is materially broader: it provides tenant lifecycle and MFA, branch and membership scope, task scheduling and transfers, evidence quarantine and review, AI gateway and shadow mode, connector health, exports, backups/restore, notifications, audit, and pilot reporting. The frontend currently represents many of these areas through one shell rather than dedicated feature screens and workflows.

## Prioritized delivery

### P0 - make the shell production-ready

1. Replace page-level placeholder/fallback states with an authenticated session provider and explicit loading/error boundaries.
2. Generate and consume the OpenAPI types for every implemented module instead of maintaining large local response types in `App.tsx`.
3. Add route-level authorization and tenant/branch context switching based on `/api/v1/bootstrap` and `/api/v1/auth/me`.
4. Complete Arabic/English direction switching, keyboard navigation, responsive layouts, and non-color status indicators.

### P1 - deliver daily operator workflows

1. Build task and operations screens for schedules, claims, transfers, overdue work, and corrective tasks (`/api/v1/tasks/` and organizations endpoints).
2. Build evidence capture, quarantine status, duplicate-risk, issue discussion, and authorized media access (`/api/v1/evidence/`).
3. Build review queues and decision flows for monitor review, overrides, retry, missed, and correction outcomes (`/api/v1/reviews/`).
4. Add live notification listing and mark-read behavior (`/api/v1/notifications/`).

### P2 - deliver owner and technical administration

1. Add people, branch, role, legal acceptance, MFA, and company lifecycle screens (`/api/v1/auth/` and organizations endpoints).
2. Add AI provider/criteria/shadow-mode views and connector enrollment, health, heartbeat, and revoke workflows.
3. Add export policy/request/download and backup policy/run/restore screens with explicit confirmation for destructive operations.
4. Add audit and pilot dashboards for the operational evidence already produced by the backend.

## Definition of done

Each screen must use the generated API contract, enforce the backend permission boundary, handle loading/empty/error states, support both locales, expose accessible status text, and have focused component tests. Delivery should proceed P0 → P1 → P2 so the shell and authorization model are stable before expanding module coverage.
