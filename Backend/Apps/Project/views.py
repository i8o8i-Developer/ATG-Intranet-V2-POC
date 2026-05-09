from django.utils import timezone

from Backend.Apps.Project.models import (
    ComplianceAssignment,
    ComplianceCampaign,
    DefaultCheckpoint,
    DeliveryAlert,
    DeliveryDocument,
    DeliveryMilestone,
    MilestoneComponent,
    ProjectContact,
    ProjectDelay,
    ProjectWorkspace,
    RepositoryLink,
    TeamAssignment,
)
from Backend.Apps.Project.serializers import (
    ComplianceAssignmentSerializer,
    ComplianceCampaignSerializer,
    DefaultCheckpointSerializer,
    DeliveryAlertSerializer,
    DeliveryDocumentSerializer,
    DeliveryMilestoneSerializer,
    MilestoneComponentSerializer,
    ProjectContactSerializer,
    ProjectDelaySerializer,
    ProjectWorkspaceSerializer,
    RepositoryLinkSerializer,
    TeamAssignmentSerializer,
)
from Backend.Apps.Project.services import ProjectDeliveryService
from Backend.Apps.TasksDashboard.serializers import ClickUpProjectMappingSerializer, WorkItemSerializer
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult, TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


class ProjectWorkspaceViewSet(TenantScopedModelViewSet):
    queryset = ProjectWorkspace.objects.select_related("tenant", "workspace").all()
    serializer_class = ProjectWorkspaceSerializer

    @action(detail=True, methods=["post"], url_path="raise-alert")
    def raise_alert(self, request, pk=None):
        result = ProjectDeliveryService.raise_delivery_alert(
            self.get_tenant_context(),
            pk,
            request.data.get("severity", "Info"),
            request.data.get("title", "Project alert"),
            description=request.data.get("description", ""),
            metadata=request.data.get("metadata") or {},
        )
        return self.service_response(result, DeliveryAlertSerializer)

    @action(detail=True, methods=["post"], url_path="create-default-milestones")
    def create_default_milestones(self, request, pk=None):
        result = ProjectDeliveryService.create_default_checkpoints(self.get_tenant_context(), pk)
        return self.service_response(result)

    @action(detail=True, methods=["post"], url_path="calculate-health")
    def calculate_health(self, request, pk=None):
        result = ProjectDeliveryService.calculate_health(self.get_tenant_context(), pk)
        return self.service_response(result)

    @action(detail=True, methods=["post"], url_path="add-member")
    def add_member(self, request, pk=None):
        result = ProjectDeliveryService.add_team_member(self.get_tenant_context(), pk, request.data.get("employee"), role=request.data.get("role", "Member"), allocation_percent=request.data.get("allocation_percent", 100))
        return self.service_response(result, TeamAssignmentSerializer)

    @action(detail=True, methods=["post"], url_path="create-repository")
    def create_repository(self, request, pk=None):
        result = ProjectDeliveryService.create_repository_link(self.get_tenant_context(), pk, request.data.get("name", ""), owner=request.data.get("owner", ""), provider=request.data.get("provider", "GitHub"), default_branch=request.data.get("default_branch", "main"), live=request.data.get("live", False))
        return self.service_response(result, RepositoryLinkSerializer)

    @action(detail=True, methods=["post"], url_path="record-document")
    def record_document(self, request, pk=None):
        result = ProjectDeliveryService.record_document(self.get_tenant_context(), pk, request.data.get("title", "Project document"), document_type=request.data.get("document_type", "General"), storage_reference=request.data.get("storage_reference", ""), file_id=request.data.get("file_id", ""))
        return self.service_response(result, DeliveryDocumentSerializer)

    @action(detail=True, methods=["post"], url_path="launch-compliance")
    def launch_compliance(self, request, pk=None):
        result = ProjectDeliveryService.launch_compliance_campaign(self.get_tenant_context(), pk, name=request.data.get("name", "Anti phishing assessment"), employee_ids=request.data.get("employee_ids") or [])
        return self.service_response(result)

    @action(detail=False, methods=["post"], url_path="daily-notifications")
    def daily_notifications(self, request):
        result = ProjectDeliveryService.daily_notifications(self.get_tenant_context())
        return self.service_response(result)


class ProjectContactViewSet(TenantScopedModelViewSet):
    queryset = ProjectContact.objects.select_related("tenant", "workspace", "project").all()
    serializer_class = ProjectContactSerializer


class DefaultCheckpointViewSet(TenantScopedModelViewSet):
    queryset = DefaultCheckpoint.objects.select_related("tenant", "workspace").all()
    serializer_class = DefaultCheckpointSerializer


