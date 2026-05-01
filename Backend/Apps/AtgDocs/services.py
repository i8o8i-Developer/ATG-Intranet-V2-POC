from django.db import transaction
from django.db.models import Max, Q
from django.utils.text import slugify

from Backend.Apps.AtgDocs.drive_provider import GoogleDriveProvider
from Backend.Apps.AtgDocs.models import DocumentVersion, DriveFile, DriveFolder, KnowledgeActivity, KnowledgeDocument, KnowledgePermission
from Backend.Apps.Users.models import Department, EmployeeProfile
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class KnowledgeDocumentService:
    @staticmethod
    def create_document(
        context,
        title,
        body="",
        owner_id=None,
        department_id=None,
        document_type="Article",
        status="Draft",
        visibility=KnowledgeDocument.VISIBILITY_PRIVATE,
        slug="",
        metadata=None,
        auto_upload=False,
        folder_name="Documents",
        make_public=None,
    ):
        if not context.tenant:
            return ServiceResult.failure({"tenant": "Tenant context is required."}, status_code=400)
        slug = slug or slugify(title)[:180]
        if KnowledgeDocument.objects.filter(tenant=context.tenant, slug=slug).exists():
            return ServiceResult.failure({"slug": "Knowledge document slug already exists."}, status_code=400)
        actor_employee = KnowledgeDocumentService._actor_employee(context)
        owner = KnowledgeDocumentService._resolve_owner(context, owner_id=owner_id, actor_employee=actor_employee)
        department = KnowledgeDocumentService._resolve_department(context, department_id=department_id, actor_employee=actor_employee)

        with transaction.atomic():
            document = KnowledgeDocument.objects.create(
                tenant=context.tenant,
                workspace=context.workspace or (owner.workspace if owner and owner.workspace_id else None),
                title=title,
                slug=slug,
                body=body,
                owner=owner,
                department=department,
                document_type=document_type,
                status=status,
                visibility=visibility,
                metadata=metadata or {},
                created_by=context.actor,
                updated_by=context.actor,
            )
            KnowledgeDocumentService.record_version(context, document)
            KnowledgeDocumentService._sync_permission_records(context, document, reset=True)
            OutboxService.publish(context, "KnowledgeDocument", document.id, "KnowledgeDocumentCreated", {"title": title, "visibility": visibility})
            if auto_upload:
                upload_result = KnowledgeDocumentService.upload_to_drive(
                    context,
                    document.id,
                    folder_name=folder_name,
                    make_public=(make_public if make_public is not None else visibility == KnowledgeDocument.VISIBILITY_LINK),
                )
                if not upload_result.ok:
                    return upload_result
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
        document = KnowledgeDocument.objects.filter(tenant=context.tenant, id=document_id).select_related("department", "owner__user").first()
        if not document:
            return ServiceResult.failure({"document": "Knowledge document not found."}, status_code=404)
        provider = provider or GoogleDriveProvider()
        root_name = folder_name or "Documents"
        root_payload = provider.get_or_create_folder(root_name)
        root_folder, _created = DriveFolder.objects.update_or_create(
            tenant=context.tenant,
            drive_folder_id=root_payload.get("id", ""),
            defaults={
                "workspace": context.workspace or document.workspace,
                "name": root_payload.get("name", root_name),
                "path": root_name,
                "metadata": root_payload,
                "updated_by": context.actor,
            },
        )
        target_folder = root_folder
        if document.department_id:
            department_path = f"{root_name}/{document.department.name}"
            department_payload = provider.get_or_create_folder(document.department.name, parent_id=root_folder.drive_folder_id)
            target_folder, _created = DriveFolder.objects.update_or_create(
                tenant=context.tenant,
                drive_folder_id=department_payload.get("id", ""),
                defaults={
                    "workspace": context.workspace or document.workspace,
                    "name": department_payload.get("name", document.department.name),
                    "parent": root_folder,
                    "path": department_path,
                    "metadata": department_payload,
                    "updated_by": context.actor,
                },
            )
        file_payload = provider.create_file(document.title, body=document.body, folder_id=target_folder.drive_folder_id)
        is_public = make_public or document.visibility == KnowledgeDocument.VISIBILITY_LINK
        drive_file, _created = DriveFile.objects.update_or_create(
            tenant=context.tenant,
            drive_file_id=file_payload.get("id", ""),
            defaults={
                "workspace": context.workspace or document.workspace,
                "document": document,
                "folder": target_folder,
                "title": file_payload.get("name", document.title),
                "mime_type": file_payload.get("mimeType", "text/html"),
                "web_view_link": file_payload.get("webViewLink", ""),
                "is_public": is_public,
                "metadata": file_payload,
                "updated_by": context.actor,
            },
        )
        KnowledgeDocumentService._sync_permission_records(context, document, reset=True)
        KnowledgeDocumentService._apply_drive_visibility(context, document, drive_file, provider)
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

    @staticmethod
    def update_document(context, document_id, **changes):
        document = KnowledgeDocument.objects.filter(tenant=context.tenant, id=document_id).select_related("owner__user", "department").first()
        if not document:
            return ServiceResult.failure({"document": "Knowledge document not found."}, status_code=404)
        actor_employee = KnowledgeDocumentService._actor_employee(context)
        if not KnowledgeDocumentService._can_edit(context, document, actor_employee=actor_employee):
            return ServiceResult.failure({"document": "You do not have permission to update this document."}, status_code=403)

        if "slug" in changes and changes.get("slug") and changes["slug"] != document.slug:
            if KnowledgeDocument.objects.filter(tenant=context.tenant, slug=changes["slug"]).exclude(id=document.id).exists():
                return ServiceResult.failure({"slug": "Knowledge document slug already exists."}, status_code=400)

        if "department_id" in changes:
            document.department = KnowledgeDocumentService._resolve_department(context, department_id=changes.get("department_id"), actor_employee=actor_employee, allow_null=True)
        if "title" in changes and changes["title"] is not None:
            document.title = changes["title"]
        if "body" in changes and changes["body"] is not None:
            document.body = changes["body"]
        if "document_type" in changes and changes["document_type"] is not None:
            document.document_type = changes["document_type"]
        if "status" in changes and changes["status"] is not None:
            document.status = changes["status"]
        if "visibility" in changes and changes["visibility"] is not None:
            document.visibility = changes["visibility"]
        if "slug" in changes and changes["slug"]:
            document.slug = changes["slug"]
        if "metadata" in changes and changes["metadata"] is not None:
            document.metadata = changes["metadata"]
        document.updated_by = context.actor
        document.save()
        KnowledgeDocumentService.record_version(context, document, metadata={"reason": "Updated"})
        KnowledgeDocumentService._sync_permission_records(context, document, reset=True)
        document.drive_files.update(is_public=document.visibility == KnowledgeDocument.VISIBILITY_LINK)
        KnowledgeActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or document.workspace,
            document=document,
            actor=actor_employee,
            activity_type="Updated",
            payload={"visibility": document.visibility},
            created_by=context.actor,
        )
        return ServiceResult.success(document)

    @staticmethod
    def document_library(context):
        if not context.tenant:
            return ServiceResult.failure({"tenant": "Tenant context is required."}, status_code=400)
        actor_employee = KnowledgeDocumentService._actor_employee(context)
        queryset = KnowledgeDocumentService._queryset(context)
        if context.actor and getattr(context.actor, "is_authenticated", False) and (context.actor.is_staff or context.actor.is_superuser):
            visible = queryset
        else:
            permission_ids = KnowledgeDocumentService._permission_document_ids(context, actor_employee=actor_employee)
            domain_id = actor_employee.department.domain_id if actor_employee and actor_employee.department_id and actor_employee.department and actor_employee.department.domain_id else None
            department_id = actor_employee.department_id if actor_employee else None
            filters = Q(id__in=permission_ids)
            if actor_employee:
                filters |= Q(owner=actor_employee)
            if domain_id:
                filters |= Q(department__domain_id=domain_id, visibility__in=[KnowledgeDocument.VISIBILITY_AUTHENTICATED, KnowledgeDocument.VISIBILITY_LINK])
            elif department_id:
                filters |= Q(department_id=department_id, visibility__in=[KnowledgeDocument.VISIBILITY_AUTHENTICATED, KnowledgeDocument.VISIBILITY_LINK])
            visible = queryset.filter(filters).distinct()
        groups = []
        grouped = {}
        for document in visible.order_by("department__name", "title"):
            group_key = document.department_id or 0
            group = grouped.setdefault(
                group_key,
                {
                    "departmentId": document.department_id,
                    "departmentName": document.department.name if document.department_id else "General",
                    "documents": [],
                },
            )
            group["documents"].append(KnowledgeDocumentService._document_card(document))
        groups.extend(grouped.values())
        return ServiceResult.success({"groups": groups, "count": sum(len(group["documents"]) for group in groups)})

    @staticmethod
    def my_documents(context):
        actor_employee = KnowledgeDocumentService._actor_employee(context)
        if not actor_employee and not context.actor:
            return ServiceResult.success([])
        queryset = KnowledgeDocumentService._queryset(context)
        filters = Q(created_by=context.actor)
        if actor_employee:
            filters |= Q(owner=actor_employee)
        rows = [KnowledgeDocumentService._document_card(document) for document in queryset.filter(filters).distinct()]
        return ServiceResult.success(rows)

    @staticmethod
    def history(context, limit=10):
        actor_employee = KnowledgeDocumentService._actor_employee(context)
        if not actor_employee:
            return ServiceResult.success([])
        queryset = (
            KnowledgeActivity.objects.filter(tenant=context.tenant, actor=actor_employee, activity_type="Viewed")
            .select_related("document", "document__department")
            .order_by("-created_at")[:limit]
        )
        rows = []
        for activity in queryset:
            if not activity.document_id:
                continue
            rows.append(
                {
                    "documentId": activity.document_id,
                    "title": activity.document.title,
                    "departmentName": activity.document.department.name if activity.document.department_id else "General",
                    "visibility": activity.document.visibility,
                    "openUrl": KnowledgeDocumentService._open_url(activity.document),
                    "visitedAt": activity.created_at.isoformat(),
                }
            )
        return ServiceResult.success(rows)

    @staticmethod
    def open_document(context, document_id, record_view=True):
        document = KnowledgeDocumentService._queryset(context).filter(id=document_id).first()
        if not document:
            return ServiceResult.failure({"document": "Knowledge document not found."}, status_code=404)
        actor_employee = KnowledgeDocumentService._actor_employee(context)
        if not KnowledgeDocumentService._can_view(context, document, actor_employee=actor_employee):
            return ServiceResult.failure({"document": "You do not have permission to access this document."}, status_code=403)
        if record_view:
            KnowledgeDocumentService._record_view(context, document, actor_employee=actor_employee)
        return ServiceResult.success({"document": document, "openUrl": KnowledgeDocumentService._open_url(document)})

    @staticmethod
    def _queryset(context):
        return KnowledgeDocument.objects.filter(tenant=context.tenant, is_active=True).select_related("department__domain", "owner__user")

    @staticmethod
    def _actor_employee(context):
        if not context.tenant or not context.actor or not getattr(context.actor, "is_authenticated", False):
            return None
        queryset = EmployeeProfile.objects.filter(tenant=context.tenant, user=context.actor, is_active=True).select_related("department__domain", "user")
        if context.workspace:
            scoped = queryset.filter(Q(workspace=context.workspace) | Q(workspace__isnull=True))
            employee = scoped.first()
            if employee:
                return employee
        return queryset.first()

    @staticmethod
    def _resolve_owner(context, owner_id=None, actor_employee=None):
        if owner_id:
            return EmployeeProfile.objects.filter(tenant=context.tenant, id=owner_id).first()
        return actor_employee

    @staticmethod
    def _resolve_department(context, department_id=None, actor_employee=None, allow_null=False):
        if department_id is None:
            return None if allow_null else (actor_employee.department if actor_employee and actor_employee.department_id else None)
        return Department.objects.filter(tenant=context.tenant, id=department_id).first()

    @staticmethod
    def _permission_document_ids(context, actor_employee=None, write_required=False):
        queryset = KnowledgePermission.objects.filter(tenant=context.tenant)
        if write_required:
            queryset = queryset.filter(permission__iregex=r"^(write|editor|owner)$")
        filters = Q(subject_type="public", subject_id="anyone")
        if context.actor and getattr(context.actor, "is_authenticated", False):
            filters |= Q(subject_type="user", subject_id=str(context.actor.id))
        if actor_employee:
            filters |= Q(subject_type="employee", subject_id=str(actor_employee.id))
            if actor_employee.department_id:
                filters |= Q(subject_type="department", subject_id=str(actor_employee.department_id))
                if actor_employee.department and actor_employee.department.domain_id:
                    filters |= Q(subject_type="domain", subject_id=str(actor_employee.department.domain_id))
        if context.workspace:
            filters |= Q(subject_type="workspace", subject_id=str(context.workspace.id))
        if context.tenant:
            filters |= Q(subject_type="tenant", subject_id=str(context.tenant.id))
        return list(queryset.filter(filters).values_list("document_id", flat=True))

    @staticmethod
    def _can_view(context, document, actor_employee=None):
        if document.visibility == KnowledgeDocument.VISIBILITY_LINK:
            return True
        if context.actor and getattr(context.actor, "is_authenticated", False) and (context.actor.is_staff or context.actor.is_superuser):
            return True
        if actor_employee and document.owner_id == actor_employee.id:
            return True
        if context.actor and getattr(context.actor, "is_authenticated", False) and document.visibility == KnowledgeDocument.VISIBILITY_AUTHENTICATED:
            return True
        return document.id in KnowledgeDocumentService._permission_document_ids(context, actor_employee=actor_employee)

    @staticmethod
    def _can_edit(context, document, actor_employee=None):
        if context.actor and getattr(context.actor, "is_authenticated", False) and (context.actor.is_staff or context.actor.is_superuser):
            return True
        if actor_employee and document.owner_id == actor_employee.id:
            return True
        return document.id in KnowledgeDocumentService._permission_document_ids(context, actor_employee=actor_employee, write_required=True)

    @staticmethod
    def _record_view(context, document, actor_employee=None):
        actor_employee = actor_employee or KnowledgeDocumentService._actor_employee(context)
        if not actor_employee:
            return None
        KnowledgeActivity.objects.filter(tenant=context.tenant, document=document, actor=actor_employee, activity_type="Viewed").delete()
        return KnowledgeActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or document.workspace,
            document=document,
            actor=actor_employee,
            activity_type="Viewed",
            payload={"openUrl": KnowledgeDocumentService._open_url(document)},
            created_by=context.actor,
        )

    @staticmethod
    def _open_url(document):
        drive_file = document.drive_files.order_by("-id").first()
        if drive_file and drive_file.web_view_link:
            return drive_file.web_view_link
        if document.metadata.get("drive_file", {}).get("webViewLink"):
            return document.metadata["drive_file"]["webViewLink"]
        return document.external_url or ""

    @staticmethod
    def _document_card(document):
        return {
            "id": document.id,
            "title": document.title,
            "slug": document.slug,
            "status": document.status,
            "visibility": document.visibility,
            "departmentId": document.department_id,
            "departmentName": document.department.name if document.department_id else "General",
            "ownerId": document.owner_id,
            "ownerName": document.owner.display_name if document.owner_id else "",
            "updatedAt": document.updated_at.isoformat(),
            "openUrl": KnowledgeDocumentService._open_url(document),
        }

    @staticmethod
    def _sync_permission_records(context, document, reset=False):
        if reset:
            KnowledgePermission.objects.filter(document=document, subject_type__in=["employee", "tenant", "public"]).delete()
        if document.owner_id:
            KnowledgePermission.objects.update_or_create(
                tenant=context.tenant,
                workspace=context.workspace or document.workspace,
                document=document,
                subject_type="employee",
                subject_id=str(document.owner_id),
                defaults={"permission": "Write", "updated_by": context.actor},
            )
        if document.visibility == KnowledgeDocument.VISIBILITY_AUTHENTICATED:
            KnowledgePermission.objects.update_or_create(
                tenant=context.tenant,
                workspace=context.workspace or document.workspace,
                document=document,
                subject_type="tenant",
                subject_id=str(context.tenant.id),
                defaults={"permission": "Read", "updated_by": context.actor},
            )
        elif document.visibility == KnowledgeDocument.VISIBILITY_LINK:
            KnowledgePermission.objects.update_or_create(
                tenant=context.tenant,
                workspace=context.workspace or document.workspace,
                document=document,
                subject_type="public",
                subject_id="anyone",
                defaults={"permission": "Read", "updated_by": context.actor},
            )

    @staticmethod
    def _apply_drive_visibility(context, document, drive_file, provider):
        if document.owner_id and document.owner and document.owner.user.email:
            provider.assign_permission(drive_file.drive_file_id, document.owner.user.email, role="writer")
        if document.visibility == KnowledgeDocument.VISIBILITY_AUTHENTICATED:
            emails = list(
                EmployeeProfile.objects.filter(tenant=context.tenant, is_active=True, user__is_active=True)
                .exclude(user__email="")
                .values_list("user__email", flat=True)
                .distinct()
            )
            for email in emails:
                provider.assign_permission(drive_file.drive_file_id, email, role="writer")
        elif document.visibility == KnowledgeDocument.VISIBILITY_LINK:
            provider.set_file_public(drive_file.drive_file_id)
