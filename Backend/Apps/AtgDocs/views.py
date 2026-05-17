from Backend.Apps.AtgDocs.models import DocumentVersion, DriveFile, DriveFolder, KnowledgeActivity, KnowledgeDocument, KnowledgePermission
from Backend.Apps.AtgDocs.serializers import (
    DocumentVersionSerializer,
    DriveFileSerializer,
    DriveFolderSerializer,
    DriveUploadSerializer,
    KnowledgeActivitySerializer,
    KnowledgeDocumentCreateSerializer,
    KnowledgeDocumentUpdateSerializer,
    KnowledgeDocumentSerializer,
    KnowledgePermissionGrantSerializer,
    KnowledgePermissionSerializer,
)
from Backend.Apps.AtgDocs.services import KnowledgeDocumentService
from Backend.EnterpriseCore.models import Tenant
from Backend.EnterpriseCore.services import TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


class SimpleDocsViewSet(TenantScopedModelViewSet):
    def get_request_tenant(self):
        tenant = getattr(self.request, "tenant", None) or Tenant.objects.filter(id=1).first()
        return tenant

    def get_request_workspace(self):
        return None

    def get_tenant_context(self):
        return TenantContext(
            tenant=self.get_request_tenant(),
            workspace=None,
            actor=self.request.user if self.request.user.is_authenticated else None,
        )


class KnowledgeDocumentViewSet(SimpleDocsViewSet):
    queryset = KnowledgeDocument.objects.all()
    serializer_class = KnowledgeDocumentSerializer

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        result = KnowledgeDocumentService.publish(self.get_tenant_context(), pk)
        return self.service_response(result, KnowledgeDocumentSerializer)

    @action(detail=False, methods=["post"], url_path="create-document")
    def create_document(self, request):
        serializer = KnowledgeDocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = KnowledgeDocumentService.create_document(
            self.get_tenant_context(),
            data["title"], body=data.get("body", ""),
            owner_id=data.get("owner"), department_id=data.get("department"),
            document_type=data.get("document_type", "Article"),
            status=data.get("status", "Draft"),
            visibility=data.get("visibility", "private"),
            slug=data.get("slug", ""), metadata=data.get("metadata", {}),
            auto_upload=data.get("upload_to_drive", False),
            folder_name=data.get("folder_name", "Documents"),
            make_public=data.get("make_public"),
        )
        return self.service_response(result, KnowledgeDocumentSerializer)

    @action(detail=True, methods=["post"], url_path="upload-to-drive")
    def upload_to_drive(self, request, pk=None):
        serializer = DriveUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = KnowledgeDocumentService.upload_to_drive(
            self.get_tenant_context(), pk,
            folder_name=serializer.validated_data.get("folder_name", "Documents"),
            make_public=serializer.validated_data.get("make_public", False),
        )
        return self.service_response(result, DriveFileSerializer)

    @action(detail=True, methods=["post"], url_path="grant-permission")
    def grant_permission(self, request, pk=None):
        serializer = KnowledgePermissionGrantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = KnowledgeDocumentService.grant_permission(
            self.get_tenant_context(), pk,
            data["user_id"], permission=data.get("permission", "Read"),
            email=data.get("email", ""),
        )
        return self.service_response(result, KnowledgePermissionSerializer)

    @action(detail=True, methods=["post"], url_path="revoke-permission")
    def revoke_permission(self, request, pk=None):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"user_id": "Required"}, status=400)
        result = KnowledgeDocumentService.revoke_permission(self.get_tenant_context(), pk, user_id)
        return self.service_response(result)

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        queryset = DocumentVersion.objects.filter(document_id=pk).order_by("-version")
        return Response(DocumentVersionSerializer(queryset, many=True).data)

    @action(detail=False, methods=["get"], url_path="library")
    def library(self, request):
        result = KnowledgeDocumentService.document_library(self.get_tenant_context())
        return Response(result.data, status=result.status_code)

    @action(detail=False, methods=["get"], url_path="my-documents")
    def my_documents(self, request):
        result = KnowledgeDocumentService.my_documents(self.get_tenant_context())
        return Response(result.data, status=result.status_code)

    @action(detail=False, methods=["get"], url_path="visit-history")
    def visit_history(self, request):
        result = KnowledgeDocumentService.history(self.get_tenant_context())
        return Response(result.data, status=result.status_code)

    @action(detail=True, methods=["get"], url_path="open")
    def open_document(self, request, pk=None):
        result = KnowledgeDocumentService.open_document(self.get_tenant_context(), pk)
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        data = KnowledgeDocumentSerializer(result.data["document"], context=self.get_serializer_context()).data
        data["openUrl"] = result.data.get("openUrl", "")
        data["canEdit"] = result.data.get("canEdit", False)
        return Response(data, status=result.status_code)

    @action(detail=True, methods=["post", "put", "patch"], url_path="update-content")
    def update_content(self, request, pk=None):
        serializer = KnowledgeDocumentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = KnowledgeDocumentService.update_document(
            self.get_tenant_context(), pk,
            title=data.get("title"), body=data.get("body"),
            department=data.get("department") if "department" in data else None,
            document_type=data.get("document_type"), status=data.get("status"),
            visibility=data.get("visibility"), slug=data.get("slug"),
            metadata=data.get("metadata") if "metadata" in data else None,
        )
        return self.service_response(result, KnowledgeDocumentSerializer)

    @action(detail=True, methods=["post", "delete"], url_path="delete-document")
    def delete_document(self, request, pk=None):
        result = KnowledgeDocumentService.delete_document(self.get_tenant_context(), pk)
        return self.service_response(result)


class KnowledgePermissionViewSet(SimpleDocsViewSet):
    queryset = KnowledgePermission.objects.all()
    serializer_class = KnowledgePermissionSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return super().get_queryset().filter(subject_type="user")


class KnowledgeActivityViewSet(SimpleDocsViewSet):
    queryset = KnowledgeActivity.objects.all()
    serializer_class = KnowledgeActivitySerializer


class DocumentVersionViewSet(SimpleDocsViewSet):
    queryset = DocumentVersion.objects.all()
    serializer_class = DocumentVersionSerializer


class DriveFolderViewSet(SimpleDocsViewSet):
    queryset = DriveFolder.objects.all()
    serializer_class = DriveFolderSerializer


class DriveFileViewSet(SimpleDocsViewSet):
    queryset = DriveFile.objects.all()
    serializer_class = DriveFileSerializer
