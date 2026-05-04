from django.conf import settings


class GitHubProvider:
    def __init__(self, token=None, client=None, repositories=None, live=False):
        self.token = token or getattr(settings, "GITHUB_ACCESS_TOKEN", "")
        self.client = client
        self.repositories = repositories
        self.live = live

    def get_client(self):
        if self.client:
            return self.client
        if not self.live or not self.token:
            return None
        from github import Github

        self.client = Github(self.token)
        return self.client

    def list_repositories(self):
        if self.repositories is not None:
            return self.repositories
        client = self.get_client()
        if not client:
            return []
        user = client.get_user()
        rows = []
        for repository in user.get_repos():
            organization = getattr(getattr(repository, "organization", None), "login", "") or getattr(getattr(repository, "owner", None), "login", "atg")
            rows.append(
                {
                    "organization": organization,
                    "name": repository.name,
                    "default_branch": getattr(repository, "default_branch", ""),
                    "latest_commit_sha": getattr(getattr(repository, "pushed_at", None), "isoformat", lambda: "")(),
                    "external_id": str(getattr(repository, "id", "")),
                    "external_url": getattr(repository, "html_url", ""),
                }
            )
        return rows

    def add_collaborator(self, organization, repository_name, github_username, permission="push", live=False):
        if not live:
            return {"dry_run": True, "action": "add_collaborator", "repository": f"{organization}/{repository_name}", "github_username": github_username, "permission": permission}
        repository = self._repo_object(organization, repository_name)
        repository.add_to_collaborators(github_username, permission=permission)
        return {"status": "sent", "repository": f"{organization}/{repository_name}", "github_username": github_username, "permission": permission}

    def remove_collaborator(self, organization, repository_name, github_username, live=False):
        if not live:
            return {"dry_run": True, "action": "remove_collaborator", "repository": f"{organization}/{repository_name}", "github_username": github_username}
        
        client = self.get_client()
        
        # Different handling for organization vs personal repos
        if organization in {"", "atg"}:
            # Personal repository - use remove_from_collaborators
            repository = client.get_user().get_repo(repository_name)
            repository.remove_from_collaborators(github_username)
        else:
            # Organization repository - use remove_outside_collaborator on org
            org_object = client.get_organization(organization)
            try:
                org_object.remove_outside_collaborator(github_username)
            except Exception:
                # Fallback to repository-level removal if org-level fails
                repository = org_object.get_repo(repository_name)
                repository.remove_from_collaborators(github_username)
        
        return {"status": "removed", "repository": f"{organization}/{repository_name}", "github_username": github_username}

    def _repo_object(self, organization, repository_name):
        client = self.get_client()
        if organization in {"", "atg"}:
            return client.get_user().get_repo(repository_name)
        return client.get_organization(organization).get_repo(repository_name)