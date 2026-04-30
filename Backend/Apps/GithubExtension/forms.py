from django import forms

from Backend.Apps.GithubExtension.models import BranchReviewerAssignment, BranchTestingAssignment, GitHubRepository, RepositoryBranchStatus


class GitHubRepositoryForm(forms.ModelForm):
    class Meta:
        model = GitHubRepository
        fields = ["project", "owner", "name", "default_branch", "status", "metadata"]


class BranchReviewerAssignmentForm(forms.ModelForm):
    class Meta:
        model = BranchReviewerAssignment
        fields = ["repository", "branch_name", "reviewer", "status", "is_pass", "is_claim", "comment", "metadata"]


class BranchTestingAssignmentForm(forms.ModelForm):
    class Meta:
        model = BranchTestingAssignment
        fields = ["repository", "branch_name", "tester", "status", "test_report_url", "is_pass", "is_claim", "comment", "result_payload"]


class RepositoryBranchStatusForm(forms.ModelForm):
    class Meta:
        model = RepositoryBranchStatus
        fields = ["repository", "branch_name", "last_commit_sha", "review_status", "testing_status", "metadata"]