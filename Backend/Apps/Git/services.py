from django.utils import timezone

from Backend.Apps.Git.models import GitActivitySnapshot, GitRepositorySnapshot, RepositoryUtilityRequest
from Backend.Apps.Git.provider import GitHubProvider
from Backend.Apps.Git.utils import build_full_name, name_formatter, normalize_repository_payload
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class GitUtilityService:
    @staticmethod
    def queue_request(context, request_type, payload=None, repository=None):
        request = RepositoryUtilityRequest.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            repository=repository,
            request_type=request_type,
            payload=payload or {},
            created_by=context.actor,
        )
        return ServiceResult.success(request, status_code=201)


class GitRepositoryService:
    @staticmethod
    def sync_github_repositories(context, provider=None, live=False):
        from Backend.Apps.GithubExtension.models import GitHubRepository

        if not getattr(context, "tenant", None):
            return ServiceResult.failure({"tenant": "Tenant context is required for Git sync."}, status_code=400)
        provider = provider or GitHubProvider(live=live)
        rows = provider.list_repositories()
        synced = []
        for item in rows:
            payload = normalize_repository_payload(item)
            organization = payload["organization"]
            repository_name = payload["repository_name"]
            full_name = build_full_name(organization, repository_name)
            snapshot, _created = GitRepositorySnapshot.objects.update_or_create(
                tenant=context.tenant,
                provider="GitHub",
                organization=organization,
                repository_name=repository_name,
                defaults={
                    "workspace": context.workspace,
                    "repository_full_name": full_name,
                    "default_branch": payload.get("default_branch", ""),
                    "latest_commit_sha": payload.get("latest_commit_sha", ""),
                    "external_id": payload.get("external_id", ""),
                    "external_url": payload.get("external_url", ""),
                    "external_payload": item,
                    "metadata": {**payload.get("metadata", {}), "legacy_name": name_formatter(organization, repository_name)},
                    "updated_by": context.actor,
                },
            )
            GitHubRepository.objects.update_or_create(
                tenant=context.tenant,
                owner=organization,
                name=repository_name,
                defaults={
                    "workspace": context.workspace,
                    "default_branch": payload.get("default_branch", ""),
                    "external_id": payload.get("external_id", ""),
                    "external_url": payload.get("external_url", ""),
                    "external_payload": item,
                    "metadata": {"legacy_name": name_formatter(organization, repository_name), "source": "GitSync"},
                    "updated_by": context.actor,
                },
            )
            synced.append(snapshot.id)
        OutboxService.publish(context, "GitRepositorySnapshot", 0, "GitHubRepositoriesSynced", {"count": len(synced), "live": live})
        return ServiceResult.success({"count": len(synced), "repositoryIds": synced, "live": live}, status_code=201)

    @staticmethod
    def request_collaborator_access(context, employee_id=None, github_username="", repository_ids=None, live=False, provider=None):
        from Backend.Apps.Users.models import EmployeeProfile

        if not getattr(context, "tenant", None):
            return ServiceResult.failure({"tenant": "Tenant context is required for collaborator access."}, status_code=400)
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first() if employee_id else None
        github_username = github_username or (employee.github_username if employee else "")
        if not github_username:
            return ServiceResult.failure({"githubUsername": "GitHub username is required."}, status_code=400)
        repositories = GitRepositoryService._repository_queryset(context, repository_ids)
        provider = provider or GitHubProvider(live=live)
        requests = []
        for repository in repositories:
            result_payload = provider.add_collaborator(repository.organization, repository.repository_name, github_username, live=live)
            request = RepositoryUtilityRequest.objects.create(
                tenant=context.tenant,
                workspace=context.workspace or repository.workspace,
                repository=repository,
                requested_by=employee,
                request_type="CollaboratorAccess",
                status="Completed" if live else "Queued",
                payload={"github_username": github_username, "permission": "push", "live": live},
                result_payload=result_payload,
                completed_at=timezone.now() if live else None,
                created_by=context.actor,
                updated_by=context.actor,
            )
            requests.append(request.id)
        OutboxService.publish(context, "RepositoryUtilityRequest", 0, "GitCollaboratorAccessRequested", {"count": len(requests), "githubUsername": github_username, "live": live})
        return ServiceResult.success({"count": len(requests), "requestIds": requests}, status_code=201)

    @staticmethod
    def deactivate_collaborator(context, employee_id=None, github_username="", repository_ids=None, live=False, provider=None):
        from Backend.Apps.Users.models import EmployeeProfile

        if not getattr(context, "tenant", None):
            return ServiceResult.failure({"tenant": "Tenant context is required for collaborator deactivation."}, status_code=400)
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first() if employee_id else None
        github_username = github_username or (employee.github_username if employee else "")
        if not github_username:
            return ServiceResult.failure({"githubUsername": "GitHub username is required."}, status_code=400)
        provider = provider or GitHubProvider(live=live)
        requests = []
        for repository in GitRepositoryService._repository_queryset(context, repository_ids):
            result_payload = provider.remove_collaborator(repository.organization, repository.repository_name, github_username, live=live)
            request = RepositoryUtilityRequest.objects.create(
                tenant=context.tenant,
                workspace=context.workspace or repository.workspace,
                repository=repository,
                requested_by=employee,
                request_type="DeactivateCollaborator",
                status="Completed" if live else "Queued",
                payload={"github_username": github_username, "live": live},
                result_payload=result_payload,
                completed_at=timezone.now() if live else None,
                created_by=context.actor,
                updated_by=context.actor,
            )
            requests.append(request.id)
        OutboxService.publish(context, "RepositoryUtilityRequest", 0, "GitCollaboratorDeactivated", {"count": len(requests), "githubUsername": github_username, "live": live})
        return ServiceResult.success({"count": len(requests), "requestIds": requests}, status_code=201)

    @staticmethod
    def record_activity_snapshot(context, repository_id, snapshot_date, commit_count=0, pull_request_count=0, review_count=0, metrics=None):
        repository = GitRepositorySnapshot.objects.filter(tenant=context.tenant, id=repository_id).first()
        if not repository:
            return ServiceResult.failure({"repository": "Repository snapshot not found."}, status_code=404)
        snapshot, _created = GitActivitySnapshot.objects.update_or_create(
            tenant=context.tenant,
            repository=repository,
            snapshot_date=snapshot_date,
            defaults={
                "workspace": context.workspace or repository.workspace,
                "commit_count": commit_count,
                "pull_request_count": pull_request_count,
                "review_count": review_count,
                "metrics": metrics or {},
                "updated_by": context.actor,
            },
        )
        return ServiceResult.success(snapshot, status_code=201)

    @staticmethod
    def _repository_queryset(context, repository_ids=None):
        queryset = GitRepositorySnapshot.objects.filter(tenant=context.tenant, is_active=True)
        if repository_ids:
            queryset = queryset.filter(id__in=repository_ids)
        return queryset.order_by("organization", "repository_name")
