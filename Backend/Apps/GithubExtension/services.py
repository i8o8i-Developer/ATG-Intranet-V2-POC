from django.utils import timezone

from Backend.Apps.Git.utils import name_formatter
from Backend.Apps.GithubExtension.models import BranchReviewerAssignment, BranchTestingAssignment, GitHubRepository, RepositoryBranchStatus
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class GitHubBranchService:
    @staticmethod
    def update_branch_status(context, repository, branch_name, review_status=None, testing_status=None, metadata=None):
        branch_status, _created = RepositoryBranchStatus.objects.get_or_create(
            tenant=context.tenant,
            repository=repository,
            branch_name=branch_name,
            defaults={"workspace": context.workspace or repository.workspace, "updated_by": context.actor},
        )
        if review_status is not None:
            branch_status.review_status = review_status
        if testing_status is not None:
            branch_status.testing_status = testing_status
        if metadata:
            branch_status.metadata = metadata
        branch_status.updated_by = context.actor
        branch_status.save(update_fields=["review_status", "testing_status", "metadata", "updated_by", "updated_at"])
        return ServiceResult.success(branch_status)

    @staticmethod
    def repository_by_legacy_name(context, repo_name):
        if not repo_name:
            return None
        for repository in GitHubRepository.objects.filter(tenant=context.tenant):
            if repository.name == repo_name or name_formatter(repository.owner, repository.name) == repo_name:
                return repository
        return None

    @staticmethod
    def check_repository(context, repo_name):
        return ServiceResult.success({"exists": bool(GitHubBranchService.repository_by_legacy_name(context, repo_name)), "repoName": repo_name})

    @staticmethod
    def list_branch_status(context, repo_name, branches):
        repository = GitHubBranchService.repository_by_legacy_name(context, repo_name)
        if not repository:
            return ServiceResult.failure({"repository": "Repository not found."}, status_code=404)
        rows = []
        for branch_name in branches:
            status_row, _created = RepositoryBranchStatus.objects.get_or_create(
                tenant=context.tenant,
                workspace=context.workspace or repository.workspace,
                repository=repository,
                branch_name=branch_name,
                defaults={"updated_by": context.actor},
            )
            rows.append(
                {
                    "id": status_row.id,
                    "name": status_row.branch_name,
                    "review_status": status_row.review_status,
                    "testing_status": status_row.testing_status,
                    "tester": list(BranchTestingAssignment.objects.filter(tenant=context.tenant, repository=repository, branch_name=branch_name).values("id", "status", "is_pass", "comment", "test_report_url")),
                    "reviewer": list(BranchReviewerAssignment.objects.filter(tenant=context.tenant, repository=repository, branch_name=branch_name).values("id", "status", "is_pass", "comment")),
                }
            )
        return ServiceResult.success(rows)

    @staticmethod
    def create_branch_assignment(context, repository_id=None, repo_name="", branch_name="", user_type="tester", employee_id=None, data=None):
        from Backend.Apps.Users.models import EmployeeProfile

        repository = GitHubRepository.objects.filter(tenant=context.tenant, id=repository_id).first() if repository_id else GitHubBranchService.repository_by_legacy_name(context, repo_name)
        if not repository:
            return ServiceResult.failure({"repository": "Repository not found."}, status_code=404)
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee profile is required."}, status_code=400)
        data = data or {}
        if user_type.lower() == "reviewer":
            assignment = BranchReviewerAssignment.objects.create(
                tenant=context.tenant,
                workspace=context.workspace or repository.workspace,
                repository=repository,
                branch_name=branch_name,
                reviewer=employee,
                status="Reviewed" if data.get("is_pass") else "Assigned",
                is_pass=data.get("is_pass", ""),
                is_claim=data.get("is_claim", False),
                comment=data.get("comment", ""),
                reviewed_at=timezone.now() if data.get("is_pass") else None,
                metadata=data.get("metadata", {}),
                created_by=context.actor,
                updated_by=context.actor,
            )
            GitHubBranchService.update_branch_status(context, repository, branch_name, review_status=assignment.is_pass or assignment.status)
            event_type = "GitHubBranchReviewerRecorded"
        else:
            assignment = BranchTestingAssignment.objects.create(
                tenant=context.tenant,
                workspace=context.workspace or repository.workspace,
                repository=repository,
                branch_name=branch_name,
                tester=employee,
                status="Tested" if data.get("is_pass") else "Pending",
                test_report_url=data.get("test_report_url", ""),
                is_pass=data.get("is_pass", ""),
                is_claim=data.get("is_claim", False),
                comment=data.get("comment", ""),
                tested_at=timezone.now() if data.get("is_pass") else None,
                result_payload=data.get("metadata", {}),
                created_by=context.actor,
                updated_by=context.actor,
            )
            GitHubBranchService.update_branch_status(context, repository, branch_name, testing_status=assignment.is_pass or assignment.status)
            event_type = "GitHubBranchTesterRecorded"
        OutboxService.publish(context, assignment.__class__.__name__, assignment.id, event_type, {"branch": branch_name, "repository": repository.id})
        return ServiceResult.success(assignment, status_code=201)

    @staticmethod
    def update_branch_assignment(context, user_type, assignment_id, data=None):
        data = data or {}
        model = BranchReviewerAssignment if user_type.lower() == "reviewer" else BranchTestingAssignment
        assignment = model.objects.filter(tenant=context.tenant, id=assignment_id).select_related("repository").first()
        if not assignment:
            return ServiceResult.failure({"assignment": "Branch assignment not found."}, status_code=404)
        for field in ["is_pass", "comment", "metadata"]:
            if field in data:
                setattr(assignment, field, data[field])
        if "is_claim" in data:
            assignment.is_claim = data["is_claim"]
        if hasattr(assignment, "test_report_url") and "test_report_url" in data:
            assignment.test_report_url = data["test_report_url"]
        if data.get("is_pass"):
            assignment.status = "Reviewed" if user_type.lower() == "reviewer" else "Tested"
            if hasattr(assignment, "reviewed_at"):
                assignment.reviewed_at = timezone.now()
            if hasattr(assignment, "tested_at"):
                assignment.tested_at = timezone.now()
        assignment.updated_by = context.actor
        assignment.save()
        if user_type.lower() == "reviewer":
            GitHubBranchService.update_branch_status(context, assignment.repository, assignment.branch_name, review_status=assignment.is_pass or assignment.status)
        else:
            GitHubBranchService.update_branch_status(context, assignment.repository, assignment.branch_name, testing_status=assignment.is_pass or assignment.status)
        return ServiceResult.success(assignment)
