from __future__ import annotations

import shutil
from collections.abc import Iterable

import redis
from django.conf import settings
from django.db import connections
from django.http import HttpRequest, HttpResponse

from apps.backups.models import BackupRun, BackupStatus


QUEUE_NAMES = ("default", "media", "ai")


def _line(name: str, value: int | float, labels: dict[str, str] | None = None) -> str:
    rendered_labels = ""
    if labels:
        rendered_labels = "{" + ",".join(f'{key}="{value}"' for key, value in labels.items()) + "}"
    return f"{name}{rendered_labels} {value}\n"


def _database_up() -> int:
    try:
        connections["default"].ensure_connection()
        return 1
    except Exception:
        return 0


def _redis_metrics() -> tuple[int, dict[str, int]]:
    depths = {queue: 0 for queue in QUEUE_NAMES}
    try:
        client = redis.Redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=0.5)
        client.ping()
        for queue in QUEUE_NAMES:
            result = client.llen(queue)
            depths[queue] = result if isinstance(result, int) else 0
        return 1, depths
    except Exception:
        return 0, depths


def _worker_count() -> int:
    try:
        from config.celery import app

        return len(app.control.ping(timeout=0.5))
    except Exception:
        return 0


def _backup_timestamps() -> tuple[float, float]:
    try:
        successful = (
            BackupRun.objects.filter(
                status__in=[BackupStatus.COMPLETED, BackupStatus.RESTORED],
                completed_at__isnull=False,
            )
            .order_by("-completed_at")
            .values_list("completed_at", flat=True)
            .first()
        )
        failed = (
            BackupRun.objects.filter(status=BackupStatus.FAILED)
            .order_by("-started_at")
            .values_list("started_at", flat=True)
            .first()
        )
    except Exception:
        return 0, 0
    return (
        successful.timestamp() if successful else 0,
        failed.timestamp() if failed else 0,
    )


def metrics_payload() -> Iterable[str]:
    redis_up, queue_depths = _redis_metrics()
    try:
        disk = shutil.disk_usage(settings.MEDIA_ROOT)
        disk_free = disk.free
        disk_size = disk.total
    except OSError:
        disk_free = 0
        disk_size = 0
    successful_backup, failed_backup = _backup_timestamps()
    yield _line("platform_up", 1)
    yield _line("platform_database_up", _database_up())
    yield _line("platform_redis_up", redis_up)
    yield _line("platform_celery_workers", _worker_count())
    for queue, depth in queue_depths.items():
        yield _line("platform_celery_queue_depth", depth, {"queue": queue})
    yield _line("platform_media_disk_free_bytes", disk_free)
    yield _line("platform_media_disk_size_bytes", disk_size)
    yield _line("platform_backup_last_success_timestamp_seconds", successful_backup)
    yield _line("platform_backup_last_failure_timestamp_seconds", failed_backup)


def metrics_response(request: HttpRequest) -> HttpResponse:
    token = getattr(settings, "METRICS_TOKEN", "")
    if token and request.headers.get("X-Metrics-Token") != token:
        return HttpResponse(status=403)
    return HttpResponse(
        "".join(metrics_payload()),
        content_type="text/plain; version=0.0.4; charset=utf-8",
    )
