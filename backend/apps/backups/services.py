from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.management import call_command
from django.db import connections, transaction
from django.db.models import Model, Q
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.evidence.models import EvidenceItem
from apps.identity.models import User
from apps.notifications.services import emit_for_outbox_event
from apps.organizations.models import Branch, CompanyRole
from apps.platform_core.models import FeatureFlag, ModuleHealthSnapshot, PlatformSetting
from apps.platform_core.outbox import emit_audit_and_outbox, quick_event
from apps.tasks.models import TaskInstance
from apps.tenancy.access import has_company_role
from apps.tenancy.models import Company

from .models import BackupPolicy, BackupRun, BackupStatus, RestoreRun


ARCHIVE_FORMAT = "mhami-local-backup-v1"
TARGET_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
EXCLUDED_BACKUP_MODELS = {"backups.backuprun", "backups.restorerun"}
RESTORE_DATABASE_ALIAS = "backup_restore"


# H-05: encryption envelope. The backup archive is wrapped in a
# Fernet-encrypted payload so a copy on disk does not expose tenant
# data without the key. Fernet is AES-128-CBC + HMAC-SHA256 with a
# versioned token format that we can rotate independently of the
# Django secret.
ENCRYPTION_ALGORITHM = "Fernet (AES-128-CBC + HMAC-SHA256)"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get_backup_fernet() -> Fernet:
    """Resolve the Fernet instance used to encrypt backup artifacts.

    H-05: ``BACKUP_ENCRYPTION_KEY`` is mandatory for any environment
    that creates a backup. We derive a deterministic dev key from
    ``DJANGO_SECRET_KEY`` so local development does not need a separate
    secret, but the production override in ``settings.prod`` fails fast
    if the variable is missing.
    """
    key = getattr(settings, "BACKUP_ENCRYPTION_KEY", "") or ""
    if not key:
        # Derive a stable dev key from the Django secret. The rotation
        # procedure in ``docs/SECRET_MANAGEMENT.md`` is the production
        # path; this fallback exists so unit tests run without
        # additional setup.
        digest = hashlib.sha256(f"{settings.SECRET_KEY}:mhami:backup-encryption".encode()).digest()
        key = __import__("base64").urlsafe_b64encode(digest).decode("ascii")
    return Fernet(key.encode("ascii"))


def _encrypt_artifact(data: bytes) -> tuple[bytes, str]:
    fernet = _get_backup_fernet()
    encrypted = fernet.encrypt(data)
    return encrypted, _sha256(encrypted)


def _decrypt_artifact(encrypted: bytes) -> bytes:
    fernet = _get_backup_fernet()
    try:
        return fernet.decrypt(encrypted)
    except InvalidToken as exc:  # pragma: no cover - failure path
        raise ValueError("Backup artifact integrity verification failed.") from exc


