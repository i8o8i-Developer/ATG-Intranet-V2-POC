from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from Backend.Apps.Project.models import ComplianceAssignment, DeliveryDocument, DeliveryMilestone, ProjectWorkspace, RepositoryLink, TeamAssignment
from Backend.Apps.Project.services import ProjectDeliveryService
from Backend.Apps.TasksDashboard.models import WorkItem
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class ProjectModuleTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Project Tenant", slug="project-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="project-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Delivery", code="PROJ")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Project", code="PROJ")
        self.user = get_user_model().objects.create_user(username="project-user", email="project@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="PROJ-1", display_name="Project User")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.project = ProjectWorkspace.objects.create(tenant=self.tenant, workspace=self.workspace, name="ERP", code="ERP", project_type="Build", terms_required=True, anti_phishing_enabled=True)
        self.client = APIClient()

    def test_project_delivery_repo_document_and_compliance_flow(self):
        milestones = ProjectDeliveryService.create_default_checkpoints(self.context, self.project.id)
        self.assertGreater(milestones.data["count"], 0)
        milestone = DeliveryMilestone.objects.filter(project=self.project).first()
        milestone.due_on = timezone.localdate() - timezone.timedelta(days=1)
        milestone.save(update_fields=["due_on"])
        health = ProjectDeliveryService.calculate_health(self.context, self.project.id)
        self.assertEqual(health.data["health"], "Escalated")
        member = ProjectDeliveryService.add_team_member(self.context, self.project.id, self.employee.id, role="Developer")
        self.assertTrue(TeamAssignment.objects.filter(id=member.data.id).exists())
        terms = ProjectDeliveryService.accept_terms(self.context, member.data.id)
        self.assertIsNotNone(terms.data.terms_accepted_at)
        repo = ProjectDeliveryService.create_repository_link(self.context, self.project.id, "erp", owner="atgworld")
        self.assertTrue(RepositoryLink.objects.filter(id=repo.data.id).exists())
        document = ProjectDeliveryService.record_document(self.context, self.project.id, "Spec", file_id="doc-1")
        pinned = ProjectDeliveryService.pin_document(self.context, document.data.id)
        self.assertTrue(DeliveryDocument.objects.get(id=pinned.data.id).is_pinned)
        campaign = ProjectDeliveryService.launch_compliance_campaign(self.context, self.project.id)
        assignment = ComplianceAssignment.objects.get(id=campaign.data["assignmentIds"][0])
        completed = ProjectDeliveryService.complete_compliance_assignment(self.context, assignment.id, score=90)
        self.assertEqual(completed.data.status, "Completed")

    def test_project_legacy_route_surface(self):
        self.client.force_authenticate(self.user)

        onboarding = self.client.get("/Project/onboarding/")
        self.assertEqual(onboarding.status_code, 200)
        self.assertEqual(onboarding.data["count"], 1)

        member = self.client.post(
            "/Project/addMember/",
            {"project_id": self.project.id, "employee": self.employee.id, "role": "Developer"},
            format="json",
        )
        self.assertEqual(member.status_code, 201)

        terms = self.client.post(f"/Project/terms/{self.project.id}/", {"accept": True}, format="json")
        self.assertEqual(terms.status_code, 200)

        repo = self.client.post(
            "/Project/create-repo/",
            {"project_id": self.project.id, "name": "erp", "owner": "atgworld"},
            format="json",
        )
        self.assertEqual(repo.status_code, 201)
        repo_id = repo.data["id"]

        assigned = self.client.post(
            "/Project/assign-repo/",
            {"repository_id": repo_id, "employee": self.employee.id, "access_status": "AccessGranted"},
            format="json",
        )
        self.assertEqual(assigned.status_code, 200)

        git_sync = self.client.post("/Project/checkgit/", {}, format="json")
        self.assertEqual(git_sync.status_code, 200)
        self.assertEqual(git_sync.data["count"], 1)

        repo_exists = self.client.get(f"/Project/check-repo-exists/?project={self.project.id}&name=erp")
        self.assertEqual(repo_exists.status_code, 200)
        self.assertTrue(repo_exists.data["exists"])

        dashboard = self.client.get(f"/Project/dashboard/{self.project.id}/ERP/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.data["project"]["id"], self.project.id)

        clickup = self.client.post(
            "/Project/create_clickup_mapping/",
            {"project_id": self.project.id, "external_id": "space-1", "project_name": "ERP"},
            format="json",
        )
        self.assertEqual(clickup.status_code, 201)

        task = self.client.post(
            "/Project/add_task/",
            {"project_id": self.project.id, "title": "Build API", "owner": self.employee.id},
            format="json",
        )
        self.assertEqual(task.status_code, 201)
        task_id = task.data["id"]

        updated = self.client.post(
            "/Project/update-task/",
            {"task_id": task_id, "description": "Updated", "priority": "High"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)

        WorkItem.objects.filter(id=task_id).update(source_system="ClickUp", external_id="CU-1", metadata={"clickup_project": "ERP"})
        detached = self.client.post(f"/Project/remove_task/{self.project.id}", {}, format="json")
        self.assertEqual(detached.status_code, 200)
        self.assertEqual(detached.data["count"], 1)
        relinked = self.client.post(f"/Project/relink_task/{self.project.id}/ERP", {}, format="json")
        self.assertEqual(relinked.status_code, 200)
        self.assertEqual(relinked.data["count"], 1)

        link_prs = self.client.post("/Project/link/", {}, format="json")
        self.assertEqual(link_prs.status_code, 200)

        details = self.client.get(f"/Project/get/tasks/{task_id}/")
        self.assertEqual(details.status_code, 200)

        due = self.client.post(
            "/Project/update-duedate/",
            {"task_id": task_id, "due_date": timezone.now().isoformat()},
            format="json",
        )
        self.assertEqual(due.status_code, 200)

        document = self.client.post(
            "/Project/upload-project-docs/",
            {"project_id": self.project.id, "title": "Spec", "file_id": "doc-1"},
            format="json",
        )
        self.assertEqual(document.status_code, 201)
        document_id = document.data["id"]

        pinned = self.client.post(
            "/Project/toggle-pin-document/",
            {"document_id": document_id, "is_pinned": True},
            format="json",
        )
        self.assertEqual(pinned.status_code, 200)

        link = self.client.post(
            "/Project/addnewlink/",
            {"project_id": self.project.id, "title": "KT", "url": "https://example.com"},
            format="json",
        )
        self.assertEqual(link.status_code, 201)

        hat = self.client.post(
            "/Project/updateHat/",
            {"project_id": self.project.id, "memberId": self.employee.id, "hatType": "SPM"},
            format="json",
        )
        self.assertEqual(hat.status_code, 200)
        self.assertEqual(hat.data["role"], "SPM")
        removed_hat = self.client.post(
            "/Project/removeHat/",
            {"project_id": self.project.id, "memberId": self.employee.id},
            format="json",
        )
        self.assertEqual(removed_hat.status_code, 200)
        self.assertEqual(removed_hat.data["role"], "Member")

        self.project.metadata = {"milestone": {"Kickoff": "on-progress"}}
        self.project.save(update_fields=["metadata"])
        extracted = self.client.post("/Project/extract/", {"project_id": self.project.id}, format="json")
        self.assertEqual(extracted.status_code, 200)
        self.assertGreaterEqual(extracted.data["created"], 1)

        TeamAssignment.objects.filter(tenant=self.tenant, project=self.project, employee=self.employee).update(status="Removed")
        cleanup = self.client.post("/Project/cleangit/", {}, format="json")
        self.assertEqual(cleanup.status_code, 200)
        self.assertEqual(cleanup.data["revoked"], 1)

        alerts = self.client.get(f"/Project/alert_data/{self.project.id}/")
        self.assertEqual(alerts.status_code, 200)

        days_left = self.client.get(f"/Project/days_left_data/{self.project.id}/")
        self.assertEqual(days_left.status_code, 200)

        campaign = self.client.post(
            "/Project/send-anti-phishing-assessment/",
            {"project_id": self.project.id, "employee_ids": [self.employee.id]},
            format="json",
        )
        self.assertEqual(campaign.status_code, 201)
        assignment = ComplianceAssignment.objects.get(id=campaign.data["assignmentIds"][0])

        anti_get = self.client.get(f"/Project/anti-phishing-assessment/{assignment.token}/")
        self.assertEqual(anti_get.status_code, 200)

        anti_post = self.client.post(
            f"/Project/anti-phishing-assessment/{assignment.token}/",
            {"score": 88},
            format="json",
        )
        self.assertEqual(anti_post.status_code, 200)

        report = self.client.get(f"/Project/anti-phishing-reports/?project_id={self.project.id}")
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.data["count"], 1)