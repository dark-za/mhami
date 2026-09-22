from __future__ import annotations

import datetime
from django.core.management.base import BaseCommand, CommandError

from apps.organizations.models import Branch, JobRole
from apps.tasks.models import (
    TaskAssignmentMode,
    TaskRecurrenceType,
    TaskRiskLevel,
    TaskSchedule,
    TaskTemplate,
    TaskTemplateVersion,
)
from apps.tenancy.models import Company
from apps.ai_gateway.models import AIAnalysisCriterion


class Command(BaseCommand):
    help = "Seed operational defaults (branches, job roles, task templates, schedules, and AI criteria) for a company."

    def add_arguments(self, parser) -> None:
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
                raise CommandError("No company found. Please run organization setup first.")

        self.stdout.write(f"Seeding defaults for company '{company.name}' ({company.code})...")

        # 1. Default Branches
        branches_data = [
            {
                "name": "الفرع الرئيسي - الرياض",
                "code": "main-ruh",
                "timezone": "Asia/Riyadh",
                "operational_day_cutoff": "03:00:00",
            },
            {
                "name": "فرع جدة",
                "code": "branch-jed",
                "timezone": "Asia/Riyadh",
                "operational_day_cutoff": "03:00:00",
            },
        ]
        created_branches = []
        for b_data in branches_data:
            branch, created = Branch.objects.get_or_create(
                company=company,
                code=b_data["code"],
                defaults={
                    "name": b_data["name"],
                    "timezone": b_data["timezone"],
                    "operational_day_cutoff": b_data["operational_day_cutoff"],
                    "active": True,
                },
            )
            created_branches.append(branch)
            status_str = "created" if created else "already exists"
            self.stdout.write(f"  Branch: {branch.name} ({branch.code}) [{status_str}]")

        main_branch = created_branches[0]

        # 2. Default Job Roles
        roles_data = [
            {"name": "مشرف عمليات", "code": "ops-supervisor"},
            {"name": "أخصائي جودة وامتثال", "code": "quality-specialist"},
            {"name": "موظف ميداني", "code": "field-operator"},
        ]
        for r_data in roles_data:
            role, created = JobRole.objects.get_or_create(
                company=company,
                code=r_data["code"],
                defaults={"name": r_data["name"], "active": True},
            )
            status_str = "created" if created else "already exists"
            self.stdout.write(f"  Job Role: {role.name} ({role.code}) [{status_str}]")

        # 3. Default Task Templates & Versions
        templates_data = [
            {
                "slug": "daily-ops-check",
                "name": "فحص جودة وسلامة العمليات اليومية",
                "description": "فحص شامل لمعايير النظافة، السلامة المهنية، وجاهزية محطة العمل.",
                "assignment_mode": TaskAssignmentMode.ROLE_POOL,
                "assigned_role_code": "field-operator",
                "risk_level": TaskRiskLevel.LOW,
                "task_weight": 1,
                "instructions": "قم بتفقد منطقة العمل والتأكد من توافر أدوات السلامة والالتزام بالزي الرسمي، ثم التقط صورة للموقع وأكد صحة البيانات.",
                "evidence_requirements": [
                    {"type": "image", "label": "صورة الموقع التشغيلي"},
                    {"type": "confirmation", "label": "إقرار الالتزام بالمعايير والجاهزية"},
                ],
                "checklist": ["التحقق من نظافة الموقع", "فحص معدات السلامة", "توثيق الحالة بالصورة"],
                "scheduled_time": datetime.time(9, 0),
            },
            {
                "slug": "daily-inventory-handover",
                "name": "جرد المخزون والتسليم التشغيلي",
                "description": "تسجيل أرقام الجرد اليومي وتوثيق محضر التسليم والتسلم للمناوبة.",
                "assignment_mode": TaskAssignmentMode.ROLE_POOL,
                "assigned_role_code": "ops-supervisor",
                "risk_level": TaskRiskLevel.MEDIUM,
                "task_weight": 2,
                "instructions": "سجل إجمالي الكميات المتبقية وتأكد من مطابقة السجلات المادية مع النظام.",
                "evidence_requirements": [
                    {"type": "number", "label": "إجمالي الوحدات المستلمة"},
                    {"type": "image", "label": "صورة نموذج الاستلام الورقي"},
                    {"type": "note", "label": "ملاحظات التسليم والتسلم"},
                ],
                "checklist": ["مطابقة السجلات", "عد الوحدات الفعلية", "تدوين الفروقات إن وجدت"],
                "scheduled_time": datetime.time(17, 0),
            },
        ]

        for t_data in templates_data:
            template, created = TaskTemplate.objects.get_or_create(
                company=company,
                slug=t_data["slug"],
                defaults={
                    "branch": main_branch,
                    "name": t_data["name"],
                    "description": t_data["description"],
                    "assignment_mode": t_data["assignment_mode"],
                    "assigned_role_code": t_data["assigned_role_code"],
                    "risk_level": t_data["risk_level"],
                    "task_weight": t_data["task_weight"],
                    "active": True,
                },
            )
            status_str = "created" if created else "already exists"
            self.stdout.write(f"  Task Template: {template.name} ({template.slug}) [{status_str}]")

            version, v_created = TaskTemplateVersion.objects.get_or_create(
                template=template,
                version_number=1,
                defaults={
                    "instructions": t_data["instructions"],
                    "checklist_definition": t_data["checklist"],
                    "evidence_requirements": t_data["evidence_requirements"],
                    "risk_level": t_data["risk_level"],
                },
            )

            # Schedule
            schedule, s_created = TaskSchedule.objects.get_or_create(
                company=company,
                template=template,
                branch=main_branch,
                recurrence_type=TaskRecurrenceType.DAILY_FIXED,
                scheduled_time=t_data["scheduled_time"],
                defaults={"active": True},
            )
            s_status = "created" if s_created else "already exists"
            self.stdout.write(f"    Schedule: Daily at {t_data['scheduled_time']} [{s_status}]")

        # 4. Default AI Criteria
        criteria, c_created = AIAnalysisCriterion.objects.get_or_create(
            company=company,
            version_number=1,
            defaults={
                "title": "معايير فحص وتدقيق الأدلة الافتراضية",
                "criteria_json": {
                    "risk_threshold": 70,
                    "description": "فحص الأدلة والتحقق من سلامة المرفقات وجودتها في وضع الظل (Shadow Mode).",
                },
                "shadow_mode": True,
                "auto_pass_enabled": False,
                "auto_pass_risk_threshold": 70,
                "created_by": company.owner,
                "active": True,
            },
        )
        c_status = "created" if c_created else "already exists"
        self.stdout.write(f"  AI Criteria: {criteria.title} (v{criteria.version_number}) [{c_status}]")

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded company defaults for '{company.name}'."))
