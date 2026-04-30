from django.contrib import admin

from Backend.Apps.Git.models import GitActivitySnapshot, GitRepositorySnapshot, RepositoryUtilityRequest


@admin.register(GitRepositorySnapshot)
class GitRepositorySnapshotAdmin(admin.ModelAdmin):
    list_display = ("repository_full_name", "provider", "status", "tenant", "updated_at")
    list_filter = ("provider", "status", "tenant")
    search_fields = ("organization", "repository_name", "repository_full_name")


@admin.register(GitActivitySnapshot)
class GitActivitySnapshotAdmin(admin.ModelAdmin):
    list_display = ("repository", "snapshot_date", "commit_count", "pull_request_count", "review_count", "tenant")
    list_filter = ("tenant", "snapshot_date")


@admin.register(RepositoryUtilityRequest)
class RepositoryUtilityRequestAdmin(admin.ModelAdmin):
    list_display = ("request_type", "repository", "requested_by", "status", "tenant", "created_at")
    list_filter = ("request_type", "status", "tenant")