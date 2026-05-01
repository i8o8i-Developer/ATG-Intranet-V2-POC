from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from Backend.Apps.AtgDocs.models import DriveFile, KnowledgeActivity, KnowledgeDocument, KnowledgePermission
from Backend.Apps.AtgDocs.services import KnowledgeDocumentService
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext
from Backend.Apps.Users.models import Department, Domain, EmployeeProfile, Position


class AtgDocsServiceTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant", slug="tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Docs", code="DOCS")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Main", code="DOCS")
        self.user = get_user_model().objects.create_user(username="docs-user", email="docs@example.com", password="test-password")
        self.viewer_user = get_user_model().objects.create_user(username="docs-viewer", email="viewer@example.com", password="test-password")
        self.external_user = get_user_model().objects.create_user(username="docs-external", email="external@example.com", password="test-password")
        self.domain = Domain.objects.create(tenant=self.tenant, workspace=self.workspace, name="Engineering", code="ENG")
        self.external_domain = Domain.objects.create(tenant=self.tenant, workspace=self.workspace, name="Finance", code="FIN")
        self.department = Department.objects.create(tenant=self.tenant, workspace=self.workspace, name="Platform", code="PLATFORM", domain=self.domain)
        self.sibling_department = Department.objects.create(tenant=self.tenant, workspace=self.workspace, name="QA", code="QA", domain=self.domain)
        self.external_department = Department.objects.create(tenant=self.tenant, workspace=self.workspace, name="Accounts", code="ACC", domain=self.external_domain)
        self.position = Position.objects.create(tenant=self.tenant, workspace=self.workspace, title="Writer", code="WRITER")
        self.owner_employee = EmployeeProfile.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            user=self.user,
            employee_code="DOC-001",
            display_name="Docs Owner",
            department=self.department,
            position=self.position,
        )
        self.viewer_employee = EmployeeProfile.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            user=self.viewer_user,
            employee_code="DOC-002",
            display_name="Docs Viewer",
            department=self.sibling_department,
            position=self.position,
        )
        self.external_employee = EmployeeProfile.objects.create(
            tenant=self.tenant,
            workspace=self.workspace,
            user=self.external_user,
            employee_code="DOC-003",
            display_name="External Viewer",
            department=self.external_department,
            position=self.position,
        )
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)
        self.viewer_context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.viewer_user)
        self.headers = {"HTTP_X_TENANT_ID": str(self.tenant.id), "HTTP_X_WORKSPACE_ID": str(self.workspace.id)}
        self.owner_client = APIClient()
        self.owner_client.force_authenticate(self.user)
        self.viewer_client = APIClient()
        self.viewer_client.force_authenticate(self.viewer_user)
        self.external_client = APIClient()
        self.external_client.force_authenticate(self.external_user)

    def test_create_publish_upload_and_permission(self):
        created = KnowledgeDocumentService.create_document(
            self.context,
            "Guide",
            body="Body",
            department_id=self.department.id,
            visibility=KnowledgeDocument.VISIBILITY_LINK,
            auto_upload=True,
        )
        self.assertTrue(created.ok)
        document = created.data
        self.assertTrue(KnowledgeDocument.objects.filter(id=document.id).exists())
        self.assertEqual(document.department_id, self.department.id)
        self.assertEqual(document.visibility, KnowledgeDocument.VISIBILITY_LINK)

        published = KnowledgeDocumentService.publish(self.context, document.id)
        self.assertTrue(published.ok)
        document.refresh_from_db()
        self.assertEqual(document.status, "Published")

        self.assertTrue(DriveFile.objects.filter(document=document, is_public=True).exists())
        self.assertTrue(KnowledgePermission.objects.filter(document=document, subject_type="public", subject_id="anyone").exists())

        permission = KnowledgeDocumentService.grant_permission(self.context, document.id, "user", "42", permission="Read")
        self.assertTrue(permission.ok)
        self.assertTrue(KnowledgePermission.objects.filter(document=document, subject_id="42").exists())
        self.assertTrue(KnowledgeActivity.objects.filter(document=document, activity_type="DriveUploaded").exists())

        opened = KnowledgeDocumentService.open_document(self.viewer_context, document.id)
        self.assertTrue(opened.ok)
        self.assertTrue(opened.data["openUrl"])
        history = KnowledgeDocumentService.history(self.viewer_context)
        self.assertEqual(len(history.data), 1)

    def test_legacy_routes_group_documents_and_enforce_private_access(self):
        create_response = self.owner_client.post(
            "/AtgDocs/create-post",
            {
                "title": "Legacy Guide",
                "body": "Legacy body",
                "department": self.department.id,
                "visibility": KnowledgeDocument.VISIBILITY_AUTHENTICATED,
            },
            format="json",
            **self.headers,
        )
        self.assertEqual(create_response.status_code, 201)
        document_id = create_response.data["id"]

        private_document = KnowledgeDocumentService.create_document(
            self.context,
            "Private Guide",
            department_id=self.department.id,
            visibility=KnowledgeDocument.VISIBILITY_PRIVATE,
        ).data

        home_response = self.viewer_client.get("/AtgDocs/", **self.headers)
        self.assertEqual(home_response.status_code, 200)
        self.assertEqual(home_response.data["count"], 1)
        self.assertEqual(home_response.data["groups"][0]["documents"][0]["title"], "Legacy Guide")

        my_posts_response = self.owner_client.get("/AtgDocs/myposts/", **self.headers)
        self.assertEqual(my_posts_response.status_code, 200)
        self.assertEqual(len(my_posts_response.data), 2)

        detail_response = self.viewer_client.get(f"/AtgDocs/post-detail/{document_id}", **self.headers)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["title"], "Legacy Guide")

        history_response = self.viewer_client.get("/AtgDocs/history", **self.headers)
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(history_response.data[0]["title"], "Legacy Guide")

        update_response = self.owner_client.post(
            f"/AtgDocs/post-update/{document_id}",
            {"title": "Legacy Guide Updated", "visibility": KnowledgeDocument.VISIBILITY_PRIVATE},
            format="json",
            **self.headers,
        )
        self.assertEqual(update_response.status_code, 200)

        forbidden_response = self.viewer_client.get(f"/AtgDocs/post-detail/{private_document.id}", **self.headers)
        self.assertEqual(forbidden_response.status_code, 403)

        filtered_home = self.viewer_client.get("/AtgDocs/", **self.headers)
        self.assertEqual(filtered_home.status_code, 200)
        self.assertEqual(filtered_home.data["count"], 0)

        external_home = self.external_client.get("/AtgDocs/", **self.headers)
        self.assertEqual(external_home.status_code, 200)
        self.assertEqual(external_home.data["count"], 0)
