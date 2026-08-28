# CI Quality Gates

## Purpose

Define the checks that must pass before runtime implementation is accepted.

## Baseline Gates

- Backend lint and format checks.
- Backend type checks.
- Backend unit and integration tests.
- Frontend lint, typecheck, unit tests, and build checks.
- Migration safety checks.
- Dependency and vulnerability scans.
- Security-header and authorization test suites.

## Rule

This document defines the enforced gates. Executable CI lives in `.github/workflows/ci.yml` and runs on every push and pull request: backend lint (`ruff`), type check (`mypy`), tests (`pytest` against Postgres), migration-state check (`makemigrations --check --dry-run`), OpenAPI schema validation (`spectacular --validate`), Django system checks (`manage.py check`), dependency vulnerability scans (`pip-audit`, `npm audit`), frontend typecheck/build/test, CodeQL SAST for Python and JavaScript, an SPDX SBOM for the backend image, Grype scanning of that image, and Trivy filesystem scanning for vulnerabilities and secrets. Grype and Trivy fail CI on high or critical findings.
