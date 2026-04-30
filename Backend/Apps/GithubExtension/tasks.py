from Backend.Apps.GithubExtension.services import GitHubBranchService


def create_branch_assignment(context, **kwargs):
    return GitHubBranchService.create_branch_assignment(context, **kwargs)


def update_branch_assignment(context, user_type, assignment_id, data=None):
    return GitHubBranchService.update_branch_assignment(context, user_type, assignment_id, data=data or {})


def list_branch_status(context, repo_name, branches):
    return GitHubBranchService.list_branch_status(context, repo_name, branches)