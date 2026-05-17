import json
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)


class GoogleDriveProvider:
    DRIVE_API = "https://www.googleapis.com/drive/v3"

    def __init__(self):
        self._creds = None

    def _load_credentials(self):
        if self._creds:
            return self._creds
        raw = os.getenv("GOOGLE_OAUTH_TOKEN_JSON", "") or getattr(settings, "GOOGLE_OAUTH_TOKEN_JSON", "")
        if not raw:
            return None
        try:
            from google.oauth2 import service_account
            info = json.loads(raw)
            self._creds = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/documents"]
            )
            return self._creds
        except Exception as e:
            logger.warning("Failed To Load Google Credentials: %s", e)
            return None

    def _get_access_token(self):
        creds = self._load_credentials()
        if not creds:
            return None
        try:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            return creds.token
        except Exception as e:
            logger.error("Failed To Refresh Google Token: %s", e)
            return None

    def _headers(self):
        token = self._get_access_token()
        if not token:
            return None
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _request(self, method, url, **kwargs):
        headers = self._headers()
        if not headers:
            return None
        headers.update(kwargs.pop("headers", {}))
        import requests as req
        try:
            resp = req.request(method, url, headers=headers, timeout=30, **kwargs)
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except Exception as e:
            logger.error("Google API Error: %s", e)
            return None

    def get_or_create_folder(self, name, parent_id=""):
        hdrs = self._headers()
        if not hdrs:
            return {"id": f"Dry-Folder-{name}", "name": name, "dry_run": True}
        import requests as req
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        hdrs["Content-Type"] = "application/json"
        try:
            resp = req.get(f"{self.DRIVE_API}/files", headers=hdrs, params={"q": query, "fields": "files(id,name,parents)"}, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("files"):
                f = data["files"][0]
                return {"id": f["id"], "name": f["name"], "parents": f.get("parents", [])}
        except Exception as e:
            logger.warning("Folder Lookup Failed, Creating: %s", e)
        body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            body["parents"] = [parent_id]
        try:
            resp = req.post(f"{self.DRIVE_API}/files", headers=hdrs, json=body, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Failed To Create Folder: %s", e)
            return {"id": f"Dry-Folder-{name}", "name": name, "dry_run": True}

    def create_file(self, name, body="", mime_type="text/html", folder_id=""):
        hdrs = self._headers()
        if not hdrs:
            return {
                "id": f"Dry-File-{name}", "name": name, "mimeType": mime_type,
                "webViewLink": f"https://drive.local/{name}", "dry_run": True,
            }
        doc_mime = "application/vnd.google-apps.document"
        metadata = {"name": name, "mimeType": doc_mime}
        if folder_id:
            metadata["parents"] = [folder_id]
        boundary = "----boundary_googledocs_12345"
        nl = "\r\n"
        body_parts = [
            f"--{boundary}",
            f"Content-Type: application/json; charset=UTF-8{nl}",
            json.dumps(metadata),
            f"--{boundary}",
            f"Content-Type: {mime_type}{nl}",
            body or "",
            f"--{boundary}--",
        ]
        upload_headers = {**hdrs, "Content-Type": f"multipart/related; boundary={boundary}"}
        upload_headers.pop("Content-Type", None) if "Content-Type" in upload_headers and upload_headers["Content-Type"] == "application/json" else None
        upload_headers["Content-Type"] = f"multipart/related; boundary={boundary}"
        import requests as req
        try:
            resp = req.post(
                f"{self.DRIVE_API}/files?uploadType=multipart&fields=id,name,mimeType,webViewLink,parents",
                headers=upload_headers,
                data="".join(body_parts).encode("utf-8") if isinstance("".join(body_parts), str) else "".join(body_parts),
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Failed To Create Drive File: %s", e)
            return {
                "id": f"Dry-File-{name}", "name": name, "mimeType": doc_mime,
                "webViewLink": f"https://drive.local/{name}", "dry_run": True,
            }

    def upload_to_drive(self, name, file_content, mime_type="text/html", folder_id=""):
        return self.create_file(name, body=file_content, mime_type=mime_type, folder_id=folder_id)

    def assign_permission(self, file_id, email, role="reader", permission_type="user"):
        hdrs = self._headers()
        if not hdrs:
            return {"file_id": file_id, "email": email, "role": role, "dry_run": True}
        import requests as req
        # 
        body = {"type": permission_type, "role": role}
        if permission_type == "user":
            body["emailAddress"] = email
        
        try:
            resp = req.post(
                f"{self.DRIVE_API}/files/{file_id}/permissions",
                headers=hdrs, json=body, timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Failed To Assign Permission: %s", e)
            return {"file_id": file_id, "email": email, "role": role, "dry_run": True, "error": str(e)}

    def revoke_permission(self, file_id, email):
        hdrs = self._headers()
        if not hdrs:
            return {"file_id": file_id, "email": email, "dry_run": True}
        import requests as req
        try:
            # 1. 
            resp = req.get(f"{self.DRIVE_API}/files/{file_id}/permissions", headers=hdrs, params={"fields": "permissions(id,emailAddress)"}, timeout=30)
            resp.raise_for_status()
            perms = resp.json().get("permissions", [])
            perm_id = next((p["id"] for p in perms if p.get("emailAddress") == email), None)
            
            if not perm_id:
                return {"file_id": file_id, "email": email, "revoked": False, "reason": "Not Found"}

            # 2. Delete the permission
            resp = req.delete(f"{self.DRIVE_API}/files/{file_id}/permissions/{perm_id}", headers=hdrs, timeout=30)
            resp.raise_for_status()
            return {"file_id": file_id, "email": email, "revoked": True}
        except Exception as e:
            logger.error("Failed To Revoke Permission: %s", e)
            return {"file_id": file_id, "email": email, "revoked": False, "error": str(e)}

    def set_file_public(self, file_id, role="reader"):
        return self.assign_permission(file_id, "anyone", role=role, permission_type="anyone")

    def restrict_editor_download(self, file_id):
        hdrs = self._headers()
        if not hdrs:
            return {"file_id": file_id, "dry_run": True}
        import requests as req
        try:
            resp = req.patch(
                f"{self.DRIVE_API}/files/{file_id}",
                headers=hdrs, json={"copyRequiresWriterPermission": True}, timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Failed To Restrict Download: %s", e)      
            return {"file_id": file_id, "dry_run": True, "error": str(e)}

    def delete_file(self, file_id):
        hdrs = self._headers()
        if not hdrs:
            return {"file_id": file_id, "dry_run": True, "deleted": True}
        import requests as req
        try:
            resp = req.delete(f"{self.DRIVE_API}/files/{file_id}", headers=hdrs, timeout=30)
            resp.raise_for_status()
            return {"file_id": file_id, "deleted": True}
        except Exception as e:
            logger.error("Failed To Delete Drive File: %s", e)
            return {"file_id": file_id, "deleted": False, "error": str(e)}

    def rename_file(self, file_id, new_name):
        hdrs = self._headers()
        if not hdrs:
            return {"file_id": file_id, "name": new_name, "dry_run": True}
        import requests as req
        try:
            resp = req.patch(
                f"{self.DRIVE_API}/files/{file_id}",
                headers=hdrs, json={"name": new_name}, timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Failed To Rename Drive File: %s", e)
            return {"file_id": file_id, "error": str(e)}

    def list_files(self, folder_id=None, query=None):
        hdrs = self._headers()
        if not hdrs:
            return {"files": [], "dry_run": True}
        import requests as req
        q = query or "trashed=false"
        if folder_id:
            q += f" and '{folder_id}' in parents"
        try:
            resp = req.get(
                f"{self.DRIVE_API}/files",
                headers=hdrs, params={"q": q, "fields": "files(id,name,mimeType,webViewLink,parents,modifiedTime,owners)"},
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Failed To List Drive Files: %s", e)
            return {"files": [], "error": str(e)}


def get_credentials():
    return GoogleDriveProvider()._load_credentials()

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

def delete_file(file_id):
    return GoogleDriveProvider().delete_file(file_id)

def rename_file(file_id, new_name):
    return GoogleDriveProvider().rename_file(file_id, new_name)

def list_files(folder_id=None, query=None):
    return GoogleDriveProvider().list_files(folder_id=folder_id, query=query)
