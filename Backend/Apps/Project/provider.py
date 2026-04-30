class ProjectIntegrationProvider:
    def __init__(self, live=False):
        self.live = live

    def create_repository(self, owner, name, private=True):
        return {"dry_run": not self.live, "owner": owner, "name": name, "private": private, "full_name": f"{owner}/{name}" if owner else name}

    def assign_repository_access(self, repository_full_name, github_username, permission="push"):
        return {"dry_run": not self.live, "repository": repository_full_name, "github_username": github_username, "permission": permission}

    def upload_document(self, project_name, title, content_type="application/octet-stream"):
        return {"dry_run": not self.live, "project_name": project_name, "title": title, "content_type": content_type}