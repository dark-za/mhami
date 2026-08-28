# ADR-0004: Browser-Only V1

## Status

Approved baseline.

## Context

The first release must minimize runtime complexity and avoid offline state synchronization and installable-app behavior.

## Decision

Ship V1 as a responsive browser application only. Do not require PWA installation or offline task mutation.

## Consequences

- No service worker or offline submission logic in V1.
- Chrome support can be tested and bounded clearly.
- Future offline behavior remains a separate phase or ADR.