class MilestoneComponentViewSet(TenantScopedModelViewSet):
    queryset = MilestoneComponent.objects.select_related("tenant", "workspace", "project").all()
    serializer_class = MilestoneComponentSerializer


class DeliveryMilestoneViewSet(TenantScopedModelViewSet):
    queryset = DeliveryMilestone.objects.select_related("tenant", "workspace", "project").all()
    serializer_class = DeliveryMilestoneSerializer

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        result = ProjectDeliveryService.mark_milestone_complete(
            self.get_tenant_context(),
            pk,
            completed_on=request.data.get("completed_on"),
        )
        return self.service_response(result, DeliveryMilestoneSerializer)


class TeamAssignmentViewSet(TenantScopedModelViewSet):
    queryset = TeamAssignment.objects.select_related("tenant", "workspace", "project", "employee").all()
    serializer_class = TeamAssignmentSerializer

    @action(detail=True, methods=["post"], url_path="accept-terms")
    def accept_terms(self, request, pk=None):
        result = ProjectDeliveryService.accept_terms(self.get_tenant_context(), pk)
        return self.service_response(result, TeamAssignmentSerializer)

    @action(detail=True, methods=["post"], url_path="remove")
    def remove(self, request, pk=None):
        result = ProjectDeliveryService.remove_team_member(self.get_tenant_context(), pk, reason=request.data.get("reason", ""))
        return self.service_response(result, TeamAssignmentSerializer)


class RepositoryLinkViewSet(TenantScopedModelViewSet):
    queryset = RepositoryLink.objects.select_related("tenant", "workspace", "project").all()
    serializer_class = RepositoryLinkSerializer

    @action(detail=True, methods=["post"], url_path="access")
    def access(self, request, pk=None):
        result = ProjectDeliveryService.update_repository_access(self.get_tenant_context(), pk, request.data.get("employee"), access_status=request.data.get("access_status", "AccessRequested"))
        return self.service_response(result, RepositoryLinkSerializer)


class DeliveryDocumentViewSet(TenantScopedModelViewSet):
    queryset = DeliveryDocument.objects.select_related("tenant", "workspace", "project").all()
    serializer_class = DeliveryDocumentSerializer

    @action(detail=True, methods=["post"], url_path="pin")
    def pin(self, request, pk=None):
        result = ProjectDeliveryService.pin_document(self.get_tenant_context(), pk, is_pinned=request.data.get("is_pinned", True))
        return self.service_response(result, DeliveryDocumentSerializer)


class DeliveryAlertViewSet(TenantScopedModelViewSet):
    queryset = DeliveryAlert.objects.select_related("tenant", "workspace", "project").all()
    serializer_class = DeliveryAlertSerializer


class ComplianceCampaignViewSet(TenantScopedModelViewSet):
    queryset = ComplianceCampaign.objects.select_related("tenant", "workspace", "project").all()
    serializer_class = ComplianceCampaignSerializer


class ComplianceAssignmentViewSet(TenantScopedModelViewSet):
    queryset = ComplianceAssignment.objects.select_related("tenant", "workspace", "campaign", "employee").all()
    serializer_class = ComplianceAssignmentSerializer

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        result = ProjectDeliveryService.complete_compliance_assignment(self.get_tenant_context(), pk, score=request.data.get("score", 0), evidence=request.data.get("evidence") or {})
        return self.service_response(result, ComplianceAssignmentSerializer)


class ProjectDelayViewSet(TenantScopedModelViewSet):
    queryset = ProjectDelay.objects.select_related("tenant", "workspace").all()
    serializer_class = ProjectDelaySerializer

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        delay = self.get_object()
        delay.status = "Resolved"
        delay.resolved_at = timezone.now()
        delay.resolved_by = request.user
        delay.save()
        return Response(ProjectDelaySerializer(delay).data)


class ProjectLegacyMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return ServiceResult.success(TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="ProjectLegacyAPI"))
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
        if not tenant:
            return ServiceResult.failure({"tenant": "Tenant Context Is Required For Project Request."}, status_code=400)
        return ServiceResult.success(TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="ProjectLegacyAPI"))

    def with_context(self, request):
        result = self.get_context(request)
        if not result.ok:
            return None, Response(result.errors, status=result.status_code)
        return result.data, None

    def to_response(self, result, serializer_class=None, many=False):
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        if serializer_class:
            return Response(serializer_class(result.data, many=many).data, status=result.status_code)
        return Response(result.data, status=result.status_code)

    @staticmethod
    def parse_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "y"}


