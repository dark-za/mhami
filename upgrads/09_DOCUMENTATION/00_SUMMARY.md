# Section 9: Documentation

## List of Fixes

| # | Title | Priority | Duration |
|---|---|---|---|
| DOC-01 | API Reference (OpenAPI) | P0 | 1 week |
| DOC-02 | User Guides | P0 | 2 weeks |
| DOC-03 | Runbooks | P0 | 1 week |
| DOC-04 | Incident Response | P0 | 1 week |
| DOC-05 | Troubleshooting | P1 | 1 week |

## DOC-01: API Reference (Detail)

### Tool
- drf-spectacular (existing)
- Swagger UI (existing at `/api/docs/`)

### Improvements
1. **Tags:** Group endpoints by module
2. **Examples:** request/response examples for each endpoint
3. **Error codes:** Document every likely error code
4. **Authentication:** Explain session + CSRF
5. **Rate limits:** Document throttling
6. **Versioning:** API versioning strategy

### Configuration
```python
# config/settings/base.py
SPECTACULAR_SETTINGS = {
    "TITLE": "Mhami Platform API",
    "DESCRIPTION": "Multi-tenant operations platform API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "auth", "description": "Authentication and session management"},
        {"name": "tenancy", "description": "Company lifecycle and legal"},
        {"name": "organizations", "description": "Branches, roles, shifts"},
        {"name": "tasks", "description": "Templates, instances, schedules"},
        {"name": "evidence", "description": "Capture, submit, review"},
        {"name": "ai", "description": "AI Gateway (Shadow Mode)"},
        {"name": "reviews", "description": "Monitor decisions"},
        {"name": "exports", "description": "Async exports"},
        {"name": "backups", "description": "Backup and restore"},
    ],
}
```

### Deployment
- Swagger UI at `/api/docs/`
- ReDoc at `/api/redoc/`
- JSON schema at `/api/schema/`
- PDF generated monthly via CI

## DOC-02: User Guides (Detail)

### Roles
1. **Company Owner Guide** (create company, manage, configure)
2. **Quality Monitor Guide** (review, decisions, exceptions)
3. **Employee Guide** (execute tasks, upload evidence)
4. **Platform Admin Guide** (support, lifecycle)
5. **Connector Owner Guide** (validate, health, update)

### Structure
```
docs/user-guides/
├── 01_OWNER/
│   ├── 01_Getting_Started.md
│   ├── 02_Company_Setup.md
│   ├── 03_Branches.md
│   ├── 04_Users_Roles.md
│   ├── 05_AI_Provider.md
│   ├── 06_Exports.md
│   ├── 07_Backups.md
│   ├── 08_Reports.md
│   └── README.md
├── 02_MONITOR/
│   ├── 01_Getting_Started.md
│   ├── 02_Review_Queue.md
│   ├── 03_Issue_Resolution.md
│   └── README.md
├── 03_EMPLOYEE/
│   ├── 01_Getting_Started.md
│   ├── 02_Task_Execution.md
│   ├── 03_Evidence_Capture.md
│   └── README.md
├── 04_ADMIN/
│   ├── 01_Tenant_Lifecycle.md
│   ├── 02_Support_Access.md
│   └── README.md
└── 05_CONNECTOR/
    ├── 01_Installation.md
    ├── 02_Configuration.md
    ├── 03_Health_Monitoring.md
    └── README.md
```

## DOC-03: Runbooks (Detail)

### Structure
```
docs/runbooks/
├── 00_INDEX.md
├── 01_API_DOWN.md
├── 02_DATABASE_CONNECTION_LOST.md
├── 03_REDIS_DOWN.md
├── 04_CELERY_QUEUE_BACKED_UP.md
├── 05_BACKUP_FAILED.md
├── 06_RESTORE_TESTING.md
├── 07_AI_PROVIDER_FAILURE.md
├── 08_CONNECTOR_OFFLINE.md
├── 09_AUDIT_CHAIN_BROKEN.md
├── 10_DSR_REQUEST_RECEIVED.md
├── 11_BREACH_DETECTED.md
└── 12_HIGH_TENANT_CHURN.md
```

### Runbook template
```markdown
# Runbook: [Incident name]

## Summary
[Short description]

## Indicators
- [How do we know this incident is ongoing?]

## Immediate response
1. [Step 1]
2. [Step 2]

## Investigation
- [Diagnostic commands]

## Solution
- [Fix steps]

## Follow-up
- [What to monitor after the fix]

## Escalation
- [When and why to escalate]

## Post-mortem
- [Post-incident report template]
```

## DOC-04: Incident Response (Detail)

### Playbooks
1. **Security Breach**
2. **Data Loss**
3. **Service Outage**
4. **Privacy Violation**
5. **Insider Threat**

### Post-Mortem Template
```markdown
# Post-Mortem: [Title]

## Summary
[What happened, when, impact]

## Timeline
| Time | Event |
|---|---|
| 14:00 | first alert |
| 14:15 | escalated |
| 14:30 | contained |
| ... | ... |

## Root Cause
[Root cause]

## Lessons Learned
[Lessons]

## Action Items
- [ ] [Action 1] - [Owner] - [Date]
- [ ] [Action 2] - [Owner] - [Date]
```

## DOC-05: Troubleshooting (Detail)

### Common Problems
1. Login fails → CSRF expired
2. Evidence upload fails → file too large
3. Review decision rejected → branch scope
4. Backup fails → disk full
5. Slow API → DB connection pool saturated
6. AI not responding → provider config
7. Connector offline → network issue
8. Email not sent → SMTP config

### For each problem
- **Symptoms**
- **Diagnosis** (commands)
- **Solutions** (multiple options)
- **Prevention**
