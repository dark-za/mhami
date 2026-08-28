"""Seed a load-test user pool for the k6 scenarios.

The command creates one company per role and ``--per-role`` users per
company. The default password is ``P@ssw0rd!`` so the k6 scenarios
can authenticate without per-user provisioning.

Usage::

    python manage.py make_load_users --per-role 50
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.identity.models import User
from apps.organizations.models import CompanyMembership, CompanyRole
from apps.tenancy.models import Company, CompanyStatus


ROLE_COMPANY_MAP = {
    CompanyRole.OWNER: "load-owner",
    CompanyRole.MONITOR: "load-monitor",
    CompanyRole.EMPLOYEE: "load-employee",
}


class Command(BaseCommand):
    help = "Create a pool of users + companies for k6 load tests."

    def add_arguments(self, parser):
        parser.add_argument("--per-role", type=int, default=50)

    @transaction.atomic
    def handle(self, *args, **opts):
        per_role = opts["per_role"]
        for role, code in ROLE_COMPANY_MAP.items():
            company, _ = Company.objects.get_or_create(
                code=code,
                defaults={
                    "name": f"Load {role.label}",
                    "status": CompanyStatus.ACTIVE,
                    "trial_ends_at": "2030-01-01T00:00:00Z",
                },
            )
            for i in range(per_role):
                login_id = f"{code}-{i}"
                user, created = User.objects.get_or_create(
                    login_id=login_id,
                    defaults={
                        "display_name": f"Load {role.label} {i}",
                    },
                )
                if created:
                    user.set_password("P@ssw0rd!")
                    user.save(update_fields=["password"])
                CompanyMembership.objects.get_or_create(
                    company=company,
                    user=user,
                    defaults={"role": role, "active": True},
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Load users ready: {per_role} per role across {len(ROLE_COMPANY_MAP)} companies."
            )
        )
