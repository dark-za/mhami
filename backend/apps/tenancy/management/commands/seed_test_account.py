from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.identity.models import User
from apps.organizations.models import Branch, CompanyMembership, JobRole, UserBranchMembership
from apps.tenancy.models import Company


class Command(BaseCommand):
    help = "Seed or update a designated test account (e.g. TEST-ahmed) for end-to-end QA and user testing."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--login-id", default="TEST-ahmed", help="Login ID for the test user.")
        parser.add_argument("--display-name", default="أحمد العتيبي (حساب اختباري)", help="Display name.")
        parser.add_argument("--password", default="Test!Password-2026", help="Password for the test user.")
        parser.add_argument(
            "--role",
            choices=["employee", "monitor", "owner"],
            default="employee",
            help="Company role for the test user.",
        )
        parser.add_argument("--company-code", help="Target company code (defaults to the first existing company).")

    def handle(self, *args, **options) -> None:
        company_code = options.get("company_code")
        if company_code:
            company = Company.objects.filter(code=company_code).first()
            if not company:
                raise CommandError(f"Company with code {company_code!r} does not exist.")
        else:
            company = Company.objects.first()
            if not company:
                raise CommandError("No company found. Please run setup or provision_owner first.")

        login_id = str(options["login_id"]).strip()
        display_name = str(options["display_name"]).strip()
        password = str(options["password"])
        role_str = options["role"]

        user, created = User.objects.get_or_create(
            login_id=login_id,
            defaults={"display_name": display_name, "is_active": True},
        )
        user.display_name = display_name
        user.is_active = True
        user.set_password(password)
        user.save()

        # Ensure company membership
        CompanyMembership.objects.update_or_create(
            company=company,
            user=user,
            defaults={"role": role_str, "active": True},
        )

        # Ensure at least one branch and job role for the user
        branch = Branch.objects.filter(company=company, active=True).first()
        if not branch:
            branch = Branch.objects.create(
                company=company,
                name="الفرع الرئيسي",
                code="main",
                timezone="Asia/Riyadh",
                operational_day_cutoff="03:00:00",
                active=True,
            )

        job_role = JobRole.objects.filter(company=company, active=True).first()
        if not job_role:
            job_role = JobRole.objects.create(
                company=company,
                name="أخصائي عمليات",
                code="ops-specialist",
                active=True,
            )

        UserBranchMembership.objects.update_or_create(
            company=company,
            user=user,
            defaults={
                "branch": branch,
                "job_role": job_role,
                "membership_type": "primary",
                "active": True,
            },
        )

        action_word = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action_word} test account {login_id!r} with role {role_str!r} in company {company.name!r} ({company.code}).\n"
                f"Credentials:\n"
                f"  Company code: {company.code}\n"
                f"  Login ID:     {login_id}\n"
                f"  Password:     {password}\n"
                f"  Branch:       {branch.name} ({branch.code})\n"
                f"  Job Role:     {job_role.name}"
            )
        )

