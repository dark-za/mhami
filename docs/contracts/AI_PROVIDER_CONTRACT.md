# AI Provider Contract

## Purpose

Allow each company to select an AI provider without binding business modules to a vendor or allowing arbitrary executable plugins.

## Required Operations

- Image verification using task criteria, approved reference media, and a blurred evidence image.
- Provider health check.
- Structured response validation.

## Required Request Context

- Opaque analysis identifier.
- Template and criteria version identifiers.
- Risk level and allowed decision policy.
- Blurred evidence derivative and permitted reference media.
- No employee name, phone, credentials, session identifiers, or unrelated tenant data.

## Required Response Semantics

- Decision: pass, retry, or review.
- Criterion-level result: pass, fail, or uncertain.
- Reason, confidence, image-quality result, and flags.
- Provider/model/version metadata when available.

## Rules

- Unknown response fields may be rejected by schema policy.
- Invalid, incomplete, timed-out, or unavailable responses become review signals.
- The provider never receives execution tools or authority to mutate platform data.
- Providers with a different protocol require a reviewed adapter added through source control.
