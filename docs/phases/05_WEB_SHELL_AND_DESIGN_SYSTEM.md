# Phase 05: Web Shell and Design System

## Status

Complete.

Note: the in-app notification center is backed by the real `apps.notifications` module. The shell fetches `/api/v1/notifications/` (credentials included) for the current user and falls back to the static UI seed (`notificationSeed` in `frontend/src/design-system/tokens.ts`) only when the API is unreachable. Notifications are produced from outbox events (`backup.completed`, `backup.restore.completed`, `exports.completed`) and support per-item and batch mark-read endpoints.

## Objective

Provide a secure, responsive Chrome web experience that reflects role scope, tenant branding, bilingual content, date preference, and in-app notifications without moving business authority to the frontend.

## Entry Requirements

- Phase 04 is complete.
- Bootstrap API, permissions, company branding, and user preferences are available.
- Arabic and English terminology is approved for the first core screens.

## Scope

- Build responsive web shells for Platform Administrator, Company Owner, Quality Monitor, and Employee.
- Implement login flow using company code, login identifier, password, and MFA where required.
- Implement Arabic RTL and English LTR interface support.
- Implement Gregorian and Hijri display preference without altering stored UTC business data.
- Implement tenant name, logo, and three-color branding tokens with automatic contrast protection.
- Implement role-appropriate navigation, loading, empty, error, and permission-denied states.
- Implement in-app notification center for the approved V1 events.
- Implement camera-permission preflight and Chrome capability messaging without implementing evidence submission yet.

## Explicit Exclusions

- No PWA manifest, service worker, offline cache, installation UX, or offline mutation.
- No Safari, Edge, Firefox, or non-Chrome support commitment in V1.
- No authoritative role decision, task transition, or policy calculation in React.
- No external SMS, WhatsApp, Telegram, or email notification integration.

## Required Software and Services

- React, TypeScript, React Router, TanStack Query, Vite build tooling, and generated API types.
- Browser testing against Chrome desktop and Chrome Android as applicable.

## Security and Data Requirements

- Frontend routes are convenience only; backend authorization remains authoritative.
- No secret, AI credential, connector token, or presigned media URL is exposed to browser code.
- Branding cannot use color as the sole status signal.
- Camera and future media permissions are requested only at the point of use.

## Deliverables

- Shared design-token system and accessible component primitives.
- Bilingual application shell and locale/date preference handling.
- Role-specific navigation and bootstrap-driven module visibility.
- In-app notification UI and error-boundary behavior.
- UX documentation and Chrome support statement.

## Verification

- Arabic RTL and English LTR layouts pass visual checks.
- Poor tenant color combinations retain readable text and semantic status labels.
- Employees cannot navigate to owner or monitor screens through client-side URL manipulation.
- Chrome Android task shell and Chrome desktop administration shell behave correctly.
- No PWA artifacts are generated.

## Exit Criteria

- Every role can sign in and see an appropriate non-business shell.
- Branding, language, calendar preference, responsive behavior, and in-app notifications are ready for operational modules.
- Frontend contracts are generated from OpenAPI rather than manually duplicated.

## Stop Conditions

- Browser support expands without a documented test commitment.
- Tenant theme colors reduce accessibility or obscure state meaning.
- Business rules are implemented only in client code.
