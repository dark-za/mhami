# INFRA-03: Backup to S3 (and equivalent cloud object stores)

## 1. Discovery Summary

### Current State (As-Is)

**Problem:** The platform has a `BACKUP_EXTERNAL_URI` environment variable declared in `compose.prod.yml` (mandatory, fail-fast), but the **`apps.backups.services` module does not actually upload to that URI**. The backup runs end-to-end inside the container, is verified locally, and then is never replicated off-host. A host loss means data loss.

**Evidence gathered:**
- `compose.prod.yml` line 70: `BACKUP_EXTERNAL_URI: ${BACKUP_EXTERNAL_URI:?Set BACKUP_EXTERNAL_URI in .env}` — declared, not consumed.
- `backend/apps/backups/` — no `boto3`, no `azure-storage-blob`, no `google-cloud-storage` import.
- `infra/backup/README.md` — documents the **local** backup flow only.
- `docs/BACKUP_RESTORE.md` — covers local backup; does not cover S3/Azure/GCS.
- The `apps/backups/services.py` encryption is a single Fernet key from `MFA_ENCRYPTION_KEYS` — there is no envelope encryption, no `key_id`, and no key rotation.

### Impact

| Dimension | Impact |
|---|---|
| Functional | A host loss destroys all backups. |
| Security | The Fernet key, if leaked, decrypts every backup. No envelope encryption. |
| Operational | No retry on transient S3 errors; no checksum verification on download. |
| Compliance | Gate-B (PDPL) requires off-host, encrypted, retention-tagged backups. |

### Reproducible Evidence

```bash
# 1. Confirm BACKUP_EXTERNAL_URI is declared
Select-String -Path compose.prod.yml -Pattern "BACKUP_EXTERNAL_URI"
# Expected: 1 match (the env var)

# 2. Confirm no S3 import in the backend
Select-String -Path backend\apps\backups -Pattern "boto3" -Recurse
# Expected: 0 matches

# 3. Confirm no azure / gcs imports
Select-String -Path backend\apps\backups -Pattern "azure-storage-blob|google-cloud-storage" -Recurse
# Expected: 0 matches

# 4. Confirm no upload retry / checksum logic
Select-String -Path backend\apps\backups -Pattern "retry|checksum|sha256" -Recurse
# Expected: 0 matches (or only the local sha256)
```

---

## 2. Gap

| Dimension | Current | Target |
|---|---|---|
| `BACKUP_EXTERNAL_URI` consumed | no | yes (S3 / Azure / GCS) |
| Envelope encryption (AES-GCM + per-artifact KEK) | no | yes |
| `key_id` in artifact metadata | no | yes (so we can rotate KEKs) |
| Key rotation | no | yes (at least 2 active KEKs, newest for encrypt, all for decrypt) |
| Restricted temporary storage | partial | `/tmp` only, then deleted |
| Remote checksum verification | no | yes (download → re-hash → compare) |
| Upload retry with exponential backoff | no | yes (3 attempts, 2/4/8s) |
| Restore-from-external drill | no | yes (scheduled weekly) |
| S3 IAM least privilege | n/a | dedicated `BACKUP_S3_ROLE_ARN` |
| SSE-KMS | n/a | `ServerSideEncryption: aws:kms` |
| Versioning + lifecycle | n/a | S3 bucket policy enforced via Terraform |
| Retention policy | n/a | 30d daily, 90d weekly, 1y monthly |

---

## 3. Goal Statement

> Within **1 week (5 working days)**, implement an **envelope-encrypted, retry-with-backoff, checksum-verified** backup upload to S3 (and Azure/GCS adapters) with **per-artifact `key_id`**, **at-least-two active KEKs**, **restricted `/tmp` staging**, and a **weekly restore-from-external drill** that the platform owner can trigger.

### Acceptance Criteria

1. **AC-1:** `BACKUP_EXTERNAL_URI` is parsed and dispatched to the correct provider (S3 / Azure / GCS / local FS).
2. **AC-2:** The artifact is encrypted with **envelope encryption**: a per-artifact AES-GCM data key, itself encrypted by a KEK identified by `key_id` from the `MFA_ENCRYPTION_KEYS` JSON.
3. **AC-3:** The artifact header records `version`, `key_id`, `ciphertext_hash`, `created_at`, and `company_id`.
4. **AC-4:** Uploads use **SSE-KMS** (or Azure Customer-Managed Keys / GCS CMEK) with least-privilege IAM.
5. **AC-5:** Uploads retry with exponential backoff (3 attempts, 2/4/8s) and a circuit breaker.
6. **AC-6:** A `restore_from_external(key)` helper downloads, decrypts, and re-hashes the artifact; mismatch returns 422.
7. **AC-7:** A weekly management command `drill_restore_from_external` runs against a non-prod tenant and asserts the round-trip.
8. **AC-8:** The S3 bucket is created with versioning, lifecycle (30d → IA, 90d → Glacier, 365d → expire), and a deny-on-TLS-1.0 policy.
9. **AC-9:** The CI job `backup-drill` runs the drill weekly and uploads the round-trip report as an artifact.

---

## 4. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| S3 outage during upload | Medium | High | Retry with backoff; write to a local `pending_uploads/` queue; resume on next tick. |
| KEK leak | Low | High | Envelope encryption means each artifact has a unique data key; rotate KEKs quarterly. |
| Restore drill accidentally hits prod | Medium | High | Drill command must take `--tenant=test` and refuse `code != "test*"`. |
| Uploaded artifact is corrupted | Low | High | SHA-256 in header; verify on download. |
| Cost of IA / Glacier | Low | Low | Lifecycle policy + budget alert. |

---

## 5. Subtasks

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Implement `apps.backups.services.upload_to_external` (S3 / Azure / GCS) | Backend | not-started |
| 2 | Implement envelope encryption with `key_id` | Backend | not-started |
| 3 | Add the `BackupArtifact` header (version, key_id, hash, ts, company) | Backend | not-started |
| 4 | Implement `restore_from_external` with checksum verification | Backend | not-started |
| 5 | Add retry + circuit breaker | Backend | not-started |
| 6 | Add `drill_restore_from_external` management command | Backend | not-started |
| 7 | Provision the S3 bucket (versioning, lifecycle, TLS) | DevOps | not-started |
| 8 | Wire `BACKUP_S3_*` secrets into `compose.prod.yml` | DevOps | not-started |
| 9 | Add `backup-drill` weekly CI job | DevOps | not-started |
| 10 | Update `docs/BACKUP_RESTORE.md` and `CHANGELOG.md` | Tech Writer | not-started |

---

## 6. References

- [backend/apps/backups/](../../../backend/apps/backups/) — services module
- [compose.prod.yml](../../../compose.prod.yml) — env var declaration
- [infra/backup/README.md](../../../infra/backup/README.md) — local backup flow
- [docs/BACKUP_RESTORE.md](../../../docs/BACKUP_RESTORE.md)
- [docs/SECRET_MANAGEMENT.md](../../../docs/SECRET_MANAGEMENT.md) — secrets
- [H-05 — Backup Encryption](../../02_HIGH_PRIORITY/H-05_BACKUP_ENCRYPTION/00_DISCOVERY.md) — partner upgrade
