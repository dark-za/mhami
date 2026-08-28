# Phase 12 Capacity and Storage-Growth Findings

## Status

Issued by `PILOT-ASSURANCE-02`. Documents image/storage capacity, storage-growth projection, and recovery capacity for the Phase 12 exit dossier.

## Objective

Measure observed evidence volume and storage growth during the pilot and confirm the backup/recovery path remains current, so that capacity findings can be incorporated into the release candidate.

## Measurement Basis

Evidence media is modeled on `EvidenceItem`:

- `media_size_bytes` — stored size of each evidence media file.
- `media_width` / `media_height` — image dimensions.
- `evidence_type` — image vs. number vs. note vs. confirmation.
- `private_media_name`, `blurred_media_name` — private and face-blur derivatives.
- `duplicate_risk_score` — duplicate-risk signal per item.

Storage growth is captured on `PilotWeeklyReport.capacity_findings` (free text) alongside structured weekly metrics.

## Projected Pilot Volume (from `docs/PILOT_PROFILE.md`)

| Item | Expected range | Basis |
| --- | --- | --- |
| Evidence images per branch per day | ~150–400 at peak | Opening prep, mid-day inspection, close-of-day |
| Task instances per branch per day | ~30–60 | Checklists, inspections, handovers |
| Branches | 3 | Pilot target |
| Peak use periods | Opening prep, lunch service, close-of-day | Profile |

## Storage-Growth Model (Template)

Final values are populated from real pilot image volume. The projection model is defined here for the release candidate:

```
Per-branch daily image rate      = peak_images_per_branch / day
Per-branch media bytes           = sum(EvidenceItem.media_size_bytes) for image evidence
Storage growth / day / branch    = image_rate * average_media_size_bytes
Storage growth / day (platform)  = branches * growth / day / branch
Retention window                 = per legal retention policy
Projected footprint             = growth / day * retention_days
```

Derivatives (private original + blurred derivative) roughly double the per-item storage for face-containing images.

## Recovery and Backup Capacity

- Backup policy records `rpo_hours=24`, `rto_hours=24`, encryption, and inclusion flags for private media, configuration, and tenant state (`BackupPolicy`).
- Backup create/download/restore with DB verification is covered (`backups/tests/test_api.py:test_backup_create_download_restore`).
- Restore evidence is current per `docs/PHASE11_RESTORE_TEST_REPORT.md`.
- Backup dashboard indicator reflects the most recent `BackupRun` completion (`pilot/services.py`).

## Findings to Carry Into Release Candidate

1. **Per-branch capacity must be sized to the projected peak image rate**; the pilot deployment is staging-equivalent and must not be the production sizing baseline.
2. **Face-containing media doubles footprint** due to private + blurred derivatives; privacy sizing must account for it.
3. **Backup retains private media** by default (`includes_private_media=True`); recovery footprint must include media, not just database.
4. **Recovery targets (RPO/RTO 24h)** are configured; the release candidate must verify they are achievable at production scale, not assumed.
5. **Final growth figures require real pilot image volume** captured in `PilotWeeklyReport.capacity_findings`; they are not replaced by seed data.

## Conclusion

The platform records all fields needed to measure capacity and storage growth, and the backup/recovery path is test-verified and documented as current. **The release candidate must incorporate the observed pilot volume and storage-growth findings; final numbers are pending real pilot data.** Capacity is a tracked release-risk item (see updated risk register).
