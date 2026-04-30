from django.db.models import Max
from django.utils.text import slugify

from Backend.Apps.AtgDocs.drive_provider import GoogleDriveProvider
from Backend.Apps.AtgDocs.models import DocumentVersion, DriveFile, DriveFolder, KnowledgeActivity, KnowledgeDocument, KnowledgePermission
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class KnowledgeDocumentService:
    @staticmethod
    def create_document(context, title, body="", owner_id=None, document_type="Article", status="Draft", slug="", metadata=None):
        slug = slug or slugify(title)[:180]
        if KnowledgeDocument.objects.filter(tenant=context.tenant, slug=slug).exists():
            return ServiceResult.failure({"slug": "Knowledge document slug already exists."}, status_code=400)
        document = KnowledgeDocument.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            title=title,
            slug=slug,
            body=body,
            owner_id=owner_id,
            document_type=document_type,
            status=status,
            metadata=metadata or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        KnowledgeDocumentService.record_version(context, document)
        OutboxService.publish(context, "KnowledgeDocument", document.id, "KnowledgeDocumentCreated", {"title": title})
        return ServiceResult.success(document, status_code=201)

    @staticmethod
    def publish(context, document_id):
        document = KnowledgeDocument.objects.filter(tenant=context.tenant, id=document_id).first()
        if not document:
            return ServiceResult.failure({"document": "Knowledge document not found."}, status_code=404)
        document.status = "Published"
        document.updated_by = context.actor
        document.save(update_fields=["status", "updated_by", "updated_at"])
        KnowledgeActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            document=document,
            activity_type="Published",
            created_by=context.actor,
        )
        OutboxService.publish(context, "KnowledgeDocument", document.id, "KnowledgeDocumentPublished", {"slug": document.slug})
        return ServiceResult.success(document)

    @staticmethod
    def record_version(context, document, metadata=None):
        current = DocumentVersion.objects.filter(tenant=context.tenant, document=document).aggregate(max_version=Max("version"))["max_version"] or 0
        version = DocumentVersion.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or document.workspace,
            document=document,
            version=current + 1,
            title=document.title,
            body=document.body,
            storage_reference=document.storage_reference,
            metadata=metadata or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        KnowledgeActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or document.workspace,
            document=document,
            activity_type="VersionRecorded",
            payload={"version": version.version},
            created_by=context.actor,
        )
        return version

    @staticmethod
    def upload_to_drive(context, document_id, folder_name="ATG Docs", provider=None, make_public=False):
        document = KnowledgeDocument.objects.filter(tenant=context.tenant, id=document_id).first()
        if not document:
            return ServiceResult.failure({"document": "Knowledge document not found."}, status_code=404)
        provider = provider or GoogleDriveProvider()
        folder_payload = provider.get_or_create_folder(folder_name)
        folder, _created = DriveFolder.objects.update_or_create(
            tenant=context.tenant,
            drive_folder_id=folder_payload.get("id", ""),
            defaults={
                "workspace": context.workspace or document.workspace,
                "name": folder_payload.get("name", folder_name),
                "path": folder_name,
                "metadata": folder_payload,
                "updated_by": context.actor,
            },
        )
        file_payload = provider.create_file(document.title, body=document.body, folder_id=folder.drive_folder_id)
        drive_file, _created = DriveFile.objects.update_or_create(
            tenant=context.tenant,
            drive_file_id=file_payload.get("id", ""),
            defaults={
                "workspace": context.workspace or document.workspace,
                "document": document,
                "folder": folder,
                "title": file_payload.get("name", document.title),
                "mime_type": file_payload.get("mimeType", "text/html"),
                "web_view_link": file_payload.get("webViewLink", ""),
                "is_public": make_public,
                "metadata": file_payload,
                "updated_by": context.actor,
            },
        )
        if make_public:
            provider.set_file_public(drive_file.drive_file_id)
        provider.restrict_editor_download(drive_file.drive_file_id)
        document.storage_reference = drive_file.drive_file_id
        document.metadata = {**document.metadata, "drive_file": file_payload}
        document.updated_by = context.actor
        document.save(update_fields=["storage_reference", "metadata", "updated_by", "updated_at"])
        KnowledgeActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or document.workspace,
            document=document,
            activity_type="DriveUploaded",
            payload={"driveFileId": drive_file.drive_file_id, "folder": folder_name},
            created_by=context.actor,
        )
        OutboxService.publish(context, "KnowledgeDocument", document.id, "KnowledgeDocumentUploadedToDrive", {"driveFileId": drive_file.drive_file_id})
        return ServiceResult.success(drive_file, status_code=201)

    @staticmethod
    def grant_permission(context, document_id, subject_type, subject_id, permission="Read", provider=None, email=""):
        document = KnowledgeDocument.objects.filter(tenant=context.tenant, id=document_id).first()
        if not document:
            return ServiceResult.failure({"document": "Knowledge document not found."}, status_code=404)
        row, _created = KnowledgePermission.objects.update_or_create(
            tenant=context.tenant,
            workspace=context.workspace or document.workspace,
            document=document,
            subject_type=subject_type,
            subject_id=subject_id,
            defaults={"permission": permission, "updated_by": context.actor},
        )
        if email and document.storage_reference:
            role = "writer" if permission.lower() in {"write", "editor", "owner"} else "reader"
            (provider or GoogleDriveProvider()).assign_permission(document.storage_reference, email, role=role)
        KnowledgeActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or document.workspace,
            document=document,
            activity_type="PermissionGranted",
            payload={"subject_type": subject_type, "subject_id": subject_id, "permission": permission},
            created_by=context.actor,
        )
        return ServiceResult.success(row)
