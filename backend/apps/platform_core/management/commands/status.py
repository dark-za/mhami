from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.utils import DatabaseError
from redis import Redis
from redis.exceptions import RedisError


class Command(BaseCommand):
    help = "Report the native runtime status without exposing configuration secrets."

    def handle(self, *args, **options):
        database = "down"
        try:
            connection.ensure_connection()
            database = "up"
        except DatabaseError:
            database = "down"

        redis_status = "down"
        try:
            Redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=1).ping()
            redis_status = "up"
        except (RedisError, OSError):
            redis_status = "down"

        self.stdout.write(f"database={database}")
        self.stdout.write(f"redis={redis_status}")
        self.stdout.write(f"media_root={settings.MEDIA_ROOT}")
        self.stdout.write(f"backup_root={settings.BACKUP_STORAGE_ROOT}")
        if database == "down" or redis_status == "down":
            self.stderr.write(self.style.ERROR("Native runtime is not ready."))
            raise CommandError("Native runtime is not ready.")
        self.stdout.write(self.style.SUCCESS("Native runtime is ready."))
