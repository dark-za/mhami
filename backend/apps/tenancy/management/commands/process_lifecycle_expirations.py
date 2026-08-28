from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware

from apps.tenancy.services import process_lifecycle_expirations


class Command(BaseCommand):
    help = "Move expired trials and read-only tenants through their lifecycle and revoke expired support grants."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--at", help="Process expirations due at this ISO-8601 timestamp.")
        parser.add_argument("--dry-run", action="store_true", help="Report due records without changing them.")

    def handle(self, *args, **options) -> None:
        at = None
        if options["at"]:
            at = parse_datetime(options["at"])
            if at is None:
                raise CommandError("--at must be an ISO-8601 datetime.")
            if not is_aware(at):
                at = make_aware(at)
        result = process_lifecycle_expirations(at=at, dry_run=options["dry_run"])
        self.stdout.write(
            "read_only={read_only} pending_deletion={pending_deletion} support_expired={support_expired}".format(
                **result
            )
        )
