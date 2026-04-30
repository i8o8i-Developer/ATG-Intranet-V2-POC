from django.contrib import admin

from Backend.Apps.AtgDocs.models import DocumentVersion, DriveFile, DriveFolder, KnowledgeActivity, KnowledgeDocument, KnowledgePermission


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "document_type", "status", "tenant", "owner", "updated_at")
    list_filter = ("status", "document_type", "tenant")
    search_fields = ("title", "slug", "body")


@admin.register(KnowledgePermission)
class KnowledgePermissionAdmin(admin.ModelAdmin):
    list_display = ("document", "subject_type", "subject_id", "permission", "tenant")
    list_filter = ("subject_type", "permission", "tenant")


@admin.register(KnowledgeActivity)
class KnowledgeActivityAdmin(admin.ModelAdmin):
    list_display = ("document", "activity_type", "actor", "tenant", "created_at")
    list_filter = ("activity_type", "tenant")


@admin.register(DriveFolder)
class DriveFolderAdmin(admin.ModelAdmin):
    list_display = ("name", "path", "drive_folder_id", "tenant")
    search_fields = ("name", "path", "drive_folder_id")


@admin.register(DriveFile)
class DriveFileAdmin(admin.ModelAdmin):
    list_display = ("title", "drive_file_id", "folder", "is_public", "tenant")
    list_filter = ("is_public", "download_restricted", "tenant")
    search_fields = ("title", "drive_file_id")


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ("document", "version", "changed_by", "tenant", "created_at")
    list_filter = ("tenant",)
