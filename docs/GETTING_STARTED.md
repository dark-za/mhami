# Getting Started

Mhami is installed and operated by one organization. It does not create a
shared Mhami account, a public registration page, or a support login. The
server owner controls the infrastructure, user accounts, integrations, and
data.

## Supported Host Systems

Use Docker Compose v2 on Linux, Windows with Docker Desktop and WSL 2, or
macOS with Docker Desktop. The application containers are Linux containers;
the host operating system does not need a local Python or Node installation
when Docker is used.

## First Installation

1. Follow [Installation](INSTALLATION.md) to copy `.env`, set unique secrets,
   and start the Compose stack.
2. Set `INITIAL_SETUP_TOKEN`, then open `/setup` to create the only
   organization and its owner. A local `provision_owner` command remains
   available for terminal-only deployments.
3. After setup, sign in at the frontend URL with that owner account. The
   setup route is closed and employees or monitors cannot self-register.

## Owner Setup Order

1. Create branches and descriptive job roles in **People**.
2. Create monitor accounts and assign each monitor to its permitted branches.
3. Create employee accounts and assign each employee to the correct branches
   and job role.
4. Configure AI, backups, exports, MCP access, and security settings only if
   the organization needs them. These controls are owner-only.
5. Create a scheduled task by choosing a branch, employee, instructions,
   recurrence, and time in **Tasks**. Mhami records an immutable instruction
   version before the schedule can create work.

## Daily Workflow

- **Owner:** sees the organization dashboard, controls all branches and
  sensitive configuration, and can review activity across the installation.
- **Monitor:** sees only owner-assigned branches, manages employees and tasks
  there, and accepts or rejects employee requests with a recorded decision.
- **Employee:** sees only assigned tasks, captures evidence, starts and
  completes work, requests a transfer, and sends a cancellation or
  unable-to-complete request with a reason.

Task requests are never decided by the target employee. Approval or rejection
is performed by a monitor with branch access or by the owner. Approval of a
cancellation cancels the task; approval of a transfer reassigns it and records
the complete audit trail.

## Operating Responsibility

The server owner is responsible for protecting credentials, taking backups,
choosing an AI provider, and deciding how user credentials are delivered to
staff. Mhami does not transmit deployment data to a central support account.
Read [Roles and Access](ROLES_AND_ACCESS.md), [Security](../SECURITY.md), and
the [runbooks](runbooks/README.md) before production use.
