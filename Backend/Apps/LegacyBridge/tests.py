from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from Backend.Apps.LegacyBridge.models import LegacyApplicationMap, LegacyModelCrosswalk, MigrationRun
from Backend.Apps.LegacyBridge.services import LegacyMappingService, LegacyMigrationService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class LegacyBridgeTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Bridge Tenant", slug="bridge-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="bridge-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Platform", code="BR")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Bridge", code="BR")
        self.user = get_user_model().objects.create_user(username="bridge-user", email="bridge@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="BR-1", display_name="Bridge User")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.client = APIClient()

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

    def test_legacy_bridge_routes(self):
        self.client.force_authenticate(self.user)

        preview = self.client.get("/LegacyBridge/api/application-maps/preview-defaults/")
        self.assertEqual(preview.status_code, 200)

        seeded = self.client.post("/LegacyBridge/api/application-maps/seed-defaults/", {}, format="json")
        self.assertEqual(seeded.status_code, 200)
        self.assertTrue(LegacyApplicationMap.objects.filter(tenant=self.tenant, legacy_app_label="l3").exists())

        started = self.client.post(
            "/LegacyBridge/api/migration-runs/start/",
            {"source_app_label": "l3", "total_rows": 1},
            format="json",
        )
        self.assertEqual(started.status_code, 201)
        run_id = started.data["id"]
        batch_id = started.data["batch_id"]

        recorded = self.client.post(
            "/LegacyBridge/api/crosswalks/record/",
            {
                "legacy_app_label": "l3",
                "legacy_model_name": "CollegeData",
                "legacy_object_id": "1",
                "backend_model_name": "CollegePipelineRecord",
                "backend_object_id": "10",
                "migration_batch_id": batch_id,
            },
            format="json",
        )
        self.assertEqual(recorded.status_code, 201)

        completed = self.client.post(f"/LegacyBridge/api/migration-runs/{run_id}/complete/", {"migrated_rows": 1}, format="json")
        self.assertEqual(completed.status_code, 200)

        failed = self.client.post(f"/LegacyBridge/api/migration-runs/{run_id}/fail/", {"failure_reason": "manual"}, format="json")
        self.assertEqual(failed.status_code, 200)

        rolled = self.client.post(f"/LegacyBridge/api/migration-runs/{run_id}/rollback/", {}, format="json")
        self.assertEqual(rolled.status_code, 200)
        self.assertIn("rolledBackCrosswalks", rolled.data)