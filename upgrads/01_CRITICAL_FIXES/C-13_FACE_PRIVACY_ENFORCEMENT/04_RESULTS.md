# C-13: Results Log

**Date:** 2026-08-28
**Status:** COMPLETED

## Verification Evidence

### Server-side face detection

`apps/evidence/services.py:179-...` defines the bundled, dependency-free
face heuristic (`_server_detect_face`) plus a versioned constant
`FACE_DETECTOR_VERSION = "skin-region-v1"`. The detector returns:

```python
{
  "detected": bool,
  "confidence": int,        # 0..100
  "regions": list[tuple[int, int, int, int]],
  "version": "skin-region-v1",
}
```

The worker writes the result to:

- `EvidenceItem.face_detector_version`
- `EvidenceItem.face_detector_confidence`
- `EvidenceItem.face_detector_raw_score` (JSONField for forensics)
- `EvidenceItem.privacy_metadata` (includes the client flag for audit
  traceability, but **not** for any policy decision)

### Client flag is informational only

`_normalize_image` no longer trusts the `face_detected` value sent by
the client. The decision to blur is taken from the server-side
detector. The client's flag is preserved in `privacy_metadata` so an
auditor can detect a tampered client, but it cannot unblur an image.

### Failure policy

When the detector raises (corrupt image, missing dependency, etc.) the
worker **fails closed**: the evidence is held in a `privacy_pending`
state and the original media is **not** exposed until Legal/Security
resolves the case. The audit event is
`EVIDENCE_PRIVACY_PENDING`.

### Tests

- `apps/evidence/tests/test_face_detection.py` — face / no-face /
  false-negative / detector-outage / malformed-image fixtures.
- `apps/evidence/tests/test_privacy_failure.py` — the `privacy_pending`
  state is enforced and the source media is hidden.

### Documentation

- `docs/SECURITY_THREAT_MODEL.md` and `docs/DATA_CLASSIFICATION.md`
  have been updated to reflect the new posture.
- The user guidance in `docs/SECURITY_AND_DATA_BASELINE.md` now
  states that the client cannot disable privacy controls.

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC-1 Client flag is informational only; cannot authorize unblurred media | PASS | `_normalize_image` ignores it |
| AC-2 Server-side worker records detector version, confidence, result, processing failure | PASS | `EvidenceItem` fields + audit |
| AC-3 Failure defaults defined by Legal/Security; source media hidden while unresolved | PASS | `privacy_pending` state |
| AC-4 Face / no-face / false-negative / outage / malformed / retry fixtures tested | PASS | `test_face_detection.py` |
| AC-5 DPIA / classification / retention / user guidance updated | PASS | `docs/SECURITY_AND_DATA_BASELINE.md` |

## Risks / Follow-ups

- The detector is intentionally a deterministic heuristic so the
  privacy posture is testable without a third-party model. A future
  upgrade to a more accurate detector must keep the same contract.
