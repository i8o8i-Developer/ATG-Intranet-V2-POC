from Backend.Apps.Git.services import GitRepositoryService


def sync_github_repositories(context, live=False):
    return GitRepositoryService.sync_github_repositories(context, live=live)


def request_collaborator_access(context, employee_id=None, github_username="", repository_ids=None, live=False):
    return GitRepositoryService.request_collaborator_access(context, employee_id=employee_id, github_username=github_username, repository_ids=repository_ids, live=live)


def deactivate_collaborator(context, employee_id=None, github_username="", repository_ids=None, live=False):
    return GitRepositoryService.deactivate_collaborator(context, employee_id=employee_id, github_username=github_username, repository_ids=repository_ids, live=live)