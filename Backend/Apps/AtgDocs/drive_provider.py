from django.conf import settings


class GoogleDriveProvider:
    def __init__(self, service=None):
        self.service = service

    def get_credentials(self):
        return getattr(settings, "GOOGLE_DRIVE_CREDENTIALS", None)

    def get_or_create_folder(self, name, parent_id=""):
        if self.service:
            return self.service.get_or_create_folder(name, parent_id=parent_id)
        return {"id": f"dry-folder-{name}", "name": name, "parent_id": parent_id, "dry_run": True}

    def create_file(self, name, body="", mime_type="text/html", folder_id=""):
        if self.service:
            return self.service.create_file(name=name, body=body, mime_type=mime_type, folder_id=folder_id)
        return {
            "id": f"dry-file-{name}",
            "name": name,
            "mimeType": mime_type,
            "webViewLink": f"https://drive.local/{name}",
            "parents": [folder_id] if folder_id else [],
            "dry_run": True,
        }

    def upload_to_drive(self, name, file_content, mime_type="application/octet-stream", folder_id=""):
        return self.create_file(name, body=file_content, mime_type=mime_type, folder_id=folder_id)

    def assign_permission(self, file_id, email, role="reader", permission_type="user"):
        if self.service:
            return self.service.assign_permission(file_id=file_id, email=email, role=role, permission_type=permission_type)
        return {"file_id": file_id, "email": email, "role": role, "type": permission_type, "dry_run": True}

    def set_file_public(self, file_id, role="reader"):
        return self.assign_permission(file_id, "anyone", role=role, permission_type="anyone")

    def restrict_editor_download(self, file_id):
        if self.service:
            return self.service.restrict_editor_download(file_id=file_id)
        return {"file_id": file_id, "copyRequiresWriterPermission": True, "dry_run": True}


def get_credentials():
    return GoogleDriveProvider().get_credentials()


def get_or_create_folder(name, parent_id=""):
    return GoogleDriveProvider().get_or_create_folder(name, parent_id=parent_id)


def create_google_file(name, body="", mime_type="text/html", folder_id=""):
    return GoogleDriveProvider().create_file(name, body=body, mime_type=mime_type, folder_id=folder_id)


def create_file(name, body="", mime_type="text/html", folder_id=""):
    return create_google_file(name, body=body, mime_type=mime_type, folder_id=folder_id)


def upload_to_drive(name, file_content, mime_type="application/octet-stream", folder_id=""):
    return GoogleDriveProvider().upload_to_drive(name, file_content, mime_type=mime_type, folder_id=folder_id)


def assign_permission(file_id, email, role="reader", permission_type="user"):
    return GoogleDriveProvider().assign_permission(file_id, email, role=role, permission_type=permission_type)


def set_file_public(file_id, role="reader"):
    return GoogleDriveProvider().set_file_public(file_id, role=role)


def restrict_editor_download(file_id):
    return GoogleDriveProvider().restrict_editor_download(file_id)
