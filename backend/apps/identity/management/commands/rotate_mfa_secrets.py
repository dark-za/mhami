from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.identity.models import MfaEnrollment


class Command(BaseCommand):
    help = "Encrypt legacy MFA secrets and rotate encrypted secrets to the active key."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        enrollments = MfaEnrollment.objects.exclude(secret="").only("id", "secret")
        count = enrollments.count()
        if options["dry_run"]:
            self.stdout.write(f"Would rotate {count} MFA secret(s).")
            return

        with transaction.atomic():
            for enrollment in enrollments.iterator():
                enrollment.updated_at = timezone.now()
                enrollment.save(update_fields=["secret", "updated_at"])
        self.stdout.write(self.style.SUCCESS(f"Rotated {count} MFA secret(s)."))
