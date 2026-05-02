from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.FinanceAndPayroll.services import PayrollCalculationService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Calculate Payroll For An Employee."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--employee-id", type=int, required=True)
        parser.add_argument("--month", type=int)
        parser.add_argument("--year", type=int)

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant not found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = PayrollCalculationService.calculate_for_employee(
            TenantContext(tenant=tenant, workspace=workspace, source="Command"),
            options["employee_id"],
            month=options.get("month"),
            year=options.get("year"),
        )
        if not result.ok:
            raise CommandError(result.errors)
        self.stdout.write(self.style.SUCCESS(str(result.data)))
