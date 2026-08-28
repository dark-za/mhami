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

The runtime baseline was adjusted to **Vite 6.4.x** (with Node.js 24 LTS for builds) for the pilot. Rationale: a Vite 8.1.x release line was not yet available as a stable, security-patched build at pilot freeze time, so the pinned, actively maintained 6.4.x line was adopted to satisfy the security-patching and version-availability requirement. The rest of the baseline (Python 3.13, Django 5.2 LTS, DRF 3.18.x, PostgreSQL 17, Redis 8.2.x, Celery 5.6.x, React 19.2.x, TypeScript 5.9.x, Node 24 LTS) is unchanged. This adjustment is recorded here rather than silently rewriting the original decision.

The currently pinned exact versions in `backend/pyproject.toml` and `frontend/package.json` confirm this baseline: **Django 5.2.17**, **DRF 3.18.0**, **Vite 6.4.3**, React 19.2.0, TypeScript 5.9.2, Celery 5.6.0, and PostgreSQL 17 / Redis 8.x images in `compose.yml`. **Pillow 12.3.0** was added to the pinned baseline for the Phase 07 evidence/media pipeline (image resizing and processing); it is a media-pipeline dependency and is recorded here as part of the current runtime pin set rather than as a change to the core stack decision above.
