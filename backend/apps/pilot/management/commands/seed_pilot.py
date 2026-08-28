from __future__ import annotations

from datetime import time, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.identity.models import User
from apps.audit.services import record_audit_event
from apps.organizations.models import (
    Branch,
    CompanyMembership,
    CompanyRole,
    JobRole,
    UserBranchMembership,
    WeeklyShift,
)
from apps.tenancy.models import Company, CompanyStatus, IndustryChoice, LegalAcceptance, LegalDocumentType
from apps.tenancy.services import normalize_company_code
from apps.tasks.models import TaskAssignmentMode, TaskRiskLevel, TaskTemplate, TaskTemplateVersion
from apps.pilot.services import pilot_program_for_company

DEFAULT_PASSWORD = "PilotPass!2026"

REFERENCE_TEMPLATES = [
    {
        "slug": "shift-cash-handover",
        "name": "Shift Cash Handover",
        "description": (
            "Closing-shift cash handover documenting till and cash drawer counts with seal evidence. "
            "Explicitly excludes accounting reconciliation (finance is out of pilot scope)."
        ),
        "risk_level": TaskRiskLevel.MEDIUM,
        "task_weight": 3,
        "assignment_mode": TaskAssignmentMode.ROLE_POOL,
        "assigned_role_code": "staff",
        "instructions": (
            "Count the till and cash drawer, record the total, place cash in the seal bag, and record the "
            "seal number. Photograph the till and the sealed bag, then confirm the seal matches the drawer log."
        ),
        "checklist_definition": [
            {"step": "count_till", "label": "Count till and record total"},
            {"step": "seal_bag", "label": "Seal cash bag and record seal number"},
            {"step": "log_drawer", "label": "Confirm drawer log entry"},
            {"step": "handover_note", "label": "Leave handover note for next shift"},
        ],
        "evidence_requirements": [
            {"type": "image", "min": 2, "max": 4, "reference_media": True},
            {"type": "number", "required": True, "step": "count_till"},
            {"type": "confirmation", "required": True, "step": "seal_bag", "random_challenge": True},
        ],
        "reference_instructions": "Golden example: sealed cash bag with legible seal number and drawer log visible.",
    },
    {
        "slug": "cleanliness-preparation-inspection",
        "name": "Critical Cleanliness and Preparation-Area Inspection",
        "description": (
            "Mid-day and pre-service inspection of food-prep surfaces, sanitizer levels, and storage. "
            "High risk; larger image set with reference media and mandatory monitor confirmation on failure."
        ),
        "risk_level": TaskRiskLevel.HIGH,
        "task_weight": 5,
        "assignment_mode": TaskAssignmentMode.ROLE_POOL,
        "assigned_role_code": "staff",
        "instructions": (
            "Inspect all food-prep surfaces, verify sanitizer concentration and storage temperature, and "
            "photograph each area. Any failure requires monitor confirmation before the task can close."
        ),
        "checklist_definition": [
            {"step": "surfaces", "label": "Inspect and clean all food-prep surfaces"},
            {"step": "sanitizer", "label": "Verify sanitizer concentration within range"},
            {"step": "storage", "label": "Check storage temperature and labels"},
            {"step": "failures", "label": "Photograph any failure and flag for monitor confirmation"},
        ],
        "evidence_requirements": [
            {"type": "image", "min": 4, "max": 8, "reference_media": True},
            {"type": "number", "required": True, "step": "sanitizer"},
            {"type": "confirmation", "required": True, "step": "failures", "random_challenge": True},
            {"type": "note", "required": True, "step": "failures", "monitor_confirmation_required": True},
        ],
        "reference_instructions": "Golden example: sanitizer test strip in range next to dated prep log.",
    },
    {
        "slug": "shift-close-handover",
        "name": "Shift Close and Handover",
        "description": (
            "End-of-shift closeout capturing station cleanliness, equipment-off evidence, and open-task "
            "handover notes to the next shift lead. Includes a transfer scenario for unresolved tasks."
        ),
        "risk_level": TaskRiskLevel.MEDIUM,
        "task_weight": 4,
        "assignment_mode": TaskAssignmentMode.ROLE_POOL,
        "assigned_role_code": "staff",
        "instructions": (
            "Close the station, confirm equipment is off, photograph the closed station, and record open-task "
            "handover notes. Unresolved tasks transfer to the next shift lead for completion."
        ),
        "checklist_definition": [
            {"step": "station_close", "label": "Clean and close station"},
            {"step": "equipment_off", "label": "Confirm equipment is powered off"},
            {"step": "handover_notes", "label": "Record open-task handover notes"},
            {"step": "transfer", "label": "Transfer unresolved tasks to next shift lead"},
        ],
        "evidence_requirements": [
            {"type": "image", "min": 3, "max": 6, "reference_media": True},
            {"type": "note", "required": True, "step": "handover_notes", "transfer_scenario": True},
            {"type": "confirmation", "required": True, "step": "equipment_off"},
        ],
        "reference_instructions": "Golden example: station closed, equipment lights off, handover note visible.",
    },
]

