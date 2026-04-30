from django.contrib.auth import get_user_model
from django.test import TestCase

from Backend.Apps.AtgDocs.models import DriveFile, KnowledgeActivity, KnowledgeDocument, KnowledgePermission
from Backend.Apps.AtgDocs.services import KnowledgeDocumentService
from Backend.EnterpriseCore.models import BusinessUnit, Organization, Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext


class AtgDocsServiceTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant", slug="tenant")
        self.organization = Organization.objects.create(tenant=self.tenant, name="Org", slug="org")
        self.business_unit = BusinessUnit.objects.create(tenant=self.tenant, organization=self.organization, name="Docs", code="DOCS")
        self.workspace = Workspace.objects.create(tenant=self.tenant, business_unit=self.business_unit, name="Main", code="DOCS")
        self.user = get_user_model().objects.create_user(username="docs-user", email="docs@example.com")
        self.context = TenantContext(tenant=self.tenant, workspace=self.workspace, actor=self.user)

    def test_create_publish_upload_and_permission(self):
        created = KnowledgeDocumentService.create_document(self.context, "Guide", body="Body")
        self.assertTrue(created.ok)
        document = created.data
        self.assertTrue(KnowledgeDocument.objects.filter(id=document.id).exists())

        published = KnowledgeDocumentService.publish(self.context, document.id)
        self.assertTrue(published.ok)
        document.refresh_from_db()
        self.assertEqual(document.status, "Published")

        uploaded = KnowledgeDocumentService.upload_to_drive(self.context, document.id, make_public=True)
        self.assertTrue(uploaded.ok)
        self.assertTrue(DriveFile.objects.filter(document=document).exists())

        permission = KnowledgeDocumentService.grant_permission(self.context, document.id, "user", "42", permission="Read")
        self.assertTrue(permission.ok)
        self.assertTrue(KnowledgePermission.objects.filter(document=document, subject_id="42").exists())
        self.assertTrue(KnowledgeActivity.objects.filter(document=document, activity_type="DriveUploaded").exists())
