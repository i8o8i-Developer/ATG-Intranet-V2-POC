from django.contrib.auth import get_user_model
from django.test import TestCase

from Backend.Apps.GithubExtension.models import BranchTestingAssignment, GitHubRepository
from Backend.Apps.GithubExtension.services import GitHubBranchService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class GithubExtensionTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Github Tenant", slug="github-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="github-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Engineering", code="GH")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Github", code="GH")
        self.user = get_user_model().objects.create_user(username="github-user", email="github@example.com")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="GH-1", display_name="Github User")
        self.repository = GitHubRepository.objects.create(tenant=self.tenant, workspace=self.workspace, owner="atgworld", name="intranet", default_branch="master")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)

    def test_branch_tester_reviewer_status_flow(self):
        tester = GitHubBranchService.create_branch_assignment(self.context, repository_id=self.repository.id, branch_name="feature", user_type="tester", employee_id=self.employee.id, data={"comment": "queued"})
        self.assertTrue(tester.ok)
        self.assertTrue(BranchTestingAssignment.objects.filter(branch_name="feature").exists())

        updated = GitHubBranchService.update_branch_assignment(self.context, "tester", tester.data.id, {"is_pass": "pass", "comment": "ok"})
        self.assertTrue(updated.ok)
        self.assertEqual(updated.data.status, "Tested")

        reviewer = GitHubBranchService.create_branch_assignment(self.context, repository_id=self.repository.id, branch_name="feature", user_type="reviewer", employee_id=self.employee.id, data={"is_pass": "partial_pass"})
        self.assertTrue(reviewer.ok)

        listed = GitHubBranchService.list_branch_status(self.context, "atgworld_intranet", ["feature"])
        self.assertTrue(listed.ok)
        self.assertEqual(listed.data[0]["testing_status"], "pass")

        checked = GitHubBranchService.check_repository(self.context, "atgworld_intranet")
        self.assertTrue(checked.data["exists"])