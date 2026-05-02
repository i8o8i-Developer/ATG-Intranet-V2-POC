from Backend.Apps.GithubExtension.models import BranchReviewerAssignment, BranchTestingAssignment, GitHubRepository, RepositoryBranchStatus
from Backend.Apps.GithubExtension.serializers import (
    BranchAssignmentCreateSerializer,
    BranchAssignmentUpdateSerializer,
    BranchStatusQuerySerializer,
    BranchReviewerAssignmentSerializer,
    BranchTestingAssignmentSerializer,
    GitHubRepositorySerializer,
    LegacyGitHubTokenObtainPairSerializer,
    LegacyGitHubTokenRefreshSerializer,
    RepositoryBranchStatusSerializer,
)
from Backend.Apps.GithubExtension.services import GitHubBranchService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


class GitHubRepositoryViewSet(TenantScopedModelViewSet):
    queryset = GitHubRepository.objects.select_related("tenant", "workspace", "project").all()
    serializer_class = GitHubRepositorySerializer

    @action(detail=True, methods=["post"], url_path="update-branch-status")
    def update_branch_status(self, request, pk=None):
        result = GitHubBranchService.update_branch_status(
            self.get_tenant_context(),
            self.get_object(),
            request.data.get("branch_name", "main"),
            review_status=request.data.get("review_status", "Unknown"),
            testing_status=request.data.get("testing_status", "Unknown"),
            metadata=request.data.get("metadata") or {},
        )
        return self.service_response(result, RepositoryBranchStatusSerializer)

    @action(detail=True, methods=["post"], url_path="assign-branch-user")
    def assign_branch_user(self, request, pk=None):
        serializer = BranchAssignmentCreateSerializer(data={**request.data, "repository": pk})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = GitHubBranchService.create_branch_assignment(
            self.get_tenant_context(),
            repository_id=pk,
            branch_name=data["branch_name"],
            user_type=data.get("user_type", "tester"),
            employee_id=data.get("employee"),
            data=data,
        )
        response_serializer = BranchReviewerAssignmentSerializer if data.get("user_type") == "reviewer" else BranchTestingAssignmentSerializer
        return self.service_response(result, response_serializer)


class BranchReviewerAssignmentViewSet(TenantScopedModelViewSet):
    queryset = BranchReviewerAssignment.objects.select_related("tenant", "workspace", "repository", "reviewer").all()
    serializer_class = BranchReviewerAssignmentSerializer


class BranchTestingAssignmentViewSet(TenantScopedModelViewSet):
    queryset = BranchTestingAssignment.objects.select_related("tenant", "workspace", "repository", "tester").all()
    serializer_class = BranchTestingAssignmentSerializer


class RepositoryBranchStatusViewSet(TenantScopedModelViewSet):
    queryset = RepositoryBranchStatus.objects.select_related("tenant", "workspace", "repository").all()
    serializer_class = RepositoryBranchStatusSerializer


class GithubExtensionLegacyMixin:
    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="GithubExtensionLegacyAPI")
        tenant_hint = request.headers.get("X-Tenant-Id") or request.query_params.get("tenant") or request.data.get("tenant")
        workspace_hint = request.headers.get("X-Workspace-Id") or request.query_params.get("workspace") or request.data.get("workspace")
        tenant = Tenant.objects.filter(id=tenant_hint).first() if str(tenant_hint or "").isdigit() else Tenant.objects.filter(slug__iexact=str(tenant_hint or "")).first()
        workspace = Workspace.objects.filter(id=workspace_hint).first() if str(workspace_hint or "").isdigit() else Workspace.objects.filter(code__iexact=str(workspace_hint or "")).first()
        if not tenant:
            active_tenants = list(Tenant.objects.filter(status=Tenant.STATUS_ACTIVE).order_by("id")[:2])
            tenant = active_tenants[0] if len(active_tenants) == 1 else None
        if tenant and workspace and workspace.tenant_id != tenant.id:
            workspace = None
        if tenant and not workspace:
            workspace = Workspace.objects.filter(tenant=tenant).order_by("id").first()
        return TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="GithubExtensionLegacyAPI")


class RepoBranchStatusAPIView(GithubExtensionLegacyMixin, APIView):
    def get(self, request):
        serializer = BranchStatusQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        branches = [item.strip() for item in data.get("list", "").split(",") if item.strip()]
        result = GitHubBranchService.list_branch_status(self.get_context(request), data.get("name", ""), branches)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class PostBranchTesterOrReviewerAPIView(GithubExtensionLegacyMixin, APIView):
    def post(self, request):
        payload = {**request.data, "reponame": request.query_params.get("reponame", request.data.get("reponame", "")), "user_type": request.query_params.get("usertype", request.data.get("user_type", "tester"))}
        serializer = BranchAssignmentCreateSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = GitHubBranchService.create_branch_assignment(
            self.get_context(request),
            repository_id=data.get("repository"),
            repo_name=data.get("reponame", ""),
            branch_name=data["branch_name"],
            user_type=data.get("user_type", "tester"),
            employee_id=data.get("employee"),
            data=data,
        )
        return Response(result.data if isinstance(result.data, dict) else {"id": result.data.id, "status": result.data.status} if result.ok else result.errors, status=result.status_code)


class DetailBranchTesterOrReviewerAPIView(GithubExtensionLegacyMixin, APIView):
    def put(self, request, user_type, pk):
        serializer = BranchAssignmentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = GitHubBranchService.update_branch_assignment(self.get_context(request), user_type, pk, serializer.validated_data)
        return Response({"id": result.data.id, "status": result.data.status} if result.ok else result.errors, status=result.status_code)


class CheckRepositoryAPIView(GithubExtensionLegacyMixin, APIView):
    def get(self, request, repo_name):
        result = GitHubBranchService.check_repository(self.get_context(request), repo_name)
        message = "The Repo Name Is Valid" if result.data["exists"] else "The Repo Name Does Not Found"
        return Response({"Message": message, **result.data}, status=result.status_code)


class LegacyGitHubTokenObtainPairView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LegacyGitHubTokenObtainPairSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class LegacyGitHubTokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LegacyGitHubTokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
