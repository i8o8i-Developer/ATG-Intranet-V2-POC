from Backend.Apps.AtgDocs.models import DocumentVersion, DriveFile, DriveFolder, KnowledgeActivity, KnowledgeDocument, KnowledgePermission
from Backend.Apps.AtgDocs.serializers import (
    DocumentVersionSerializer,
    DriveFileSerializer,
    DriveFolderSerializer,
    DriveUploadSerializer,
    KnowledgeActivitySerializer,
    KnowledgeDocumentCreateSerializer,
    KnowledgeDocumentSerializer,
    KnowledgePermissionGrantSerializer,
    KnowledgePermissionSerializer,
)
from Backend.Apps.AtgDocs.services import KnowledgeDocumentService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


class KnowledgeDocumentViewSet(TenantScopedModelViewSet):
    queryset = KnowledgeDocument.objects.select_related("tenant", "workspace", "owner").all()
    serializer_class = KnowledgeDocumentSerializer

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
            data["title"],
            body=data.get("body", ""),
            owner_id=data.get("owner"),
            document_type=data.get("document_type", "Article"),
            status=data.get("status", "Draft"),
            slug=data.get("slug", ""),
            metadata=data.get("metadata", {}),
        )
        return self.service_response(result, KnowledgeDocumentSerializer)

    @action(detail=True, methods=["post"], url_path="upload-to-drive")
    def upload_to_drive(self, request, pk=None):
        serializer = DriveUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = KnowledgeDocumentService.upload_to_drive(
            self.get_tenant_context(),
            pk,
            folder_name=serializer.validated_data.get("folder_name", "ATG Docs"),
            make_public=serializer.validated_data.get("make_public", False),
        )
        return self.service_response(result, DriveFileSerializer)

    @action(detail=True, methods=["post"], url_path="grant-permission")
    def grant_permission(self, request, pk=None):
        serializer = KnowledgePermissionGrantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = KnowledgeDocumentService.grant_permission(
            self.get_tenant_context(),
            pk,
            data["subject_type"],
            data["subject_id"],
            permission=data.get("permission", "Read"),
            email=data.get("email", ""),
        )
        return self.service_response(result, KnowledgePermissionSerializer)

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        queryset = DocumentVersion.objects.filter(tenant=self.get_tenant_context().tenant, document_id=pk)
        return Response(DocumentVersionSerializer(queryset, many=True).data)


class KnowledgePermissionViewSet(TenantScopedModelViewSet):
    queryset = KnowledgePermission.objects.select_related("tenant", "workspace", "document").all()
    serializer_class = KnowledgePermissionSerializer


class KnowledgeActivityViewSet(TenantScopedModelViewSet):
    queryset = KnowledgeActivity.objects.select_related("tenant", "workspace", "document", "actor").all()
    serializer_class = KnowledgeActivitySerializer


class DriveFolderViewSet(TenantScopedModelViewSet):
    queryset = DriveFolder.objects.select_related("tenant", "workspace", "parent").all()
    serializer_class = DriveFolderSerializer


class DriveFileViewSet(TenantScopedModelViewSet):
    queryset = DriveFile.objects.select_related("tenant", "workspace", "document", "folder").all()
    serializer_class = DriveFileSerializer


class DocumentVersionViewSet(TenantScopedModelViewSet):
    queryset = DocumentVersion.objects.select_related("tenant", "workspace", "document", "changed_by").all()
    serializer_class = DocumentVersionSerializer
