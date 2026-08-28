# Architecture Baseline

## Status

Approved planning architecture. Runtime files must not be created until the relevant delivery phase.

## Architecture Style

Use a modular monolith. The application is one deployable system with clear internal module contracts, one primary PostgreSQL database, explicit domain events, background workers, and strict tenant boundaries.

Do not introduce microservices, runtime plugin loading, user-defined schema engines, or user-uploaded executable integrations.

## Approved Technology Baseline

| Layer | Approved direction |
| --- | --- |
| Backend | Python 3.13, Django 5.2 LTS, Django REST Framework 3.18.x |
| Database | PostgreSQL 17 |
| Queue and cache | Redis 8.2.x for Celery broker, cache, rate limits, locks, and temporary state only |
| Background jobs | Celery 5.6.x with default, media, and AI queues |
| Frontend | React 19.2.x, TypeScript 5.9.x, Vite 6.4.x build pipeline, Node.js 24 LTS for builds only |
| Production web serving | Static React build served by NGINX; no Node.js runtime server |
| Media | Private platform storage behind application authorization |
| Deployment | Docker Compose, Cloudflare Tunnel, NGINX, Gunicorn, PostgreSQL, Redis, Celery |
| Connector | Linux Docker service managed by the tenant technical team |

Exact patch versions, image digests, and server sizing remain inventory-dependent.

## Implemented Modules

| Module | Responsibility |
| --- | --- |
| `platform_core` | Module registry, settings, feature flags, errors, request IDs, health, shared policy primitives. |
| `identity` | Custom user model, sessions, MFA, rate limiting, account lifecycle. |
| `tenancy` | Company registration, company code, industry, trial, status, support authorization, legal acceptance. |
| `organizations` | Branches, job roles, memberships, simple weekly shifts, operational-day settings. |
| `tasks` | Templates, versions, schedules, instances, claims, transfers, state machine, corrective tasks. |
| `evidence` | Capture sessions, media quarantine, evidence records, face derivatives, hashes, duplicate risk, task discussion. |
| `reviews` | Review queue, monitor decisions, overrides, retry, missed, correction, performance restriction decisions. |
| `ai_gateway` | Provider contract, provider configuration, analysis runs, policy gates, structured outputs, cost and limit tracking. |
| `connector_control` | Tenant connector enrollment, health, version compatibility, job dispatch, and audit. |
| `notifications` | In-app notifications scoped to company and user, produced from outbox events (backup/export) and mark-read API. |
| `audit` | Append-only business and security audit events with integrity protection. |
| `exports` | Authorized asynchronous ZIP, CSV, and PDF export jobs. |
| `backups` | Encrypted local backup, integrity verification, and isolated restore runs. |
| `pilot` | Phase 12 internal pilot program, weekly metrics, issues, and change requests. |

## Planned Modules

| Module | Responsibility |
| --- | --- |
| `reporting` | Owner and monitor indicators, performance policy calculations, export preparation. |

## Backend Boundaries

- API views receive requests, serializers validate transport data, application services execute business actions, domain logic enforces transitions, and the ORM persists data.
- Views, serializers, signals, React components, and Celery task wrappers must not become the authoritative home of business rules.
- Every tenant-sensitive query must apply company and branch scope before object lookup.
- Every module declares its manifest, dependencies, permissions, events, health check, API routes, tests, and documentation before completion.

## Data and Event Rules

- UUIDs are used for public identifiers.
- PostgreSQL is the business source of truth.
- Critical domain events are written through a transactional outbox.
- Consumers are idempotent and assume at-least-once delivery.
- Business status and audit history are append-only. Current state is a projection, not the only history.
- Store timestamps in UTC and render in branch timezone.

## Frontend Rules

- The frontend is a responsive Chrome web application. It has no service worker, PWA install flow, or offline mutation support in V1.
- Routes are module-scoped and protected by bootstrap permissions from the backend.
- Tenant branding is tokenized, contrast-safe, and cannot make status color-only.
- Arabic and English layouts are first-class. Calendar choice is a user preference, not a storage format.

## Runtime Topology

```text
Internet
  -> Cloudflare
  -> Cloudflare Tunnel
  -> NGINX
     -> React static build
     -> /api -> Gunicorn -> Django
                           -> PostgreSQL
                           -> Redis
                           -> Celery workers
                           -> private media storage

Tenant private AI endpoint
  <- Tenant Connector (Linux Docker, outbound authenticated channel)
  <- Platform AI Gateway
```

The first production host, regional location, backup destination, resource limits, and staging topology are determined only after the Phase 00 read-only inventory.
