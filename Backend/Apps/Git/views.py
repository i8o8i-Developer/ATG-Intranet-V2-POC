from Backend.Apps.Git.models import GitActivitySnapshot, GitRepositorySnapshot, RepositoryUtilityRequest
from Backend.Apps.Git.serializers import (
    CollaboratorAccessSerializer,
    GitActivitySnapshotSerializer,
    GitRepositorySnapshotSerializer,
    GitRepositorySyncSerializer,
    RepositoryUtilityRequestSerializer,
)
from Backend.Apps.Git.services import GitRepositoryService, GitUtilityService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


class GitRepositorySnapshotViewSet(TenantScopedModelViewSet):
    queryset = GitRepositorySnapshot.objects.select_related("tenant", "workspace").all()
    serializer_class = GitRepositorySnapshotSerializer

    @action(detail=True, methods=["post"], url_path="queue-request")
    def queue_request(self, request, pk=None):
        result = GitUtilityService.queue_request(
            self.get_tenant_context(),
            request.data.get("request_type", "InspectRepository"),
            payload=request.data.get("payload") or {},
            repository=self.get_object(),
        )
        return self.service_response(result, RepositoryUtilityRequestSerializer)

    @action(detail=False, methods=["post"], url_path="sync-github")
    def sync_github(self, request):
        serializer = GitRepositorySyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = GitRepositoryService.sync_github_repositories(self.get_tenant_context(), live=serializer.validated_data.get("live", False))
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=False, methods=["post"], url_path="request-collaborator")
    def request_collaborator(self, request):
        serializer = CollaboratorAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = GitRepositoryService.request_collaborator_access(
            self.get_tenant_context(),
            employee_id=data.get("employee"),
            github_username=data.get("github_username", ""),
            repository_ids=data.get("repositories"),
            live=data.get("live", False),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=False, methods=["post"], url_path="deactivate-collaborator")
    def deactivate_collaborator(self, request):
        serializer = CollaboratorAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = GitRepositoryService.deactivate_collaborator(
            self.get_tenant_context(),
            employee_id=data.get("employee"),
            github_username=data.get("github_username", ""),
            repository_ids=data.get("repositories"),
            live=data.get("live", False),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class GitActivitySnapshotViewSet(TenantScopedModelViewSet):
    queryset = GitActivitySnapshot.objects.select_related("tenant", "workspace", "repository").all()
    serializer_class = GitActivitySnapshotSerializer


class RepositoryUtilityRequestViewSet(TenantScopedModelViewSet):
    queryset = RepositoryUtilityRequest.objects.select_related("tenant", "workspace", "repository", "requested_by").all()
    serializer_class = RepositoryUtilityRequestSerializer


class LegacyGitDownloadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="LegacyGitDownload")
        tenant_hint = request.headers.get("X-Tenant-Id") or request.query_params.get("tenant")
        workspace_hint = request.headers.get("X-Workspace-Id") or request.query_params.get("workspace")
        tenant = Tenant.objects.filter(id=tenant_hint).first() if str(tenant_hint or "").isdigit() else Tenant.objects.filter(slug__iexact=str(tenant_hint or "")).first()
        workspace = Workspace.objects.filter(id=workspace_hint).first() if str(workspace_hint or "").isdigit() else Workspace.objects.filter(code__iexact=str(workspace_hint or "")).first()
        if not tenant:
            active_tenants = list(Tenant.objects.filter(status=Tenant.STATUS_ACTIVE).order_by("id")[:2])
            tenant = active_tenants[0] if len(active_tenants) == 1 else None
        if tenant and workspace and workspace.tenant_id != tenant.id:
            workspace = None
        if tenant and not workspace:
            workspace = Workspace.objects.filter(tenant=tenant).order_by("id").first()
        return TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="LegacyGitDownload")

    def _forbidden_response(self):
        return Response({"detail": "Request Failed. User Is Not An Admin."}, status=403)

    def get(self, request):
        if not request.user.is_superuser:
            return self._forbidden_response()
        result = GitRepositoryService.sync_github_repositories(self.get_context(request), live=False)
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    def post(self, request):
        if not request.user.is_superuser:
            return self._forbidden_response()
        result = GitRepositoryService.sync_github_repositories(self.get_context(request), live=bool(request.data.get("live", False)))
        return Response(result.data if result.ok else result.errors, status=result.status_code)
