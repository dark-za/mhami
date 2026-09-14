# Launch Decisions

## Deployment Model

**Status:** Approved by platform owner

**Recorded:** 2026-08-30

Mhami is an open-source, self-hosted application. Each installation is owned
and operated by one organization on infrastructure it controls. The project
does not operate a shared SaaS service, a multi-customer control plane, or a
support-account path into customer deployments.

The first owner is provisioned locally by the installation operator. Public
self-registration is disabled. The application does not create a second
organization after first provisioning.

## Access Model

**Status:** Approved by platform owner

**Recorded:** 2026-08-30

The supported roles are fixed and server-enforced:

- Owner: full access to installation and organization data.
- Monitor: manages employees and tasks only in branches assigned by the owner.
- Employee: works only with tasks assigned to that employee.

The owner creates real operational users and data locally. Capacity is chosen
by the organization operating the deployment; it is not a shared platform
limit.

## Data Classification At Launch

**Status:** Owner requirement; external launch remains gated

**Recorded:** 2026-08-30

The first launch is intended to use real employee and operational evidence
data. The installation owner creates and manages that data within its local
organization.

Because this includes real personal data, the organization operating the server
must verify its own internal and applicable legal requirements before launch.
The supplied notices explain the product model but do not claim legal or
regulatory compliance.
