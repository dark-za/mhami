from __future__ import annotations

import getpass

from django.core.management.base import BaseCommand, CommandError

from apps.identity.models import User


class Command(BaseCommand):
    help = "Create or promote the first platform administrator."

    def add_arguments(self, parser):
        parser.add_argument("--login-id", required=True)
        parser.add_argument("--display-name", default="")
        parser.add_argument("--password")

    def handle(self, *args, **options):
        login_id = options["login_id"].strip()
        if not login_id:
            raise CommandError("--login-id cannot be empty.")
        password = options["password"] or getpass.getpass("Admin password: ")
        if len(password) < 12:
            raise CommandError("Admin password must be at least 12 characters.")
        user, created = User.objects.get_or_create(
            login_id=login_id,
            defaults={"display_name": options["display_name"].strip()},
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if options["display_name"].strip():
            user.display_name = options["display_name"].strip()
        if created or not user.has_usable_password():
            user.set_password(password)
        user.save(update_fields=["is_staff", "is_superuser", "is_active", "display_name", "password", "updated_at"])
        action = "created" if created else "promoted"
        self.stdout.write(self.style.SUCCESS(f"Administrator {action}: {login_id}"))
