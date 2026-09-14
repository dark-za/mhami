# ADR-0007: Runtime Baseline

## Status

Approved baseline.

## Context

The project needs a stable backend, queue, cache, and build stack that is mature and reviewable.

## Decision

Use Python 3.13, Django 5.2 LTS, Django REST Framework 3.18.x, PostgreSQL 17, Redis 8.2.x, Celery 5.6.x, React 19.2.x, TypeScript 5.9.x, and Vite 6.4.x as the runtime baseline.

## Consequences

- Versions remain pinned and reviewable.
- The stack matches the approved modular-monolith and browser-only strategy.
- Upgrades require the documented dependency process.

## Status / Update

The runtime baseline uses **Vite 6.4.x** with Node.js 24 LTS for builds. The
pinned, actively maintained release line satisfies the project’s security and
version-availability requirements. The rest of the baseline (Python 3.13,
Django 5.2 LTS, DRF 3.18.x, PostgreSQL 17, Redis 8.2.x, Celery 5.6.x, React
19.2.x, TypeScript 5.9.x, Node 24 LTS) is unchanged.

The currently pinned exact versions in `backend/pyproject.toml` and
`frontend/package.json` confirm this baseline: **Django 5.2.17**, **DRF
3.18.0**, **Vite 6.4.3**, React 19.2.0, TypeScript 5.9.2, Celery 5.6.0, and
PostgreSQL 17 / Redis 8.x images in `compose.yml`. **Pillow 12.3.0** supports
the evidence/media pipeline for image resizing and processing.
