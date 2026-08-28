from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.organizations.models import CompanyMembership
from apps.tenancy.models import Company, LegalAcceptance, LegalDocumentType
from apps.tenancy.services import normalize_company_code

STAGING_METADATA = {
    "source": "pilot-acceptance-drive",
    "attestation": "staging-recorded",
    "staging": True,
}


class Command(BaseCommand):
    help = (
        "Record the four required legal acceptances for every active participant of a pilot company. "
        "This records a STAGING ATTESTATION (automated system record); it is not a human/legal sign-off."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--company", default="pilotco", help="Company code (default: pilotco).")
        parser.add_argument("--doc-version", default="v1", help="Document version to record (default: v1).")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-write metadata and version on existing acceptance records.",
        )

    def handle(self, *args, **options) -> None:
        code = normalize_company_code(options["company"])
        version = options["doc_version"]
        company = Company.objects.filter(code=code).first()
        if company is None:
            raise CommandError(f"Company '{code}' does not exist.")

        memberships = CompanyMembership.objects.filter(company=company, active=True).select_related("user")
        required = list(LegalDocumentType.values)
        created = 0
        updated = 0
        for membership in memberships:
            for document_type in required:
                defaults = {
                    "document_version": version,
                    "metadata": dict(STAGING_METADATA),
                }
                acceptance, was_created = LegalAcceptance.objects.get_or_create(
                    company=company,
                    accepted_by=membership.user,
                    document_type=document_type,
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                    continue
                if options["force"] and (
                    acceptance.document_version != version or acceptance.metadata.get("source") != "pilot-acceptance-drive"
                ):
                    acceptance.document_version = version
                    acceptance.metadata = dict(STAGING_METADATA)
                    acceptance.save(update_fields=["document_version", "metadata"])
                    updated += 1

        complete = 0
        incomplete: list[str] = []
        for membership in memberships:
            present = set(
                LegalAcceptance.objects.filter(company=company, accepted_by=membership.user).values_list(
                    "document_type", flat=True
                )
            )
            if set(required).issubset(present):
                complete += 1
            else:
                incomplete.append(membership.user.login_id)

        self.stdout.write(
            f"Company={code} participants={memberships.count()} "
            f"required_per_participant={len(required)} "
            f"acceptance_records={LegalAcceptance.objects.filter(company=company).count()} "
            f"created={created} updated={updated} complete={complete}/{memberships.count()} "
            f"incomplete={incomplete}"
        )
        if incomplete:
            raise CommandError("Some participants are missing required acceptances: " + ", ".join(incomplete))