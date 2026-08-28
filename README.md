# Modular Operations Platform

[![CI](https://github.com/dark-za/mhami/actions/workflows/ci.yml/badge.svg)](https://github.com/dark-za/mhami/actions/workflows/ci.yml)

## Status

Runnable foundation at platform version `0.1.0`. The repository contains a Django 5.2/DRF 3.18 backend, a React 19.2/TypeScript 5.9/Vite 6.4 frontend, PostgreSQL 17, Redis 8.2, Celery 5.6, Docker Compose environments, and CI quality gates.

## Repository structure

- `backend/` - Django modular monolith and REST API.
- `frontend/` - React web shell and TypeScript API contract.
- `docs/` - architecture, security, operations, and delivery records.
- `infra/` - NGINX and monitoring configuration.
- `compose.yml` - shared local service topology.
- `compose.dev.yml` - development ports, mounts, and hot reload.
- `compose.prod.yml` - production security and serving overrides.

## Quick start

1. Copy `.env.example` to `.env` and set local values as needed.
2. Start the development stack:

   ```bash
   docker compose -f compose.yml -f compose.dev.yml up --build
   ```

3. Open the frontend at <http://localhost:5173> and the API at <http://localhost:8000>.

For production, provide `DJANGO_SECRET_KEY`, `METRICS_TOKEN`,
`BACKUP_EXTERNAL_URI`, and a public hostname in `.env`, then run:

```bash
docker compose -f compose.yml -f compose.prod.yml up --build -d
```

The API schema is available at `/api/schema/` and Swagger UI at `/api/docs/`.

## Purpose

Build a multi-tenant operations platform for organizations in multiple sectors. The platform core manages execution, evidence, verification, correction, review, reporting, and operational intelligence. Restaurants and cafes are an initial sector package, not a hard-coded platform boundary.

## Official Sources

Read the documents in this order before any implementation work:

1. `docs/PROJECT_CHARTER.md`
2. `docs/CONSTITUTION_AMENDMENTS.md`
3. `docs/REQUIREMENTS_BASELINE.md`
4. `docs/ARCHITECTURE_BASELINE.md`
5. `docs/SECURITY_AND_DATA_BASELINE.md`
6. `docs/GOVERNANCE.md`
7. `docs/DELIVERY_ROADMAP.md`
8. The relevant document under `docs/phases/`

`distor-en.md` is the historical engineering constitution. Where it conflicts with an approved amendment, `docs/CONSTITUTION_AMENDMENTS.md` takes precedence.

## Repository Rule

No code may be added until the relevant phase authorizes it. Phase 01 is the repository and governance foundation; Phase 02 introduces the runtime scaffold only.
