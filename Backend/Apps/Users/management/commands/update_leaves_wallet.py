from django.core.management.base import BaseCommand

from Backend.Apps.Users.services import LeaveWalletService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Updates Leave Wallet For All Active Users."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--amount", type=float)

    def handle(self, *args, **options):
        tenant = Tenant.objects.get(id=options["tenant_id"])
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = LeaveWalletService.update_all_wallets(TenantContext(tenant=tenant, workspace=workspace, source="Command"), amount=options.get("amount"))
        self.stdout.write(self.style.SUCCESS(f"Created {result.data['count']} Leave Wallet Transactions."))
