# C-13: Replace Client-Controlled Face Privacy Flag

## Discovery

The client submits `face_detected`; the server uses that value to decide whether
to blur evidence:

- `backend/apps/evidence/api/views.py:59-67`
- `backend/apps/evidence/services.py:152-163`

This is not a privacy control because a modified client can submit `false` for
an image containing a face.

## Goal

Prevent storage or disclosure of an unapproved face image through a trusted,
versioned server-side processing path and a safe failure policy.

## Acceptance Criteria

1. The client flag is informational only and cannot authorize unblurred media.
2. A server-side media worker/detector records detector version, confidence,
   result, and processing failure in auditable metadata.
3. Failure defaults are defined by Legal/Security; no source media is exposed
   while a required privacy decision is unresolved.
4. Face/no-face, false-negative, detector outage, malformed-image, and retry
   fixtures are tested.
5. DPIA, data classification, retention, and user guidance are updated before
   real pilot data is processed.

## Required Evidence

- Detector evaluation and limitation record.
- Privacy/Security approval of the failure policy.
- Media pipeline integration test output.
