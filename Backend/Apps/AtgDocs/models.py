from django.db import models

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class KnowledgeDocument(TenantScopedModel, ExternalReference):
    VISIBILITY_PRIVATE = "private"
    VISIBILITY_AUTHENTICATED = "authenticated"
    VISIBILITY_LINK = "link"
    VISIBILITY_CHOICES = [
        (VISIBILITY_PRIVATE, "Private"),
        (VISIBILITY_AUTHENTICATED, "Authenticated User"),
        (VISIBILITY_LINK, "Anyone with the Link"),
    ]

    title = models.CharField(max_length=240)
    slug = models.SlugField(max_length=180)
    document_type = models.CharField(max_length=100, default="Article", db_index=True)
    status = models.CharField(max_length=80, default="Draft", db_index=True)
    body = models.TextField(blank=True)
    storage_reference = models.CharField(max_length=260, blank=True)
    owner = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="knowledge_documents")
    department = models.ForeignKey("Users.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="knowledge_documents")
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_PRIVATE, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "title"]
        constraints = [models.UniqueConstraint(fields=["tenant", "slug"], name="docs_slug_per_tenant")]

    def __str__(self):
        return self.title


class KnowledgePermission(TenantScopedModel):
    document = models.ForeignKey("AtgDocs.KnowledgeDocument", on_delete=models.CASCADE, related_name="permissions")
    subject_type = models.CharField(max_length=80, db_index=True)
    subject_id = models.CharField(max_length=120, db_index=True)
    permission = models.CharField(max_length=80, default="Read")

    class Meta:
        indexes = [models.Index(fields=["tenant", "subject_type", "subject_id"])]


class KnowledgeActivity(TenantScopedModel):
    document = models.ForeignKey("AtgDocs.KnowledgeDocument", on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="knowledge_activities")
    activity_type = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class DriveFolder(TenantScopedModel, ExternalReference):
    name = models.CharField(max_length=220)
    parent = models.ForeignKey("AtgDocs.DriveFolder", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    drive_folder_id = models.CharField(max_length=220, blank=True, db_index=True)
    path = models.CharField(max_length=500, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "path", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "path", "name"], name="docs_drive_folder_path_per_tenant")]


class DriveFile(TenantScopedModel, ExternalReference):
    document = models.ForeignKey("AtgDocs.KnowledgeDocument", null=True, blank=True, on_delete=models.SET_NULL, related_name="drive_files")
    folder = models.ForeignKey("AtgDocs.DriveFolder", null=True, blank=True, on_delete=models.SET_NULL, related_name="files")
    title = models.CharField(max_length=240)
    mime_type = models.CharField(max_length=180, blank=True)
    drive_file_id = models.CharField(max_length=220, blank=True, db_index=True)
    web_view_link = models.URLField(blank=True)
    download_restricted = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "title"]


class DocumentVersion(TenantScopedModel):
    document = models.ForeignKey("AtgDocs.KnowledgeDocument", on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=240)
    body = models.TextField(blank=True)
    storage_reference = models.CharField(max_length=260, blank=True)
    changed_by = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="knowledge_document_versions")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "document_id", "-version"]
        constraints = [models.UniqueConstraint(fields=["tenant", "document", "version"], name="docs_document_version_per_tenant")]
