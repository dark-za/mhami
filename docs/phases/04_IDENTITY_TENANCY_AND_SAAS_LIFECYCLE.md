# Phase 04: Identity, Tenancy, and SaaS Lifecycle

## Status

Complete.

## Objective

Deliver isolated company tenancy, individual access control, self-service registration, legal acceptance, MFA, company lifecycle, and branch membership before operational work is available.

## Entry Requirements

- Phase 03 is complete.
- Legal-policy drafts and company-status rules are approved.
- Company code uniqueness and tenant-scope design are reviewed.

## Scope

- Implement Company registration with company name, owner identity, permanent unique company code, contact channel, industry, and 30-day trial.
- Implement automated registration-abuse controls without mandatory identity verification.
- Implement Platform Administrator, Company Owner, Quality Monitor, Employee, and named Support Actor permissions.
- Implement company scope, branch scope, one-active-branch employee membership, job roles, and employee transfer history.
- Implement simple weekly shifts as schedule inputs, not attendance.
- Implement owner and platform MFA through TOTP and passkeys.
- Implement versioned owner acceptance for terms, privacy, and AI transfer policies, plus employee acknowledgement.
- Implement trial extension, suspension, read-only export window, deletion scheduling, and revocable support authorization.
- Implement owner-managed employee account lifecycle and documented manual owner recovery.

## Required Software and Services

- Django authentication and session framework.
- PostgreSQL constraints and indexes for tenant and branch scoping.
- Rate limiting backed by Redis.
- MFA libraries or code selected through ADR and security review.

## Security and Data Requirements

- Tenant identifiers are stable UUIDs; company code is not a security secret.
- Every object lookup uses company scope and applicable branch scope.
- Support access must require a current authorization grant and log the acting individual.
- Suspended companies cannot mutate operational data.
- Legal acceptance versions and timestamps are immutable records.

## Deliverables

- Identity, tenancy, organization, and SaaS lifecycle modules.
- Registration, login, logout, MFA, bootstrap, and account-management APIs.
- Owner, monitor, employee, and platform administration routes.
- Legal-acceptance and tenant-status audit events.
- Tenant-isolation and role-permission test suite.

## Verification

- A user cannot see, guess, export, or mutate another company data.
- A monitor cannot manage unassigned branches.
- A transferred employee retains history but loses prior branch access according to policy.
- Owner and platform MFA are enforced.
- Trial expiration, suspension, read-only export, and deletion scheduling behave as documented.
- Revoking support authorization blocks future support requests immediately.

## Exit Criteria

- A self-registered company can create its authorized organization safely.
- Tenant and branch isolation are demonstrably enforced.
- Every later module can rely on stable identities, company scope, branch scope, and policy acceptance.

## Stop Conditions

- Shared user credentials are introduced.
- Tenant or branch filtering is optional.
- Support or platform actors can bypass company consent without an explicit audited emergency policy.
