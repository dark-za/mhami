# Phase 02: Runtime and Development Foundation

## Status

Completed.

## Objective

Create the smallest safe runnable development foundation for the modular monolith. This phase establishes execution mechanics, not product workflows.

## Entry Requirements

- Phase 01 is complete.
- Server inventory and environment topology are approved.
- Exact runtime versions and base-image policy are frozen.

## Scope

- Create the Django project skeleton with the custom user model before any production-like migration.
- Create the React and TypeScript build skeleton without business pages.
- Create Docker Compose development services for API, PostgreSQL, Redis, Celery queues, and static frontend build workflow.
- Define environment-specific configuration for development, test, staging, and production.
- Establish dependency locking, linting, formatting, type checking, test runners, and baseline CI.
- Establish request ID propagation, basic structured logging, and live/readiness health endpoint foundations.
- Create separate test database configuration and safe local media storage path.

## Required Software and Services

- Python 3.13.
- Django 5.2 LTS and Django REST Framework 3.18.x.
- PostgreSQL 17.
- Redis 8.2.x.
- Celery 5.6.x.
- React 19.2.x, TypeScript 5.9.x, Vite 6.4.x, and Node.js 24 LTS for builds only.
- Docker and Docker Compose.

## Security and Data Requirements

- Use a custom user model before first migration.
- Do not use production data in development or test.
- Do not expose PostgreSQL or Redis publicly.
- Do not create public media routes.
- Do not add provider credentials, connector secrets, or Cloudflare tokens.

## Deliverables

- Runnable local development environment.
- Backend and frontend health/application shell only.
- Locked dependency manifests.
- Baseline lint, type, unit-test, and build commands.
- Environment templates without real secrets.
- Runtime documentation and developer setup guide.

## Verification

- Development stack starts from a clean checkout.
- Backend liveness and readiness endpoints work.
- Frontend build completes and shows a non-business application shell.
- Test database isolation is verified.
- Dependency and secret scans pass.

## Exit Criteria

- A clean developer can run the foundation with documented steps.
- No product task, tenant, evidence, or AI behavior has been implemented prematurely.
- CI can execute baseline quality gates.

## Stop Conditions

- Custom user model is deferred or migrations are created against an unsuitable model.
- Production and test environments can reach the same database.
- Runtime versions are unpinned.
