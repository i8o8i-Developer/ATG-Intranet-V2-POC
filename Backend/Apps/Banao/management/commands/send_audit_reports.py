from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.Banao.models import LeadAccount
from Backend.Apps.Banao.services import LeadWorkflowService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Queue Banao Audit Reports For Leads."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--lead-id", type=int)

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant Not Found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        context = TenantContext(tenant=tenant, workspace=workspace, source="Command")
        leads = LeadAccount.objects.filter(tenant=tenant)
        if options.get("lead_id"):
            leads = leads.filter(id=options["lead_id"])
        count = 0
        for lead in leads:
            result = LeadWorkflowService.send_audit(context, lead.id)
            if result.ok:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Queued {count} Audit Reports."))
