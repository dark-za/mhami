from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.utils import DatabaseError
from redis.exceptions import RedisError


class Command(BaseCommand):
    help = "Check native runtime dependencies and writable application paths."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Fail when an optional dependency is unavailable.",
        )

    def handle(self, *args, **options):
        strict = options["strict"]
        failures: list[str] = []
        self._check_database(failures)
        self._check_redis(failures, strict)
        self._check_path("MEDIA_ROOT", Path(settings.MEDIA_ROOT), failures)
        self._check_path("STATIC_ROOT", Path(settings.STATIC_ROOT), failures)
        self._check_path("BACKUP_STORAGE_ROOT", Path(settings.BACKUP_STORAGE_ROOT), failures)
        self._check_path("BACKUP_RESTORE_ROOT", Path(settings.BACKUP_RESTORE_ROOT), failures)
        if failures:
            for failure in failures:
                self.stderr.write(self.style.ERROR(f"FAIL: {failure}"))
            raise CommandError(f"Native doctor found {len(failures)} problem(s).")
        self.stdout.write(self.style.SUCCESS("Native runtime checks passed."))

    def _check_database(self, failures: list[str]) -> None:
        try:
            connection.ensure_connection()
        except DatabaseError as exc:
            failures.append(f"database connection failed: {exc.__class__.__name__}")
        else:
            self.stdout.write("OK: database connection")

    def _check_redis(self, failures: list[str], strict: bool) -> None:
        redis_url = getattr(settings, "CELERY_BROKER_URL", "")
        if not redis_url:
            failures.append("CELERY_BROKER_URL is empty")
            return
        try:
            from redis import Redis

            Redis.from_url(redis_url, socket_timeout=1).ping()
        except (ImportError, OSError) as exc:
            message = f"redis client or connection is unavailable: {exc.__class__.__name__}"
            if strict:
                failures.append(message)
            else:
                self.stdout.write(self.style.WARNING(f"WARN: {message}"))
        except RedisError as exc:
            message = f"redis connection failed: {exc.__class__.__name__}"
            if strict:
                failures.append(message)
            else:
                self.stdout.write(self.style.WARNING(f"WARN: {message}"))
        else:
            self.stdout.write("OK: redis connection")

    def _check_path(self, label: str, path: Path, failures: list[str]) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".mhami-write-test"
            probe.write_text("ok", encoding="ascii")
            probe.unlink()
        except OSError as exc:
            failures.append(f"{label} is not writable ({path}): {exc.__class__.__name__}")
        else:
            self.stdout.write(f"OK: {label} {path}")
