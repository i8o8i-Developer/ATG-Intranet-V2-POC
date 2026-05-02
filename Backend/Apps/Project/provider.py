import os
from datetime import timedelta
from urllib.parse import urlencode

import requests
from django.utils import timezone


class ProjectIntegrationProviderError(Exception):
    pass


class ProjectIntegrationProvider:
    github_base_url = "https://api.github.com"

    def __init__(self, live=False, github_token=None, session=None, timeout=20):
        self.live = live
        self.github_token = github_token or os.getenv("GITHUB_ACCESS_TOKEN", "")
        self.session = session or requests.Session()
        self.timeout = timeout

    def _github_headers(self):
        if not self.github_token:
            raise ProjectIntegrationProviderError("GITHUB_ACCESS_TOKEN Is Not Configured.")
        return {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(self, method, path, payload=None):
        response = self.session.request(method, f"{self.github_base_url}{path}", headers=self._github_headers(), json=payload or {}, timeout=self.timeout)
        if response.status_code >= 400:
            raise ProjectIntegrationProviderError(f"GitHub Request Failed With {response.status_code}: {response.text}")
        return response.json() if response.content else {}

    def create_repository(self, owner, name, private=True):
        dry_payload = {"dry_run": not self.live, "owner": owner, "name": name, "private": private, "full_name": f"{owner}/{name}" if owner else name}
        if not self.live:
            return dry_payload
        path = f"/orgs/{owner}/repos" if owner else "/user/repos"
        payload = self._request("POST", path, {"name": name, "private": private, "auto_init": True})
        return {
            "dry_run": False,
            "owner": owner or payload.get("owner", {}).get("login", ""),
            "name": payload.get("name", name),
            "private": payload.get("private", private),
            "full_name": payload.get("full_name", dry_payload["full_name"]),
            "default_branch": payload.get("default_branch", "main"),
            "external_id": str(payload.get("id", "")),
            "external_url": payload.get("html_url", ""),
        }

    def assign_repository_access(self, repository_full_name, github_username, permission="push"):
        if not self.live:
            return {"dry_run": True, "repository": repository_full_name, "github_username": github_username, "permission": permission}
        payload = self._request("PUT", f"/repos/{repository_full_name}/collaborators/{github_username}", {"permission": permission})
        return {"dry_run": False, "repository": repository_full_name, "github_username": github_username, "permission": permission, "invitation_id": payload.get("id")}

    def upload_document(self, project_name, title, content_type="application/octet-stream"):
        return {"dry_run": not self.live, "project_name": project_name, "title": title, "content_type": content_type}

    def fetch_repository_commits(self, repository_full_name, since_days=10, branch=""):
        since = (timezone.now() - timedelta(days=int(since_days or 10))).isoformat().replace("+00:00", "Z")
        params = {"since": since, "per_page": 100}
        if branch:
            params["sha"] = branch
        path = f"/repos/{repository_full_name}/commits?{urlencode(params)}"
        if not self.live:
            return {"dry_run": True, "repository": repository_full_name, "since": since, "commits": []}
        return {"dry_run": False, "repository": repository_full_name, "since": since, "commits": self._request("GET", path)}

    def fetch_pull_requests(self, repository_full_name, state="all", per_page=50):
        path = f"/repos/{repository_full_name}/pulls?{urlencode({'state': state, 'per_page': per_page})}"
        if not self.live:
            return {"dry_run": True, "repository": repository_full_name, "pull_requests": []}
        return {"dry_run": False, "repository": repository_full_name, "pull_requests": self._request("GET", path)}