from django import forms

from Backend.Apps.Git.models import GitActivitySnapshot, GitRepositorySnapshot, RepositoryUtilityRequest


class GitRepositorySnapshotForm(forms.ModelForm):
    class Meta:
        model = GitRepositorySnapshot
        fields = ["organization", "repository_name", "repository_full_name", "provider", "default_branch", "latest_commit_sha", "status", "metadata"]


class GitActivitySnapshotForm(forms.ModelForm):
    class Meta:
        model = GitActivitySnapshot
        fields = ["repository", "snapshot_date", "commit_count", "pull_request_count", "review_count", "metrics"]


class RepositoryUtilityRequestForm(forms.ModelForm):
    class Meta:
        model = RepositoryUtilityRequest
        fields = ["repository", "requested_by", "request_type", "status", "payload", "result_payload", "failure_reason"]