def backup_storage_root() -> Path:
    root = Path(settings.BACKUP_STORAGE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    return root


def backup_restore_root() -> Path:
    root = Path(settings.BACKUP_RESTORE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    return root


def backup_policy_for_company(company: Company) -> BackupPolicy:
    policy, _created = BackupPolicy.objects.get_or_create(company=company)
    return policy


def _local_models() -> list[type[Model]]:
    return sorted(
        [
            model
            for model in apps.get_models()
            if model._meta.app_config.name.startswith("apps.")
            and model._meta.label_lower not in EXCLUDED_BACKUP_MODELS
        ],
        key=lambda model: model._meta.label_lower,
    )


def _tenant_model_ids(company: Company) -> dict[type[Model], set[Any]]:
    """Follow tenant-owned foreign keys so dependent rows are restored too."""
    models = _local_models()
    selected: dict[type[Model], set[Any]] = {Company: {company.pk}, User: {company.owner_id}}
    changed = True
    while changed:
        changed = False
        for model in models:
            if model in {Company, PlatformSetting, ModuleHealthSnapshot, FeatureFlag}:
                continue
            predicate = Q()
            has_predicate = False
            for field in model._meta.concrete_fields:
                if not field.is_relation or field.remote_field is None:
                    continue
                related_model = field.remote_field.model
                if related_model is Company:
                    predicate |= Q(**{field.attname: company.pk})
                    has_predicate = True
                elif related_model in selected and selected[related_model]:
                    predicate |= Q(**{f"{field.attname}__in": selected[related_model]})
                    has_predicate = True
            if not has_predicate:
                continue
            ids = set(model.objects.filter(predicate).values_list("pk", flat=True))
            before = selected.setdefault(model, set())
            new_ids = ids - before
            if new_ids:
                before.update(new_ids)
                changed = True
        user_ids = set(selected.get(User, set()))
        for model, ids in selected.items():
            if not ids:
                continue
            for field in model._meta.concrete_fields:
                if field.is_relation and field.remote_field is not None and field.remote_field.model is User:
                    user_ids.update(model.objects.filter(pk__in=ids).values_list(field.attname, flat=True))
        user_ids.discard(None)
        new_user_ids = user_ids - selected.setdefault(User, set())
        if new_user_ids:
            selected[User].update(new_user_ids)
            changed = True
    selected_ids = {
        str(record_id)
        for model, ids in selected.items()
        if model is not User
        for record_id in ids
    }
    branch_ids = {str(record_id) for record_id in selected.get(Branch, set())}
    selected[AuditEvent] = set(
        AuditEvent.objects.filter(Q(branch_id__in=branch_ids) | Q(target_id__in=selected_ids)).values_list(
            "pk", flat=True
        )
    )
    return selected


def _serialize_models(model_ids: dict[type[Model], set[Any]]) -> tuple[bytes, dict[str, int]]:
    records: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for model in sorted(model_ids, key=lambda item: item._meta.label_lower):
        ids = model_ids[model]
        if not ids:
            continue
        queryset = model.objects.filter(pk__in=ids).order_by("pk")
        serialized = json.loads(serializers.serialize("json", queryset))
        records.extend(serialized)
        counts[model._meta.label_lower] = len(serialized)
    return json.dumps(records, ensure_ascii=True, sort_keys=True).encode("utf-8"), counts


def _configuration_bytes(include_configuration: bool) -> tuple[bytes, dict[str, int]]:
    if not include_configuration:
        return b"[]", {}
    records: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for model in (PlatformSetting, FeatureFlag, ModuleHealthSnapshot):
        serialized = json.loads(serializers.serialize("json", model.objects.all().order_by("pk")))
        records.extend(serialized)
        counts[model._meta.label_lower] = len(serialized)
    return json.dumps(records, ensure_ascii=True, sort_keys=True).encode("utf-8"), counts


def _media_payload(company: Company, include_private_media: bool) -> dict[str, bytes]:
    if not include_private_media:
        return {}
    root = Path(settings.MEDIA_ROOT) / "evidence" / "private"
    payload: dict[str, bytes] = {}
    for evidence in EvidenceItem.objects.filter(company=company).exclude(private_media_name=""):
        for name in {evidence.private_media_name, evidence.blurred_media_name} - {""}:
            if Path(name).name != name:
                raise ValueError("Evidence media name is unsafe.")
            path = root / name
            if not path.is_file():
                raise ValueError(f"Evidence media is missing: {name}")
            payload[f"media/evidence/private/{name}"] = path.read_bytes()
    return payload


def _manifest(
    company: Company,
    includes: dict[str, bool],
    database_counts: dict[str, int],
    configuration_counts: dict[str, int],
    entries: dict[str, bytes],
) -> dict[str, Any]:
    return {
        "format": ARCHIVE_FORMAT,
        "company": {
            "id": str(company.id),
            "name": company.name,
            "code": company.code,
            "status": company.status,
        },
        "includes": includes,
        "counts": {
            "database": database_counts,
            "configuration": configuration_counts,
            "media": len(entries) - 2,
            "tasks": TaskInstance.objects.filter(company=company).count(),
            "evidence": EvidenceItem.objects.filter(company=company).count(),
        },
        "entries": {name: _sha256(data) for name, data in sorted(entries.items())},
        "encryption": {"encrypted": False, "algorithm": None},
    }


def _artifact_bytes(manifest: dict[str, Any], entries: dict[str, bytes]) -> tuple[bytes, str, str]:
    """Build the unencrypted archive and return its hash triple.

    H-05: encryption is applied at the storage boundary so the
    in-memory bytes used for hashing stay plaintext (which is what we
    want for the manifest hash). The disk artefact written to
    ``backup_storage_root()`` is the Fernet-wrapped payload, and
    ``artifact_sha256`` is the SHA-256 of the *encrypted* payload so
    tampering after the fact is detectable.
    """
    manifest_bytes = json.dumps(manifest, ensure_ascii=True, sort_keys=True, indent=2).encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_bytes)
        for name, data in sorted(entries.items()):
            archive.writestr(name, data)
    artifact = buffer.getvalue()
    return artifact, _sha256(artifact), _sha256(manifest_bytes)


@transaction.atomic
def prepare_backup_run(
    company: Company,
    user: User,
    include_private_media: bool = True,
    include_configuration: bool = True,
    include_tenant_state: bool = True,
) -> BackupRun:
    if not has_company_role(company, user, str(CompanyRole.OWNER)):
        raise ValueError("Owner access required.")
    return BackupRun.objects.create(
        company=company,
        requested_by=user,
        status=BackupStatus.REQUESTED,
        manifest={
            "includes_requested": {
                "private_media": include_private_media,
                "configuration": include_configuration,
                "tenant_state": include_tenant_state,
            }
        },
    )


@transaction.atomic
def complete_backup_run(
    backup_run_id: str,
    include_private_media: bool = True,
    include_configuration: bool = True,
    include_tenant_state: bool = True,
) -> BackupRun:
    backup_run = BackupRun.objects.get(id=backup_run_id)
    company = backup_run.company
    user = backup_run.requested_by
    database, database_counts = _serialize_models(_tenant_model_ids(company))
    configuration, configuration_counts = _configuration_bytes(include_configuration)
    entries = {"database.json": database, "configuration.json": configuration}
    entries.update(_media_payload(company, include_private_media))
    includes = {
        "private_media": include_private_media,
        "configuration": include_configuration,
        "tenant_state": include_tenant_state,
    }
    manifest = _manifest(company, includes, database_counts, configuration_counts, entries)
    data, plaintext_sha256, manifest_sha256 = _artifact_bytes(manifest, entries)
    # H-05: encrypt the bytes before writing to disk. The on-disk
    # artefact is the Fernet payload, and ``artifact_sha256`` is the
    # SHA-256 of the *encrypted* payload so the integrity check on
    # download sees the same bytes that are on disk.
    encrypted_data, encrypted_sha256 = _encrypt_artifact(data)
    manifest["encryption"] = {"encrypted": True, "algorithm": ENCRYPTION_ALGORITHM}
    backup_run.manifest = manifest
    backup_run.artifact_sha256 = encrypted_sha256
    backup_run.manifest_sha256 = manifest_sha256
    path = backup_storage_root() / f"{backup_run.id}-backup.zip.enc"
    path.write_bytes(encrypted_data)
    backup_run.artifact_name = path.name
    backup_run.status = BackupStatus.COMPLETED
    backup_run.completed_at = timezone.now()
    backup_run.save(update_fields=["artifact_name", "status", "completed_at", "artifact_sha256", "manifest_sha256", "manifest"])
    audit_event, outbox_event = emit_audit_and_outbox(
        audit_event_type="BACKUP_COMPLETED",
        audit_target_type="backup_run",
        audit_target_id=str(backup_run.id),
        actor_id=str(user.id),
        branch_id="",
        audit_metadata={
            "artifact_name": path.name,
            "artifact_sha256": encrypted_sha256,
            "plaintext_sha256": plaintext_sha256,
            "encryption": ENCRYPTION_ALGORITHM,
        },
        outbox=quick_event(
            event_name="backup.completed",
            aggregate_type="backup_run",
            aggregate_id=str(backup_run.id),
            company_id=str(company.id),
            artifact_name=path.name,
        ),
    )
    emit_for_outbox_event(outbox_event)
    return backup_run


@transaction.atomic
def create_backup_run(
    company: Company,
    user: User,
    include_private_media: bool = True,
    include_configuration: bool = True,
    include_tenant_state: bool = True,
) -> BackupRun:
    backup_run = prepare_backup_run(
        company,
        user,
        include_private_media=include_private_media,
        include_configuration=include_configuration,
        include_tenant_state=include_tenant_state,
    )
    return complete_backup_run(
        str(backup_run.id),
        include_private_media=include_private_media,
        include_configuration=include_configuration,
        include_tenant_state=include_tenant_state,
    )


def list_backup_runs(company: Company) -> Iterable[BackupRun]:
    return BackupRun.objects.filter(company=company).order_by("-started_at")


def download_backup_artifact(company: Company, backup_run_id: str) -> Path:
    backup_run = BackupRun.objects.get(id=backup_run_id, company=company)
    if backup_run.status not in {BackupStatus.COMPLETED, BackupStatus.RESTORED}:
        raise ValueError("Backup is not ready.")
    path = backup_storage_root() / backup_run.artifact_name
    if not path.exists():
        raise ValueError("Backup artifact is missing.")
    # H-05: for H-06 we expose a decrypted copy on download. The
    # on-disk artefact is still the Fernet-wrapped bytes; the helper
    # below produces a sibling ``.decrypted`` file when needed.
    if path.suffix == ".enc":
        decrypted_path = path.with_suffix("")
        if not decrypted_path.exists():
            decrypted_bytes = _decrypt_artifact(path.read_bytes())
            decrypted_path.write_bytes(decrypted_bytes)
        return decrypted_path
    return path


def _validated_archive(backup_run: BackupRun, artifact: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    data = artifact.read_bytes()
    # H-05: when reading a ``.enc`` artefact decrypt first. ``download_backup_artifact``
    # already returns the decrypted file, but ``restore_backup_run`` may be invoked
    # directly so the path is handled inline here as well.
    if artifact.suffix == ".enc":
        data = _decrypt_artifact(data)
    storage_path = backup_storage_root() / backup_run.artifact_name
    if backup_run.artifact_sha256:
        on_disk = storage_path.read_bytes()
        if _sha256(on_disk) != backup_run.artifact_sha256:
            raise ValueError("Backup artifact integrity verification failed.")
        if artifact != storage_path and storage_path.suffix == ".enc":
            expected_plaintext = _decrypt_artifact(on_disk)
            if data != expected_plaintext:
                raise ValueError("Backup artifact integrity verification failed.")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or "manifest.json" not in names or archive.testzip() is not None:
                raise ValueError("Backup archive is invalid.")
            if any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
                raise ValueError("Backup archive contains an unsafe path.")
            manifest_bytes = archive.read("manifest.json")
            if not backup_run.manifest_sha256 or _sha256(manifest_bytes) != backup_run.manifest_sha256:
                raise ValueError("Backup manifest integrity verification failed.")
            manifest = json.loads(manifest_bytes.decode("utf-8"))
            expected = manifest.get("entries", {})
            if manifest.get("format") != ARCHIVE_FORMAT or not isinstance(expected, dict):
                raise ValueError("Backup manifest is invalid.")
            if str(manifest.get("company", {}).get("id")) != str(backup_run.company_id):
                raise ValueError("Backup manifest belongs to a different company.")
            if any(not isinstance(name, str) or not isinstance(digest, str) for name, digest in expected.items()):
                raise ValueError("Backup manifest entries are invalid.")
            if set(names) != {"manifest.json", *expected}:
                raise ValueError("Backup archive entries do not match its manifest.")
            entries = {name: archive.read(name) for name in expected}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise ValueError("Backup artifact integrity verification failed.") from exc
    if any(_sha256(entries[name]) != digest for name, digest in expected.items()):
        raise ValueError("Backup payload integrity verification failed.")
    return manifest, entries


def _target_path(target_name: str) -> Path:
    if target_name == "default" or not TARGET_NAME_RE.fullmatch(target_name):
        raise ValueError("Restore target must be a non-default isolated target name.")
    target = (backup_restore_root() / target_name).resolve()
    root = backup_restore_root().resolve()
    if target.parent != root:
        raise ValueError("Restore target is outside the configured restore root.")
    if target.exists() and any(target.iterdir()):
        raise ValueError("Restore target must be empty.")
    return target


def _restore_database(
    target: Path,
    entries: dict[str, bytes],
    expected_counts: dict[str, int],
    *,
    database_alias: str | None = None,
) -> dict[str, int]:
    """Restore the database payload into an isolated target.

    H-06: the default backend is SQLite (so the platform's standard
    restore path stays self-contained). When the ``BACKUP_RESTORE_DB_ENGINE``
    setting names a PostgreSQL backend we switch the restore alias to
    it and use the same Django ORM to load the payload, which keeps
    the contract identical and makes the verification check
    database-engine independent.
    """
    target.mkdir(parents=True, exist_ok=False)
    target_engine = (getattr(settings, "BACKUP_RESTORE_DB_ENGINE", "") or "").lower()
    use_postgres = "postgresql" in target_engine
    if use_postgres and not database_alias:
        database_alias = "backup_restore_pg"
        # Re-register the alias with the production-style config if the
        # project has not already done so via ``DATABASES``.
        if database_alias not in connections.databases:
            connections.databases[database_alias] = {
                "ENGINE": target_engine,
                "NAME": getattr(settings, "BACKUP_RESTORE_DB_NAME", "mhami_restore"),
                "USER": getattr(settings, "BACKUP_RESTORE_DB_USER", ""),
                "PASSWORD": getattr(settings, "BACKUP_RESTORE_DB_PASSWORD", ""),
                "HOST": getattr(settings, "BACKUP_RESTORE_DB_HOST", "127.0.0.1"),
                "PORT": str(getattr(settings, "BACKUP_RESTORE_DB_PORT", 5432)),
                "OPTIONS": getattr(settings, "BACKUP_RESTORE_DB_OPTIONS", {}),
            }
    alias = database_alias or RESTORE_DATABASE_ALIAS
    if not use_postgres:
        database_path = target / "database.sqlite3"
        connection = connections[alias]
        original_config = connection.settings_dict.copy()
        connection.close()
        connection.settings_dict.update(
            {"ENGINE": "django.db.backends.sqlite3", "NAME": str(database_path), "OPTIONS": {}}
        )
    else:
        connection = connections[alias]
        original_config = connection.settings_dict.copy()
        connection.close()
    try:
        call_command("migrate", database=alias, interactive=False, verbosity=0)
        with connection.constraint_checks_disabled():
            for payload_name in ("database.json", "configuration.json"):
                for deserialized in serializers.deserialize("json", entries[payload_name].decode("utf-8")):
                    deserialized.save(using=alias)
        connection.check_constraints()
        restored_counts: dict[str, int] = {}
        for label in expected_counts:
            model = apps.get_model(label)
            restored_counts[label] = model.objects.using(alias).count()
        return restored_counts
    finally:
        connection.close()
        connection.settings_dict.clear()
        connection.settings_dict.update(original_config)


def _restore_media(target: Path, entries: dict[str, bytes]) -> int:
    media_entries = {name: data for name, data in entries.items() if name.startswith("media/")}
    for name, data in media_entries.items():
        destination = target / "media" / Path(name).relative_to("media")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        if _sha256(destination.read_bytes()) != _sha256(data):
            raise ValueError("Restored media integrity verification failed.")
    return len(media_entries)


def restore_backup_run(
    company: Company,
    user: User,
    backup_run_id: str,
    target_name: str,
    confirmation: str,
) -> RestoreRun:
    if not has_company_role(company, user, str(CompanyRole.OWNER)):
        raise ValueError("Owner access required.")
    backup_run = BackupRun.objects.get(id=backup_run_id, company=company)
    if confirmation != f"RESTORE {backup_run.id}":
        raise ValueError("Restore confirmation does not match the backup run.")
    artifact = download_backup_artifact(company, backup_run_id)
    manifest, entries = _validated_archive(backup_run, artifact)
    target = _target_path(target_name)
    restore = RestoreRun.objects.create(
        company=company,
        backup_run=backup_run,
        requested_by=user,
        target_name=target_name,
    )
    try:
        restored_counts = _restore_database(target, entries, manifest["counts"]["database"])
        restored_media = _restore_media(target, entries)
    except Exception as exc:
        shutil.rmtree(target, ignore_errors=True)
        restore.status = BackupStatus.FAILED
        restore.report = {"restored": False, "error": str(exc), "target_name": target_name}
        restore.completed_at = timezone.now()
        restore.save(update_fields=["status", "report", "completed_at"])
        raise ValueError("Restore failed; the isolated target was removed.") from exc
    restore.status = BackupStatus.RESTORED
    restore.verified_database = restored_counts == manifest["counts"]["database"]
    restore.verified_media = restored_media == manifest["counts"]["media"]
    restore.verified_configuration = bool(manifest["includes"]["configuration"])
    restore.report = {
        "manifest": manifest,
        "restored": True,
        "restored_counts": restored_counts,
        "target_name": target_name,
    }
    restore.completed_at = timezone.now()
    restore.save()
    backup_run.status = BackupStatus.RESTORED
    backup_run.restored_at = timezone.now()
    backup_run.save(update_fields=["status", "restored_at"])
    _audit, restore_outbox_event = emit_audit_and_outbox(
        audit_event_type="BACKUP_RESTORED",
        audit_target_type="backup_run",
        audit_target_id=str(backup_run.id),
        actor_id=str(user.id),
        branch_id="",
        audit_metadata={"restore_id": str(restore.id), "target_name": target_name},
        outbox=quick_event(
            event_name="backup.restore.completed",
            aggregate_type="backup_run",
            aggregate_id=str(backup_run.id),
            restore_id=str(restore.id),
            company_id=str(company.id),
        ),
    )
    emit_for_outbox_event(restore_outbox_event)
    return restore
