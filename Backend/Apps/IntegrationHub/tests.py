from django.contrib.auth import get_user_model
from django.test import TestCase

from Backend.Apps.IntegrationHub.models import IntegrationConnection, IntegrationProvider, IntegrationSyncJob, WebhookInboxEvent
from Backend.Apps.IntegrationHub.services import IntegrationJobService, WebhookInboxService
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class IntegrationHubTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Integration Tenant", slug="integration-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="integration-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Platform", code="INT")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Integration", code="INT")
        self.user = get_user_model().objects.create_user(username="integration-user", email="integration@example.com")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.provider = IntegrationProvider.objects.create(tenant=self.tenant, workspace=self.workspace, name="GitHub", provider_type="GitHub", base_url="https://api.github.com")
        self.connection = IntegrationConnection.objects.create(tenant=self.tenant, workspace=self.workspace, provider=self.provider, owner_module="Git", name="GitHub Main")

    def test_sync_job_and_webhook_lifecycle(self):
        queued = IntegrationJobService.queue_sync(self.context, self.connection, "RepositorySync")
        self.assertTrue(queued.ok)
        started = IntegrationJobService.start_job(self.context, queued.data.id)
        self.assertEqual(started.data.status, "Running")
        completed = IntegrationJobService.complete_job(self.context, queued.data.id, {"synced": 1})
        self.assertEqual(completed.data.status, "Completed")

        failed = IntegrationSyncJob.objects.create(tenant=self.tenant, workspace=self.workspace, connection=self.connection, job_type="RetryMe", status="Failed")
        retry = IntegrationJobService.retry_failed_jobs(self.context, connection=self.connection)
        self.assertTrue(retry.ok)
        self.assertGreaterEqual(retry.data["count"], 1)
        self.assertTrue(IntegrationSyncJob.objects.filter(result_payload__retryOf=failed.id).exists())

        received = WebhookInboxService.receive(self.context, provider_id=self.provider.id, event_type="push", external_event_id="evt-1", payload={"ok": True})
        self.assertTrue(received.ok)
        processed = WebhookInboxService.mark_processed(self.context, received.data.id)
        self.assertEqual(processed.data.status, "Processed")
        self.assertTrue(WebhookInboxEvent.objects.filter(event_type="push", processed_at__isnull=False).exists())