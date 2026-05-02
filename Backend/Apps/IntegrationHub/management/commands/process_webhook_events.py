from django.core.management.base import BaseCommand, CommandError

from Backend.Apps.IntegrationHub.models import WebhookInboxEvent
from Backend.Apps.IntegrationHub.services import WebhookInboxService
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class Command(BaseCommand):
    help = "Mark Received Webhook Inbox Events As Processed."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-id", type=int, required=True)
        parser.add_argument("--workspace-id", type=int)
        parser.add_argument("--event-id", type=int, action="append", default=[])

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(id=options["tenant_id"]).first()
        if not tenant:
            raise CommandError("Tenant Not Found.")
        workspace = Workspace.objects.filter(id=options.get("workspace_id"), tenant=tenant).first() if options.get("workspace_id") else None
        context = TenantContext(tenant=tenant, workspace=workspace, source="Command")
        events = WebhookInboxEvent.objects.filter(tenant=tenant, status="Received")
        if options.get("event_id"):
            events = events.filter(id__in=options["event_id"])
        count = 0
        for event in events:
            result = WebhookInboxService.mark_processed(context, event.id)
            if result.ok:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Processed {count} Webhook Events."))