from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Apply database migrations, collect static files, and run strict runtime checks."

    def handle(self, *args, **options):
        call_command("check", deploy=True)
        call_command("migrate", interactive=False)
        call_command("collectstatic", interactive=False, verbosity=0)
        call_command("doctor", strict=True)
        self.stdout.write(self.style.SUCCESS("Mhami upgrade completed."))
