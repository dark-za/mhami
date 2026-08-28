# ADR-0005: Private Media and Face-Derivative Handling

## Status

Approved baseline.

## Context

Evidence images may contain sensitive operational content and incidental people. Media must remain private and access-controlled.

## Decision

Keep media private behind application authorization. When a face is detected, preserve only a blurred derivative as the stored evidence and external-AI input.

## Consequences

- Public media URLs are not allowed.
- The platform reduces exposure of incidental personal imagery.
- Media processing must happen in a controlled worker pipeline.
