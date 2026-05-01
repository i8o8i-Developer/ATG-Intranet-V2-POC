from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from Backend.Apps.Git.models import GitRepositorySnapshot, RepositoryUtilityRequest
from Backend.Apps.Git.services import GitRepositoryService
from Backend.Apps.GithubExtension.models import GitHubRepository
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class FakeGitHubProvider:
    def list_repositories(self):
        return [{"organization": "atgworld", "name": "intranet", "default_branch": "master", "external_id": "606"}]

    def add_collaborator(self, organization, repository_name, github_username, permission="push", live=False):
        return {"dry_run": not live, "repository": f"{organization}/{repository_name}", "github_username": github_username}

    def remove_collaborator(self, organization, repository_name, github_username, live=False):
        return {"dry_run": not live, "repository": f"{organization}/{repository_name}", "github_username": github_username}


class GitModuleTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Git Tenant", slug="git-tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="git-org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Engineering", code="ENG")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Git", code="GIT")
        self.user = get_user_model().objects.create_user(username="git-user", email="git@example.com")
        self.superuser = get_user_model().objects.create_superuser(username="git-admin", email="git-admin@example.com", password="Password123!")
        self.employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.user, employee_code="GIT-1", display_name="Git User", github_username="gituser")
        self.super_employee = EmployeeProfile.objects.create(tenant=self.tenant, workspace=self.workspace, user=self.superuser, employee_code="GIT-2", display_name="Git Admin", github_username="gitadmin")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.client = APIClient()

    def test_sync_repository_and_collaborator_requests(self):
        synced = GitRepositoryService.sync_github_repositories(self.context, provider=FakeGitHubProvider())
        self.assertTrue(synced.ok)
        repository = GitRepositorySnapshot.objects.get(tenant=self.tenant, repository_name="intranet")
        self.assertEqual(repository.repository_full_name, "atgworld/intranet")
        self.assertTrue(GitHubRepository.objects.filter(tenant=self.tenant, owner="atgworld", name="intranet").exists())

        requested = GitRepositoryService.request_collaborator_access(self.context, employee_id=self.employee.id, repository_ids=[repository.id], provider=FakeGitHubProvider())
        self.assertTrue(requested.ok)
        self.assertTrue(RepositoryUtilityRequest.objects.filter(tenant=self.tenant, request_type="CollaboratorAccess").exists())

        deactivated = GitRepositoryService.deactivate_collaborator(self.context, employee_id=self.employee.id, repository_ids=[repository.id], provider=FakeGitHubProvider())
        self.assertTrue(deactivated.ok)
        self.assertTrue(RepositoryUtilityRequest.objects.filter(tenant=self.tenant, request_type="DeactivateCollaborator").exists())

    def test_legacy_download_requires_admin_and_uses_actor_tenant(self):
        self.client.force_authenticate(self.user)
        forbidden = self.client.get("/Git/download/")
        self.assertEqual(forbidden.status_code, 403)

        self.client.force_authenticate(self.superuser)
        with patch("Backend.Apps.Git.views.GitRepositoryService.sync_github_repositories") as sync_mock:
            sync_mock.return_value = type("Result", (), {"ok": True, "data": {"count": 1, "repositoryIds": [1], "live": False}, "status_code": 201})()
            response = self.client.get("/Git/download/")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["count"], 1)
        sync_mock.assert_called_once()