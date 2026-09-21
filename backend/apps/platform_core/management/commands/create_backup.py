from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.backups.services import create_backup_run
from apps.identity.models import User
from apps.tenancy.models import Company


class Command(BaseCommand):
    help = "Create an encrypted backup for a company using an existing owner."

    def add_arguments(self, parser):
        parser.add_argument("--company-code", required=True)
        parser.add_argument("--login-id", required=True)

    def handle(self, *args, **options):
        try:
            company = Company.objects.get(code=options["company_code"])
            user = User.objects.get(login_id=options["login_id"])
            run = create_backup_run(company=company, user=user)
        except (Company.DoesNotExist, User.DoesNotExist) as exc:
            raise CommandError("Company or user was not found.") from exc
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Backup created: {run.id}"))
