from __future__ import annotations

from celery import shared_task

from .services import mark_overdue_tasks, schedule_due_tasks


@shared_task(name="apps.tasks.run_scheduler")
def run_scheduler_task() -> int:
    return len(schedule_due_tasks())


@shared_task(name="apps.tasks.mark_overdue")
def mark_overdue_task() -> int:
    return len(mark_overdue_tasks())
