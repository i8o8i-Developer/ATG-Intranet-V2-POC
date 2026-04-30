from django.core.management.base import BaseCommand

from Backend.Apps.Users.services import EmployeeLifecycleService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Assign all existing department skills to active users."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)

    def handle(self, *args, **options):
        tenant = Tenant.objects.get(id=options["tenant_id"])
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = EmployeeLifecycleService.assign_all_department_skills(TenantContext(tenant=tenant, workspace=workspace, source="Command"))
        self.stdout.write(self.style.SUCCESS(f"Processed {result.data['count']} active employees."))
