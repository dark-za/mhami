# Backup and Restore

## Status

Phase 3b production baseline. The restore evidence record must be refreshed
after every production topology or encryption change.

## Purpose

Document the approved backup scope, external destination, encryption, schedule,
RPO, RTO, verification, and restoration procedure.

## Required coverage

- PostgreSQL data.
- Private media and face derivatives.
- Protected configuration and non-secret deployment metadata.
- Tenant lifecycle and deletion state required for correct restoration.
- Backup expiry and deletion behavior.

## Production destination and encryption

The local archive under `BACKUP_STORAGE_ROOT` is only a staging artifact. The
authoritative production copy is uploaded to the separately administered
external object-storage destination configured as `BACKUP_EXTERNAL_URI`, for
example:

```text
s3://<approved-backup-bucket>/<environment>/
```

The real bucket name is held in the deployment secret store and must never be
committed to this repository. The destination must satisfy all of the
following:

- a separate cloud account/project and region from the application host;
- private access over TLS, with a least-privileged upload/restore identity;
- client-side envelope encryption (KMS-managed key or an approved `age`/SOPS
  workflow) before upload, plus provider-side encryption at rest;
- versioning and immutable retention/object lock for the retention window; and
- access logging, MFA-protected administrative access, and a quarterly access
  review.

The current application archive records hashes and an encryption boundary but
does not encrypt the ZIP itself. Production backup automation must encrypt the
artifact before it leaves the host; a successful local ZIP is not evidence of
an encrypted external backup.

## Schedule and recovery objectives

- Celery Beat schedules `apps.backups.create_daily_backups` at **02:30 UTC**
  every day. Each tenant backup must be copied to the external destination and
  the upload/checksum result recorded.
- **RPO: at most 24 hours** of committed database, tenant-state, configuration,
  and private-media data. A two-hour operational grace period is alertable but
  does not change the objective.
- **RTO: at most 24 hours** from recovery declaration to a verified service-ready
  restore. The clock includes external artifact retrieval/decryption, isolated
  database and media restore, integrity checks, and application smoke tests.

The on-call operator must escalate a missed backup, failed upload, checksum
failure, or restore verification failure immediately; do not silently accept
an RPO/RTO exception.

## Backup verification

For each scheduled run:

1. Confirm the `BackupRun` is `completed`, its artifact and manifest SHA-256
   values are present, and all required scope flags are enabled.
2. Encrypt the artifact, upload it to `BACKUP_EXTERNAL_URI`, and verify the
   remote object checksum, encryption metadata, version ID, and retention lock.
3. Record the tenant, UTC completion time, destination/version, artifact and
   manifest hashes, encryption key ID, and operator/job identity.
4. Alert on any failed or missing tenant run. Keep the local staging artifact
   only for the configured short staging window.

## Restore verification exercise

At least quarterly, and before admitting the first external tenant, perform a
restore from the external encrypted copy into a newly provisioned isolated
target. Never restore over production. The operator must:

1. retrieve and decrypt the object using the restore-only identity;
2. verify the remote checksum, archive manifest hash, entry hashes, and
   expected company identity;
3. restore the database and private/blurred media into the isolated target;
4. verify database, configuration, tenant-state, evidence, and media counts
   against the manifest, including readable media files and their hashes;
5. run migrations and authenticated API smoke checks against the isolated
   target; and
6. record start/end UTC timestamps, artifact/version, operator, measured
   restore duration, RPO observed, RTO observed, all verification results, and
   discrepancies in the restore evidence report.

The exercise passes only when every verification item is true and the measured
RPO/RTO are within 24 hours. Delete the isolated target and temporary
decryption material after evidence capture.

## Application restore procedure

1. Confirm the backup run is `completed` and within retention.
2. Retrieve and decrypt the external artifact using the restore-only identity.
3. Verify the artifact, manifest, payload hashes, and tenant identity.
4. Restore into an isolated staging or recovery environment; never overwrite
   production data.
5. Verify database, media, configuration, and tenant-state counts.
6. Run migrations and authenticated API smoke checks.
7. Record the restore result, measured duration, RPO/RTO, and any discrepancy.

## Retention and deletion

Apply the approved retention policy to external object versions and local
staging artifacts. Deletion must be authenticated, logged, and irreversible
only after the retention/legal hold check succeeds.

## Rule

This document is not complete until a restore has been performed into an
isolated environment and the result is recorded.
