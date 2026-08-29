# Mhami Backend

The backend is a Django 5.2 modular monolith with Django REST Framework APIs, PostgreSQL persistence, Redis-backed Celery jobs, OpenAPI schema generation, audit events, tenant isolation helpers, encrypted backups, and production security settings.

## Structure

- `apps/tenancy` - company lifecycle, tenant context, authentication, and access helpers.
- `apps/organizations` - branches, roles, memberships, and weekly shifts.
- `apps/tasks` - templates, instances, lifecycle actions, and transfer requests.
- `apps/evidence` - capture sessions, uploads, privacy decisions, issues, and media access.
- `apps/reviews` - review queues, policy, and decisions.
- `apps/ai_gateway` - AI provider configuration, criteria, shadow analysis, and provider boundaries.
- `apps/exports` - export request creation and tokenized downloads.
- `apps/backups` - encrypted backup, external upload, and restore workflows.
- `apps/compliance` - ROPA, DSR, legal document versions, and compliance services.
- `apps/pilot` - pilot program, charter, weekly reports, issues, and change requests.
- `apps/platform_core` - health, metrics, audit/outbox helpers, registry, and exit decisions.

## Local Commands

```bash
python -m compileall .
ruff check .
mypy .
python manage.py makemigrations --check --dry-run
python manage.py spectacular --validate
python manage.py check
pytest
```

Use Docker Compose from the repository root for the normal development stack.
