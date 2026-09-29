# API Versioning Policy

## Overview
Mhami enforces URL-path versioning for all client-facing and external integration endpoints.
All current public and application APIs are mounted under the `/api/v1/` prefix.

## Versioning Rules
1. **URI Prefixing**: Every endpoint path must be prefixed with `/api/v{major}/`.
2. **Backward Compatibility**:
   - Backward-compatible additions (such as new optional request parameters or non-breaking response fields) do NOT trigger a major version bump.
   - Breaking schema changes, field removals, or semantic modifications require a new major version path (e.g. `/api/v2/`).
3. **Deprecation Window**:
   - When a major version is deprecated, a formal deprecation header (`Deprecation: true`) and `Sunset` header will be included in responses.
   - Deprecated versions are maintained for a minimum transition period before removal.
4. **Internal & Operations Endpoints**:
   - Platform internal health probes (`/health/`, `/metrics/`) are not versioned under `/api/v1/` and maintain stable, dedicated routes.
