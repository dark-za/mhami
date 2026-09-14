# Roles and Access

## Supported Roles

Mhami has three roles. All access enforcement happens in the backend; the frontend displays role-appropriate navigation but never enforces authorization.

### Owner

- Full administrative access to the entire installation and all organization data.
- Creates and manages branches, users, roles, task templates, policies, AI provider configuration, exports, and backups.
- Can view and manage all branches and all employees.
- Provisions the first owner account locally via `python manage.py provision_owner`.

### Monitor

- Manages employees and tasks only within branches assigned by the owner.
- Can view and process evidence, make review decisions, create corrective tasks, and manage task reassignment within the assigned branches.
- Decides employee cancellation, unable-to-complete, suggestion, and transfer requests only in assigned branches.
- Cannot access branches not assigned to that monitor.
- Cannot modify organization-wide settings, policies, or AI provider configuration.

### Employee

- Works only with tasks assigned to that employee.
- Can capture evidence, start and complete assigned tasks, submit transfer, cancellation, and unable-to-complete requests, and report issues within a task.
- Cannot view other employees' tasks or evidence.
- Cannot perform review decisions or manage other users.

## Authorization Enforcement

- Every API endpoint resolves the authenticated user's role and branch assignments before processing the request.
- Branch-sensitive queries apply branch scoping before object lookup.
- Role checks are applied by API views and domain services.
- Frontend bootstrap permissions control navigation visibility; they do not control data access.

## User Provisioning

The owner creates all user accounts locally. There is no self-registration. The owner assigns roles and branch memberships directly. Provisioning is local and single-organization: one installation serves one organization, created once via `provision_owner`; no public registration endpoint exists.

## Branch Assignments

- An employee can be assigned to one or more active branches by the owner.
- A monitor is assigned to one or more branches by the owner.
- The owner has access to all branches.

Branch assignments are stored server-side and enforced on every request. Client-side state does not influence authorization.

## No Central Support Path

There is no central or upstream support-account path into a deployment. Product accounts are only owner, monitor, and employee. The organization that operates the installation owns its infrastructure, accounts, and data.
