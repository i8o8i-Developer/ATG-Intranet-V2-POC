from django.test import TestCase

from Backend.Apps.LegacyBridge.models import LegacyApplicationMap, LegacyModelCrosswalk, MigrationRun
from Backend.Apps.LegacyBridge.services import LegacyMappingService, LegacyMigrationService
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class LegacyBridgeTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Bridge Tenant", slug="bridge-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="bridge-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Platform", code="BR")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Bridge", code="BR")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace)

    def test_mapping_migration_and_rollback(self):
        seeded = LegacyMappingService.seed_default_app_map(self.context)
        self.assertGreater(seeded.data["count"], 0)
        self.assertTrue(LegacyApplicationMap.objects.filter(tenant=self.tenant, legacy_app_label="l3").exists())
        started = LegacyMigrationService.start_run(self.context, "l3", total_rows=1)
        self.assertEqual(started.data.status, "Running")
        crosswalk = LegacyMigrationService.record_crosswalk(self.context, {"legacy_app_label": "l3", "legacy_model_name": "CollegeData", "legacy_object_id": "1", "backend_model_name": "CollegePipelineRecord", "backend_object_id": "10", "migration_batch_id": started.data.batch_id})
        self.assertTrue(crosswalk.ok)
        completed = LegacyMigrationService.complete_run(self.context, started.data.id, migrated_rows=1)
        self.assertEqual(completed.data.status, "Completed")
        rolled = LegacyMigrationService.rollback_run(self.context, started.data.id)
        self.assertEqual(rolled.data["rolledBackCrosswalks"], 1)
        self.assertEqual(MigrationRun.objects.get(id=started.data.id).status, "RolledBack")
        self.assertFalse(LegacyModelCrosswalk.objects.get(id=crosswalk.data.id).is_active)