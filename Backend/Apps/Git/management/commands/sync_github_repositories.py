from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.Git.services import GitRepositoryService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Sync GitHub Repositories Into Git And GithubExtension Read Models."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--live", action="store_true")

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant Not Found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        result = GitRepositoryService.sync_github_repositories(TenantContext(tenant=tenant, workspace=workspace, source="Command"), live=options["live"])
        if not result.ok:
            raise CommandError(result.errors)
        self.stdout.write(self.style.SUCCESS(f"Synced {result.data['count']} GitHub Repositories."))