from django.db import models, transaction
from django.db.models import Max, Q
from django.utils.text import slugify

from Backend.Apps.AtgDocs.drive_provider import GoogleDriveProvider
from Backend.Apps.AtgDocs.models import DocumentVersion, KnowledgeActivity, KnowledgeDocument, KnowledgePermission
from Backend.Apps.Users.models import Department, EmployeeProfile
from Backend.EnterpriseCore.services import ServiceResult


class KnowledgeDocumentService:
    @staticmethod
    def _actor(context):
        return getattr(context, "actor", context.get("actor")) if isinstance(context, dict) else getattr(context, "actor", None)

    @staticmethod
    def _tenant(context):
        return getattr(context, "tenant", context.get("tenant")) if isinstance(context, dict) else getattr(context, "tenant", None)

    @staticmethod
    def _queryset(context=None):
        qs = KnowledgeDocument.objects.filter(is_active=True).select_related("owner__user", "department")
        tenant = KnowledgeDocumentService._tenant(context)
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs

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
    def _user_has_perm(document, user, require_write=False):
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        if document.owner_id and document.owner and document.owner.user == user:
            return True
        perm_filter = {"document": document, "subject_type": "user", "subject_id": str(user.id)}
        if document.tenant_id:
            perm_filter["tenant_id"] = document.tenant_id
        if require_write:
            perm_filter["permission__in"] = ["Write", "Owner"]
        return KnowledgePermission.objects.filter(**perm_filter).exists()

    @staticmethod
    def _open_url(document):
        if document.metadata.get("drive_file", {}).get("webViewLink"):
            return document.metadata["drive_file"]["webViewLink"]
        return f"/docs/post-detail/{document.id}"

    @staticmethod
    def _actor_employee(context):
        actor = KnowledgeDocumentService._actor(context)
        if not actor: return None
        return EmployeeProfile.objects.filter(user=actor, is_active=True).first()

    @staticmethod
    def create_document(context, title, body="", owner_id=None, department_id=None, document_type="Article", status="Draft", visibility="private", slug="", metadata=None, auto_upload=False, folder_name="Documents", make_public=None):
        actor = KnowledgeDocumentService._actor(context)
        slug = slug or slugify(title)[:180]
        actor_employee = KnowledgeDocumentService._actor_employee(context) if hasattr(context, "tenant") else None
        owner = None
        if owner_id:
            owner = EmployeeProfile.objects.filter(id=owner_id).first()
        elif actor_employee:
            owner = actor_employee
        department = None
        if department_id:
            department = Department.objects.filter(id=department_id).first()
        elif actor_employee and actor_employee.department_id:
            department = actor_employee.department
        tenant = KnowledgeDocumentService._tenant(context)
        with transaction.atomic():
            document = KnowledgeDocument.objects.create(
                title=title, slug=slug, body=body, owner=owner,
                department=department, document_type=document_type,
                status=status, visibility=visibility, metadata=metadata or {},
                tenant=tenant, created_by=actor, updated_by=actor,
            )
            if actor:
                KnowledgePermission.objects.update_or_create(
                    document=document, subject_type="user", subject_id=str(actor.id),
                    defaults={"permission": "Owner", "tenant": tenant},
                )
            KnowledgeDocumentService.record_version(context, document)
            if auto_upload:
                upload_result = KnowledgeDocumentService.upload_to_drive(
                    context, document.id, folder_name=folder_name,
                    make_public=make_public if make_public is not None else visibility == "public",
                )
                if not upload_result.ok:
                    return upload_result
        return ServiceResult.success(document, status_code=201)

    @staticmethod
    def publish(context, document_id):
        actor = KnowledgeDocumentService._actor(context)
        try:
            document = KnowledgeDocument.objects.get(id=document_id)
        except KnowledgeDocument.DoesNotExist:
            return ServiceResult.failure({"document": "Not Found"}, status_code=404)
        document.status = "Published"
        document.updated_by = actor
        document.save(update_fields=["status", "updated_by", "updated_at"])
        KnowledgeActivity.objects.create(
            document=document, activity_type="Published",
            tenant=KnowledgeDocumentService._tenant(context), created_by=actor,
        )
        return ServiceResult.success(document)

    @staticmethod
    def record_version(context, document, metadata=None):
        current = DocumentVersion.objects.filter(document=document).aggregate(
            max_version=Max("version")
        )["max_version"] or 0
        return DocumentVersion.objects.create(
            document=document, version=current + 1,
            title=document.title, body=document.body,
            storage_reference=document.storage_reference,
            metadata=metadata or {},
            tenant=KnowledgeDocumentService._tenant(context),
            created_by=document.updated_by,
            updated_by=document.updated_by,
        )

    @staticmethod
    def upload_to_drive(context, document_id, folder_name="ATG Docs", provider=None, make_public=False):
        try:
            document = KnowledgeDocument.objects.get(id=document_id)
        except KnowledgeDocument.DoesNotExist:
            return ServiceResult.failure({"document": "Not Found"}, status_code=404)
        provider = provider or GoogleDriveProvider()
        root_payload = provider.get_or_create_folder(folder_name)
        target_folder_id = root_payload.get("id", "")
        file_payload = provider.create_file(document.title, body=document.body, folder_id=target_folder_id)
        if file_payload.get("dry_run"):
            pass
        if file_payload.get("webViewLink"):
            document.metadata = {**document.metadata, "drive_file": file_payload}
            document.updated_by = KnowledgeDocumentService._actor(context)
            document.save(update_fields=["metadata", "updated_by", "updated_at"])
        return ServiceResult.success(file_payload, status_code=201)

    @staticmethod
    def grant_permission(context, document_id, user_id, permission="Read", email=""):
        actor = KnowledgeDocumentService._actor(context)
        try:
            document = KnowledgeDocument.objects.get(id=document_id)
        except KnowledgeDocument.DoesNotExist:
            return ServiceResult.failure({"document": "Not Found"}, status_code=404)
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return ServiceResult.failure({"user": "Not Found"}, status_code=404)
        tenant = KnowledgeDocumentService._tenant(context)
        perm, _created = KnowledgePermission.objects.update_or_create(
            document=document, subject_type="user", subject_id=str(user.id),
            defaults={"permission": permission, "updated_by": actor, "tenant": tenant},
        )
        drive_file_id = document.metadata.get("drive_file", {}).get("id") or ""
        if email and drive_file_id:
            role = "writer" if permission.lower() in {"write", "owner"} else "reader"
            GoogleDriveProvider().assign_permission(drive_file_id, email, role=role)
        KnowledgeActivity.objects.create(
            document=document, activity_type="PermissionGranted",
            payload={"user_id": user.id, "permission": permission},
            tenant=tenant, created_by=actor,
        )
        return ServiceResult.success(perm)

    @staticmethod
    def revoke_permission(context, document_id, user_id):
        actor = KnowledgeDocumentService._actor(context)
        try:
            document = KnowledgeDocument.objects.get(id=document_id)
        except KnowledgeDocument.DoesNotExist:
            return ServiceResult.failure({"document": "Not Found"}, status_code=404)
        
        tenant = KnowledgeDocumentService._tenant(context)
        perm = KnowledgePermission.objects.filter(
            document=document, subject_type="user", subject_id=str(user_id), tenant=tenant
        ).first()
        
        if not perm:
            return ServiceResult.failure({"permission": "Not Found"}, status_code=404)

        # Sync with Drive if possible
        drive_file_id = document.metadata.get("drive_file", {}).get("id")
        if drive_file_id:
            from django.contrib.auth.models import User
            user = User.objects.filter(id=user_id).first()
            employee = EmployeeProfile.objects.filter(user=user).first()
            email = employee.user_email if employee else (user.email if user else "")
            if email:
                GoogleDriveProvider().revoke_permission(drive_file_id, email)

        perm.delete()
        
        KnowledgeActivity.objects.create(
            document=document, activity_type="PermissionRevoked",
            payload={"user_id": user_id},
            tenant=tenant, created_by=actor,
        )
        return ServiceResult.success({"revoked": True})

    @staticmethod
    def update_document(context, document_id, **changes):
        actor = KnowledgeDocumentService._actor(context)
        try:
            document = KnowledgeDocument.objects.get(id=document_id)
        except KnowledgeDocument.DoesNotExist:
            return ServiceResult.failure({"document": "Not Found"}, status_code=404)
        if not KnowledgeDocumentService._user_has_perm(document, actor, require_write=True):
            return ServiceResult.failure({"document": "Permission Denied"}, status_code=403)
        for field in ["title", "body", "document_type", "status", "visibility", "slug"]:
            val = changes.get(field)
            if val is not None:
                setattr(document, field, val)
        if "department" in changes:
            document.department = changes["department"]
        if "metadata" in changes and changes["metadata"] is not None:
            document.metadata = changes["metadata"]
        document.updated_by = actor
        document.save()
        KnowledgeDocumentService.record_version(context, document, metadata={"reason": "Updated"})
        return ServiceResult.success(document)

    @staticmethod
    def document_library(context):
        actor = KnowledgeDocumentService._actor(context)
        tenant = KnowledgeDocumentService._tenant(context)
        docs = KnowledgeDocumentService._queryset(context)
        if actor and actor.is_authenticated:
            perm_filter = {"subject_type": "user", "subject_id": str(actor.id)}
            if tenant:
                perm_filter["tenant"] = tenant
            perm_ids = list(KnowledgePermission.objects.filter(**perm_filter).values_list("document_id", flat=True))
            docs = docs.filter(
                Q(owner__user=actor) | Q(id__in=perm_ids) | Q(visibility="public") | Q(visibility="authenticated")
            )
        else:
            docs = docs.filter(visibility="public")
        groups = {}
        for doc in docs.order_by("department__name", "title"):
            key = doc.department_id or 0
            group = groups.setdefault(key, {
                "departmentId": doc.department_id,
                "departmentName": doc.department.name if doc.department_id else "General",
                "documents": [],
            })
            group["documents"].append(KnowledgeDocumentService._document_card(doc))
        return ServiceResult.success({"groups": list(groups.values()), "count": docs.count()})

    @staticmethod
    def my_documents(context):
        actor = KnowledgeDocumentService._actor(context)
        if not actor or not actor.is_authenticated:
            return ServiceResult.success([])
        docs = KnowledgeDocumentService._queryset(context).filter(
            Q(created_by=actor) | Q(owner__user=actor)
        )
        return ServiceResult.success([KnowledgeDocumentService._document_card(d) for d in docs])

    @staticmethod
    def history(context, limit=10):
        actor = KnowledgeDocumentService._actor(context)
        actor_employee = None
        if actor and actor.is_authenticated:
            actor_employee = EmployeeProfile.objects.filter(user=actor, is_active=True).first()
        if not actor_employee:
            return ServiceResult.success([])
        activities = KnowledgeActivity.objects.filter(
            actor=actor_employee, activity_type="Viewed",
        ).select_related("document__department").order_by("-created_at")[:limit]
        rows = []
        for a in activities:
            if not a.document_id:
                continue
            rows.append({
                "documentId": a.document_id,
                "title": a.document.title,
                "departmentName": a.document.department.name if a.document.department_id else "General",
                "visitedAt": a.created_at.isoformat(),
            })
        return ServiceResult.success(rows)

    @staticmethod
    def open_document(context, document_id, record_view=True):
        actor = KnowledgeDocumentService._actor(context)
        try:
            document = KnowledgeDocument.objects.get(id=document_id)
        except KnowledgeDocument.DoesNotExist:
            return ServiceResult.failure({"document": "Not Found"}, status_code=404)
        if not KnowledgeDocumentService._user_has_perm(document, actor):
            return ServiceResult.failure({"document": "Permission Denied"}, status_code=403)
        if record_view:
            actor_employee = KnowledgeDocumentService._actor_employee(context)
            KnowledgeActivity.objects.create(
                document=document, actor=actor_employee, activity_type="Viewed",
                tenant=KnowledgeDocumentService._tenant(context), created_by=actor,
            )
        open_url = KnowledgeDocumentService._open_url(document)
        return ServiceResult.success({"document": document, "openUrl": open_url})

    @staticmethod
    def delete_document(context, document_id):
        actor = KnowledgeDocumentService._actor(context)
        try:
            document = KnowledgeDocument.objects.get(id=document_id)
        except KnowledgeDocument.DoesNotExist:
            return ServiceResult.failure({"document": "Not Found"}, status_code=404)
        if not KnowledgeDocumentService._user_has_perm(document, actor, require_write=True):
            return ServiceResult.failure({"document": "Permission Denied"}, status_code=403)
        drive_file_id = document.metadata.get("drive_file", {}).get("id")
        if drive_file_id:
            GoogleDriveProvider().delete_file(drive_file_id)
        document.delete()
        return ServiceResult.success({"deleted": True})

    @staticmethod
    def _assign_drive_permission(document, email, permission):
        drive_file_id = document.metadata.get("drive_file", {}).get("id")
        if drive_file_id:
            role = "writer" if permission.lower() in {"write", "owner"} else "reader"
            GoogleDriveProvider().assign_permission(drive_file_id, email, role=role)



