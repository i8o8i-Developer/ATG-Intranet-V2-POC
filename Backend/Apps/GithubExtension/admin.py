from django.contrib import admin

from Backend.Apps.GithubExtension.models import BranchReviewerAssignment, BranchTestingAssignment, GitHubRepository, RepositoryBranchStatus


@admin.register(GitHubRepository)
class GitHubRepositoryAdmin(admin.ModelAdmin):
    list_display = ("owner", "name", "default_branch", "status", "tenant")
    list_filter = ("status", "tenant")
    search_fields = ("owner", "name")


@admin.register(BranchReviewerAssignment)
class BranchReviewerAssignmentAdmin(admin.ModelAdmin):
    list_display = ("repository", "branch_name", "reviewer", "status", "is_pass", "tenant")
    list_filter = ("status", "is_pass", "tenant")


@admin.register(BranchTestingAssignment)
class BranchTestingAssignmentAdmin(admin.ModelAdmin):
    list_display = ("repository", "branch_name", "tester", "status", "is_pass", "tenant")
    list_filter = ("status", "is_pass", "tenant")


@admin.register(RepositoryBranchStatus)
class RepositoryBranchStatusAdmin(admin.ModelAdmin):
    list_display = ("repository", "branch_name", "review_status", "testing_status", "tenant")
    list_filter = ("review_status", "testing_status", "tenant")