ACTIVITY_PROTECTION_MODELS = (
    ("tasks", "taskinstance"),
    ("evidence", "evidenceitem"),
    ("evidence", "capturesession"),
    ("evidence", "taskissuereport"),
    ("reviews", "reviewdecision"),
    ("ai_gateway", "aianalysisrun"),
    ("exports", "exportrequest"),
    ("backups", "backuprun"),
    ("backups", "restorerun"),
)


class Command(BaseCommand):
    help = "Create or update an internal pilot company, branches, roles, users, shifts, templates, and pilot program."

    def add_arguments(self, parser):
        parser.add_argument("--company", default="pilotco", help="Company code (default: pilotco).")
        parser.add_argument("--name", default="Pilot Coffee Co", help="Company display name.")
        parser.add_argument("--branches", type=int, default=3, help="Number of branches (default: 3).")
        parser.add_argument("--employees-per-branch", type=int, default=10, help="Employees per branch (default: 10).")
        parser.add_argument("--chrome-devices", type=int, default=0, help="Chrome device count (default: branches * 2).")
        parser.add_argument("--trial-days", type=int, default=60, help="Trial length in days (default: 60).")
        parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Shared account password for seeded users.")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the company (and its users) if it already exists before reseeding.",
        )
        parser.add_argument(
            "--charter",
            action="store_true",
            help="PILOT-01: also sign an authorize-charter for the seeded program.",
        )
        parser.add_argument(
            "--charter-rationale",
            default="Pilot seeded in staging-equivalent environment; charter signed to enable Phase 12 evidence collection.",
            help="PILOT-01: rationale for the signed charter.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        code = normalize_company_code(options["company"])
        password = options["password"] or DEFAULT_PASSWORD
        branches_count = options["branches"]
        employees_per_branch = options["employees_per_branch"]
        chrome_devices = options["chrome_devices"] or branches_count * 2
        name = options["name"]

        existing = Company.objects.filter(code=code).first()
        if existing:
            if not options["reset"]:
                raise CommandError(f"Company '{code}' already exists. Use --reset to recreate it.")
            self._reset_company(existing)
            self.stdout.write(self.style.WARNING(f"Removed existing company '{code}'."))

        owner = User.objects.create_user(login_id=f"{code}-owner", password=password, display_name="Pilot Owner")
        company = Company.objects.create(
            name=name,
            code=code,
            industry=IndustryChoice.RESTAURANTS_CAFES,
            owner=owner,
            contact_email=f"{code}@example.test",
            contact_phone="+966500000000",
            status=CompanyStatus.TRIAL,
            trial_ends_at=timezone.now() + timedelta(days=options["trial_days"]),
        )
        CompanyMembership.objects.create(company=company, user=owner, role=CompanyRole.OWNER)
        for document_type in (
            LegalDocumentType.TERMS,
            LegalDocumentType.PRIVACY,
            LegalDocumentType.AI_TRANSFER,
            LegalDocumentType.EMPLOYEE_PRIVACY,
        ):
            LegalAcceptance.objects.create(company=company, accepted_by=owner, document_type=document_type, document_version="v1")

        staff_role = JobRole.objects.create(company=company, name="Shift Staff", code="staff")
        monitor_role = JobRole.objects.create(company=company, name="Quality Monitor", code="monitor")

        branches: list[Branch] = []
        for index in range(branches_count):
            branch = Branch.objects.create(
                company=company,
                name=f"Branch {index + 1}",
                code=f"{code}-b{index + 1}",
                timezone="Asia/Riyadh",
                operational_day_cutoff=time(6, 0),
            )
            branches.append(branch)

        monitors = self._create_monitors(company, monitor_role, branches, password)
        employees = self._create_employees(company, staff_role, branches, employees_per_branch, password)
        self._seed_templates(company, branches)

        program = pilot_program_for_company(company)
        program.status = "active"
        program.branch_count_target = branches_count
        program.employee_count_target = branches_count * employees_per_branch
        program.chrome_device_count = chrome_devices
        program.ai_provider_name = "staging-openai"
        program.connector_owner = f"{code}-owner"
        program.test_environment = "staging-equivalent"
        program.success_measures = [
            "Employees complete Chrome-only tasks",
            "Monitors resolve exceptions without engineering intervention",
            "Owners see weekly branch and quality trends",
        ]
        program.weekly_metrics_goal = {"branches": branches_count, "employees": branches_count * employees_per_branch}
        program.save()

        charter_signed = False
        if options["charter"]:
            from apps.pilot.services import sign_charter

            observation_start = timezone.now().date()
            observation_end = observation_start + timedelta(days=options["trial_days"])
            charter = sign_charter(
                company=company,
                user=owner,
                payload={
                    "decision": "authorize",
                    "rationale": options["charter_rationale"],
                    "conditions": "",
                    "observation_start": observation_start,
                    "observation_end": observation_end,
                    "success_measures": program.success_measures,
                    "metadata": {"seeded_by": "seed_pilot --charter"},
                },
            )
            record_audit_event(
                event_type="PILOT_CHARTER_SIGNED",
                target_type="pilot_charter",
                target_id=str(charter.id),
                actor_id=str(owner.id),
                branch_id="",
                metadata={"pilot_program_id": str(program.id), "decision": charter.decision, "via": "seed_pilot --charter"},
            )
            charter_signed = True

        self.stdout.write(
            self.style.SUCCESS(
                f"Pilot seeded: company='{code}' ({name}), {branches_count} branches, "
                f"{len(monitors)} monitors, {len(employees)} employees, "
                f"owner='{code}-owner' / monitors / employees password='{password}', "
                f"templates={len(REFERENCE_TEMPLATES)}, charter_signed={charter_signed}."
            )
        )

    def _reset_company(self, company: Company) -> None:
        protected: list[str] = []
        apps = type(company)._meta.apps
        for app_label, model_name in ACTIVITY_PROTECTION_MODELS:
            model = apps.get_model(app_label, model_name)
            if model.objects.filter(company=company).exists():
                protected.append(f"{app_label}.{model_name}")
        program = pilot_program_for_company(company)
        for model_name in ("pilotweeklyreport", "pilotissue", "pilotchangerequest"):
            model = apps.get_model("pilot", model_name)
            if model.objects.filter(pilot_program=program).exists():
                protected.append(f"pilot.{model_name}")
        if protected:
            raise CommandError(
                f"Company '{company.code}' has protected operational records ({', '.join(protected)}); "
                "reset refused. Create the pilot on a fresh company code instead."
            )
        user_ids = list(company.memberships.values_list("user_id", flat=True))
        CompanyMembership.objects.filter(company=company).delete()
        UserBranchMembership.objects.filter(company=company).delete()
        WeeklyShift.objects.filter(company=company).delete()
        Branch.objects.filter(company=company).delete()
        JobRole.objects.filter(company=company).delete()
        TaskTemplate.objects.filter(company=company).delete()
        company.delete()
        User.objects.filter(id__in=user_ids).delete()

    def _seed_templates(self, company: Company, branches: list[Branch]) -> None:
        for definition in REFERENCE_TEMPLATES:
            template, _created = TaskTemplate.objects.get_or_create(
                company=company,
                slug=definition["slug"],
                defaults={
                    "name": definition["name"],
                    "description": definition["description"],
                    "assignment_mode": definition["assignment_mode"],
                    "assigned_role_code": definition["assigned_role_code"],
                    "risk_level": definition["risk_level"],
                    "task_weight": definition["task_weight"],
                    "branch": branches[0],
                },
            )
            if template.versions.exists():
                continue
            TaskTemplateVersion.objects.create(
                template=template,
                version_number=1,
                instructions=definition["instructions"],
                checklist_definition=definition["checklist_definition"],
                evidence_requirements=definition["evidence_requirements"],
                reference_instructions=definition["reference_instructions"],
                risk_level=definition["risk_level"],
            )

    def _create_monitors(self, company: Company, monitor_role: JobRole, branches: list[Branch], password: str) -> list[User]:
        monitors: list[User] = []
        for index in range(2):
            login_id = f"{company.code}-monitor{index + 1}"
            user = User.objects.create_user(login_id=login_id, password=password, display_name=f"Monitor {index + 1}")
            CompanyMembership.objects.create(company=company, user=user, role=CompanyRole.MONITOR)
            branch = branches[index % len(branches)]
            UserBranchMembership.objects.create(
                company=company,
                user=user,
                branch=branch,
                job_role=monitor_role,
            )
            monitors.append(user)
        return monitors

    def _create_employees(
        self,
        company: Company,
        staff_role: JobRole,
        branches: list[Branch],
        per_branch: int,
        password: str,
    ) -> list[User]:
        employees: list[User] = []
        for branch_index, branch in enumerate(branches):
            for employee_index in range(per_branch):
                login_id = f"{company.code}-emp{branch_index + 1}-{employee_index + 1}"
                user = User.objects.create_user(
                    login_id=login_id,
                    password=password,
                    display_name=f"Employee {branch_index + 1}-{employee_index + 1}",
                )
                CompanyMembership.objects.create(company=company, user=user, role=CompanyRole.EMPLOYEE)
                UserBranchMembership.objects.create(
                    company=company,
                    user=user,
                    branch=branch,
                    job_role=staff_role,
                )
                for weekday in range(7):
                    WeeklyShift.objects.create(
                        company=company,
                        branch=branch,
                        user=user,
                        weekday=weekday,
                        start_time=time(9, employee_index),
                        end_time=time(17, employee_index),
                    )
                employees.append(user)
        return employees
