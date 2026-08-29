# Documentation Authority

## Status

These documents describe the product baseline, architecture, controls, runbooks, and release constraints for the running Mhami foundation.

## Precedence

1. `PROJECT_CHARTER.md` defines product intent and non-negotiable outcomes.
2. `CONSTITUTION_AMENDMENTS.md` records approved engineering constraints and amendments.
3. `REQUIREMENTS_BASELINE.md`, `ARCHITECTURE_BASELINE.md`, `DOMAIN_MODEL.md`, and `SECURITY_AND_DATA_BASELINE.md` define the approved baseline.
4. `GOVERNANCE.md`, `BRANCH_POLICY.md`, `COMMIT_POLICY.md`, `RELEASE_POLICY.md`, `SECRET_MANAGEMENT.md`, `CI_QUALITY_GATES.md`, and `DIRECTORY_OWNERSHIP.md` define repository foundation controls.
5. `DELIVERY_ROADMAP.md` and `phases/` define implementation order and gates.
6. ADRs document future approved architectural changes.

## Change Control

Any change to scope, role permissions, tenant isolation, AI behavior, retention, evidence handling, security, or a completed phase must be documented before implementation. Use an ADR for foundational decisions.

## Documentation Areas

- `phases/`: authoritative execution phases and exit criteria.
- `contracts/`: implementation-independent contracts for external boundaries.
- `adr/`: architecture decision records.
- `legal/`: legal-policy drafting space; placeholder text is not legal advice.
- `runbooks/`: operational procedures.
- `templates/`: reusable documentation templates.
- `governance` is expressed through the root governance documents listed above.
