# Support Authorization Runbook

Grant and revoke temporary support access to a tenant for a legitimate operational request, with audit and tenant-owner visibility.

## Grant

1. Confirm the request is valid and the requester is a Platform Administrator or the tenant owner.
2. Record the reason and grant duration.
3. Grant support access to the support user for the company (see `apps/tenancy/services.grant_support`).
4. Announce the grant to the affected tenant owner.

## Use

- Support access is scoped to the tenant and must not bypass MFA, tenant isolation, or media authorization.
- All support actions are recorded in the audit log with the request reason.

## Revoke

- Revoke support access when the task is complete or the grant duration expires.
- Confirm the tenant owner is notified of what was accessed and when.

## Verification

- Support actions appear in the audit log.
- Support access cannot read another tenant's private media.
- Revoked access cannot re-authenticate.