class ProjectLegacyActionAPIView(ProjectLegacyMixin, APIView):
    action_name = ""
    response_serializer = None

    def get(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

    def handle(self, request, *args, **kwargs):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response

        action = self.action_name
        if action == "onboarding":
            result = ProjectDeliveryService.onboarding_summary(context)
        elif action == "terms":
            result = ProjectDeliveryService.project_terms(
                context,
                kwargs["project_id"],
                employee_id=request.data.get("employee") or request.query_params.get("employee"),
                accept=request.method == "POST" and self.parse_bool(request.data.get("accept"), True),
            )
            if request.method == "POST" and result.ok:
                result = ServiceResult.success({"project_id": kwargs["project_id"], "accepted": bool(result.data.terms_accepted_at), "assignment_id": result.data.id}, status_code=result.status_code)
        elif action == "dashboard":
            result = ProjectDeliveryService.project_dashboard(context, kwargs["pk"])
        elif action == "check_repo_exists":
            result = ProjectDeliveryService.check_repository_exists(
                context,
                name=request.data.get("name") or request.query_params.get("name", ""),
                project_id=request.data.get("project") or request.query_params.get("project"),
                full_name=request.data.get("full_name") or request.query_params.get("full_name", ""),
            )
        elif action == "create_repo":
            result = ProjectDeliveryService.create_repository_link(
                context,
                request.data.get("project") or request.data.get("project_id"),
                request.data.get("name", ""),
                owner=request.data.get("owner", ""),
                provider=request.data.get("provider", "GitHub"),
                default_branch=request.data.get("default_branch", "main"),
                live=self.parse_bool(request.data.get("live"), False),
            )
        elif action == "assign_repo":
            result = ProjectDeliveryService.update_repository_access(context, request.data.get("repository_id"), request.data.get("employee") or request.data.get("member_id"), access_status=request.data.get("access_status", "AccessRequested"))
        elif action == "revoke_repo":
            result = ProjectDeliveryService.update_repository_access(context, request.data.get("repository_id"), request.data.get("employee") or request.data.get("member_id"), access_status="Revoked")
        elif action == "add_member":
            result = ProjectDeliveryService.add_team_member(context, request.data.get("project") or request.data.get("project_id"), request.data.get("employee") or request.data.get("member_id"), role=request.data.get("role", "Member"), allocation_percent=request.data.get("allocation_percent", 100))
        elif action == "remove_member":
            assignment = TeamAssignment.objects.filter(tenant=context.tenant, project_id=request.data.get("project") or request.data.get("project_id"), employee_id=request.data.get("employee") or request.data.get("member_id")).first()
            result = ProjectDeliveryService.remove_team_member(context, assignment.id if assignment else None, reason=request.data.get("reason", "")) if assignment else ServiceResult.failure({"assignment": "Team Assignment Not Found."}, status_code=404)
        elif action == "add_member_back":
            result = ProjectDeliveryService.add_member_back(context, request.data.get("project") or request.data.get("project_id"), request.data.get("employee") or request.data.get("member_id"))
        elif action == "replace_member":
            result = ProjectDeliveryService.replace_member(context, request.data.get("project") or request.data.get("project_id"), request.data.get("old_employee") or request.data.get("old_member_id"), request.data.get("new_employee") or request.data.get("new_member_id"), role=request.data.get("role", "Member"))
        elif action == "mark_absent":
            result = ProjectDeliveryService.mark_absent(context, request.data.get("project") or request.data.get("project_id"), request.data.get("employee") or request.data.get("member_id"), is_absent=self.parse_bool(request.data.get("is_absent"), True), absent_reason=request.data.get("absent_reason", ""))
        elif action == "update_details":
            result = ProjectDeliveryService.update_project_details(context, request.data.get("project") or request.data.get("project_id"), request.data)
        elif action == "update_milestone":
            result = ProjectDeliveryService.update_milestone_details(context, request.data.get("milestone_id") or request.data.get("id"), request.data)
        elif action == "notifications_read":
            result = ProjectDeliveryService.mark_notifications_read(context, project_id=request.data.get("project") or request.data.get("project_id"))
        elif action == "get_user_organizations":
            result = ProjectDeliveryService.get_user_organizations(context)
        elif action == "get_user_repo":
            result = ProjectDeliveryService.get_user_repositories(context, kwargs["member_id"], kwargs["project_id"])
        elif action == "days_left":
            result = ProjectDeliveryService.get_days_left(context, kwargs["project_id"])
        elif action == "alerts":
            result = ProjectDeliveryService.get_alerts(context, kwargs["project_id"])
        elif action == "update_git":
            result = ProjectDeliveryService.sync_repository_activity(context, live=self.parse_bool(request.data.get("live") or request.query_params.get("live"), False), since_days=request.data.get("since_days") or request.query_params.get("since_days", 10))
        elif action == "cleanup_git":
            result = ProjectDeliveryService.cleanup_repository_access(context)
        elif action == "extract_milestones":
            result = ProjectDeliveryService.extract_legacy_milestones(context, project_id=request.data.get("project_id") or request.query_params.get("project_id"))
        elif action == "create_clickup_mapping":
            result = ProjectDeliveryService.upsert_clickup_mapping(context, request.data.get("project") or request.data.get("project_id"), external_id=request.data.get("external_id", ""), project_name=request.data.get("project_name", ""), space_id=request.data.get("space_id", ""), list_id=request.data.get("list_id", ""))
        elif action == "add_task":
            result = ProjectDeliveryService.add_task(context, request.data.get("project") or request.data.get("project_id"), request.data.get("title", "Untitled task"), owner_id=request.data.get("owner") or request.data.get("employee"), parent_id=request.data.get("parent"), description=request.data.get("description", ""), priority=request.data.get("priority", "Normal"), bounty=request.data.get("bounty", 0))
        elif action == "update_task":
            result = ProjectDeliveryService.update_task(context, request.data.get("task_id") or request.data.get("id"), request.data)
        elif action == "delete_task":
            result = ProjectDeliveryService.delete_task(context, request.data.get("task_id") or request.data.get("id"))
        elif action == "task_detail":
            result = ProjectDeliveryService.task_detail(context, kwargs["pk"])
        elif action == "save_task_link":
            result = ProjectDeliveryService.save_task_link(context, request.data.get("task_id") or request.data.get("id"), request.data.get("url") or request.data.get("link", ""))
        elif action == "delete_item":
            result = ProjectDeliveryService.delete_task(context, request.data.get("task_id") or request.data.get("id"))
        elif action == "link_prs_to_tasks":
            result = ProjectDeliveryService.link_pull_requests_to_tasks(context, live=self.parse_bool(request.data.get("live") or request.query_params.get("live"), False))
        elif action == "rename_task":
            result = ProjectDeliveryService.update_task(context, kwargs["task_id"], {"title": request.data.get("title", "")})
        elif action == "assign_assignee":
            result = ProjectDeliveryService.assign_assignee(context, request.data.get("task_id") or request.data.get("id"), request.data.get("employee") or request.data.get("assignee"))
        elif action == "update_priority":
            result = ProjectDeliveryService.update_task(context, request.data.get("task_id") or request.data.get("id"), {"priority": request.data.get("priority", "Normal")})
        elif action == "update_type":
            result = ProjectDeliveryService.update_task(context, kwargs["task_id"], {"task_type": request.data.get("task_type") or request.data.get("type")})
        elif action == "update_description":
            result = ProjectDeliveryService.update_task(context, kwargs["task_id"], {"description": request.data.get("description", "")})
        elif action == "update_bounty":
            result = ProjectDeliveryService.update_task(context, request.data.get("task_id") or request.data.get("id"), {"bounty": request.data.get("bounty", 0)})
        elif action == "update_duedate":
            result = ProjectDeliveryService.update_task(context, request.data.get("task_id") or request.data.get("id"), {"due_at": request.data.get("due_at") or request.data.get("due_date")})
        elif action == "update_task_order":
            result = ProjectDeliveryService.update_task_order(context, request.data.get("ordered_ids") or [])
        elif action == "update_subtask_parent":
            result = ProjectDeliveryService.update_subtask_parent(context, request.data.get("task_id") or request.data.get("id"), request.data.get("parent_id"))
        elif action == "update_subtask_status":
            result = ProjectDeliveryService.update_subtask_status(context, kwargs["subtask_id"], request.data.get("status", "Completed"))
        elif action == "upload_project_docs":
            result = ProjectDeliveryService.upload_project_document(context, request.data.get("project") or request.data.get("project_id"), request.data.get("title", "Project document"), document_type=request.data.get("document_type", "General"), storage_reference=request.data.get("storage_reference", ""), file_id=request.data.get("file_id", ""), metadata=request.data.get("metadata"))
        elif action == "create_document":
            result = ProjectDeliveryService.upload_project_document(context, request.data.get("project") or request.data.get("project_id"), request.data.get("title", "Document"), document_type=request.data.get("document_type", "General"), storage_reference=request.data.get("storage_reference", "generated"), file_id=request.data.get("file_id", ""))
        elif action == "get_file_name":
            result = ProjectDeliveryService.get_file_name(context, request.data.get("file_id") or request.query_params.get("file_id", ""))
        elif action == "add_new_link":
            result = ProjectDeliveryService.record_project_link(context, request.data.get("project") or request.data.get("project_id"), request.data.get("title", "Project link"), request.data.get("url", ""), link_type="Link")
        elif action == "add_kt_link":
            result = ProjectDeliveryService.record_project_link(context, request.data.get("project") or request.data.get("project_id"), request.data.get("title", "KT link"), request.data.get("url", ""), link_type="KT")
        elif action == "delete_project_document":
            result = ProjectDeliveryService.delete_project_document(context, request.data.get("document_id") or request.data.get("id"))
        elif action == "edit_project_document":
            result = ProjectDeliveryService.edit_project_document(context, request.data.get("document_id") or request.data.get("id"), title=request.data.get("title", ""), storage_reference=request.data.get("storage_reference", ""), metadata=request.data.get("metadata"))
        elif action == "toggle_pin_document":
            result = ProjectDeliveryService.pin_document(context, request.data.get("document_id") or request.data.get("id"), is_pinned=self.parse_bool(request.data.get("is_pinned"), True))
        elif action == "update_hat":
            result = ProjectDeliveryService.update_assignment_hat(context, request.data.get("project") or request.data.get("project_id"), request.data.get("employee") or request.data.get("memberId") or request.data.get("member_id"), hat_type=request.data.get("hatType") or request.data.get("hat_type") or "Member")
        elif action == "remove_hat":
            result = ProjectDeliveryService.update_assignment_hat(context, request.data.get("project") or request.data.get("project_id"), request.data.get("employee") or request.data.get("memberId") or request.data.get("member_id"), hat_type="Member")
        elif action == "delete_clickup_tasks":
            result = ProjectDeliveryService.detach_clickup_tasks(context, kwargs["project_id"])
        elif action == "relink_clickup_tasks":
            result = ProjectDeliveryService.relink_clickup_tasks(context, kwargs["project_id"], kwargs["clickup_name"])
        elif action == "send_anti_phishing_assessment":
            result = ProjectDeliveryService.send_anti_phishing_assessment(context, request.data.get("project") or request.data.get("project_id"), employee_ids=request.data.get("employee_ids") or [], name=request.data.get("name", "Anti Phishing Assessment"))
        elif action == "anti_phishing_reports":
            result = ProjectDeliveryService.anti_phishing_reports(context, project_id=request.query_params.get("project_id") or request.data.get("project_id"))
        elif action == "add_delay":
            result = ProjectDeliveryService.add_delay(context, request.data.get("milestone_id"), delayed_days=request.data.get("delayed_days", 1))
        elif action == "get_items":
            result = ProjectDeliveryService.get_items(context, project_id=request.query_params.get("project_id") or request.data.get("project_id"))
        elif action == "daily_notifications":
            result = ProjectDeliveryService.daily_notifications(context)
        else:
            result = ServiceResult.failure({"action": "Unsupported Project Compatibility Action."}, status_code=400)

        return self.to_response(result, self.response_serializer)


class AntiPhishingAssessmentLegacyAPIView(APIView):
    permission_classes = []

    def get(self, request, token):
        assignment = ComplianceAssignment.objects.filter(token=token).select_related("campaign", "campaign__project").first()
        if not assignment:
            return Response({"assignment": "Compliance Assignment Not Found."}, status=404)
        return Response(
            {
                "token": token,
                "status": assignment.status,
                "campaign": assignment.campaign.name,
                "project_id": assignment.campaign.project_id,
                "employee_id": assignment.employee_id,
            },
            status=200,
        )

    def post(self, request, token):
        assignment = ComplianceAssignment.objects.filter(token=token).select_related("campaign", "campaign__project", "tenant", "workspace").first()
        if not assignment:
            return Response({"assignment": "Compliance Assignment Not Found."}, status=404)
        context = TenantContext(tenant=assignment.tenant, workspace=assignment.workspace, actor=request.user if request.user.is_authenticated else None, source="ProjectAntiPhishingToken")
        result = ProjectDeliveryService.complete_compliance_by_token(context, token, score=request.data.get("score", 0), evidence=request.data.get("evidence") or {})
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        return Response(ComplianceAssignmentSerializer(result.data).data, status=result.status_code)
