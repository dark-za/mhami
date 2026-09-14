from __future__ import annotations

import getpass

from django.core.management.base import BaseCommand, CommandError

from apps.tenancy.services import provision_initial_owner


class Command(BaseCommand):
    help = (
        "Provision the sole organization/company and first owner. "
        "Fails safely if any organization already exists. "
        "This is the one-time self-hosted first-install command."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--organization-name", required=True, help="Display name for the sole organization.")
        parser.add_argument("--owner-login-id", required=True, help="Login ID for the owner user.")
        parser.add_argument("--owner-display-name", required=True, help="Display name for the owner user.")
        parser.add_argument(
            "--password",
            help="Password for the owner user (min 12 chars). Prefer the interactive prompt so it is not stored in shell history.",
        )

    def handle(self, *args, **options) -> None:
        org_name = str(options.get("organization_name") or "")
        owner_login_id = str(options.get("owner_login_id") or "")
        owner_display_name = str(options.get("owner_display_name") or "")
        password = options.get("password") or getpass.getpass("Owner password: ")

        try:
            company, owner = provision_initial_owner(
                organization_name=org_name,
                owner_login_id=owner_login_id,
                owner_display_name=owner_display_name,
                password=password,
                initiated_via="command_line",
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Provisioned organization {company.name!r} ({company.code}) with owner {owner.login_id!r}"))
