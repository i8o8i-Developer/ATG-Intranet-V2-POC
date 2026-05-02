from Backend.Apps.TasksDashboard.models import ClickUpProjectMapping, DailyStatusEntry, ExternalWorkMapping, ManagerAbbreviation, SlackDeliveryMessage, SlackDeliveryThread, TaskActivity, WorkEntry, WorkItem
from Backend.Apps.TasksDashboard.serializers import (
    ClickUpProjectMappingSerializer,
    DailyStatusEntrySerializer,
    ExternalWorkMappingSerializer,
    ManagerAbbreviationSerializer,
    SlackDeliveryMessageSerializer,
    SlackDeliveryThreadSerializer,
    TaskActivitySerializer,
    WorkEntrySerializer,
    WorkItemSerializer,
)
from Backend.Apps.TasksDashboard.services import ClickUpSyncService, EODService, ManagerAbbreviationService, TasksDashboardLegacyService, WorkManagementService
from Backend.Apps.TasksDashboard.services.slack_eod import SlackEODService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult, TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


class WorkItemViewSet(TenantScopedModelViewSet):
    queryset = WorkItem.objects.select_related("tenant", "workspace", "project", "owner").all()
    serializer_class = WorkItemSerializer

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        result = WorkManagementService.transition_work_item(
            self.get_tenant_context(),
            pk,
            request.data.get("status", "Open"),
            message=request.data.get("message", ""),
        )
        return self.service_response(result, WorkItemSerializer)

    @action(detail=False, methods=["post"], url_path="create-work-item")
    def create_work_item(self, request):
        result = WorkManagementService.create_work_item(
            self.get_tenant_context(),
            request.data.get("title", "Untitled task"),
            project_id=request.data.get("project"),
            owner_id=request.data.get("owner"),
            parent_id=request.data.get("parent"),
            description=request.data.get("description", ""),
            priority=request.data.get("priority", "Normal"),
            bounty=request.data.get("bounty", 0),
            external_id=request.data.get("external_id", ""),
            provider=request.data.get("provider", ""),
        )
        return self.service_response(result, WorkItemSerializer)

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        result = WorkManagementService.reorder_work_items(self.get_tenant_context(), request.data.get("ordered_ids") or [])
        return self.service_response(result)

    @action(detail=True, methods=["post"], url_path="initialize-timer")
    def initialize_timer(self, request, pk=None):
        result = WorkManagementService.initialize_timer(self.get_tenant_context(), pk)
        return self.service_response(result, WorkItemSerializer)

    @action(detail=True, methods=["post"], url_path="log-work")
    def log_work(self, request, pk=None):
        result = WorkManagementService.log_work_entry(self.get_tenant_context(), pk, request.data.get("employee"), minutes=request.data.get("minutes", 0), summary=request.data.get("summary", ""), entry_date=request.data.get("entry_date"), entry_type=request.data.get("entry_type", "WorkLog"))
        return self.service_response(result, WorkEntrySerializer)


class WorkEntryViewSet(TenantScopedModelViewSet):
    queryset = WorkEntry.objects.select_related("tenant", "workspace", "work_item", "employee").all()
    serializer_class = WorkEntrySerializer


class TaskActivityViewSet(TenantScopedModelViewSet):
    queryset = TaskActivity.objects.select_related("tenant", "workspace", "work_item", "actor").all()
    serializer_class = TaskActivitySerializer


class DailyStatusEntryViewSet(TenantScopedModelViewSet):
    queryset = DailyStatusEntry.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = DailyStatusEntrySerializer

    @action(detail=False, methods=["post"], url_path="submit")
    def submit(self, request):
        result = EODService.submit_status(self.get_tenant_context(), request.data.get("employee"), summary=request.data.get("summary", ""), blockers=request.data.get("blockers", ""), next_plan=request.data.get("next_plan", ""), status_date=request.data.get("status_date"))
        return self.service_response(result, DailyStatusEntrySerializer)

    @action(detail=False, methods=["post"], url_path="deliver-slack-summary")
    def deliver_slack_summary(self, request):
        live = request.data.get("live") in [True, "true", "True", "1", 1]
        result = SlackEODService(self.get_tenant_context(), live=live).send_department_daily_summary(
            status_date=request.data.get("status_date"),
            channel_name=request.data.get("channel_name", "daily-eod"),
            department_id=request.data.get("department"),
        )
        return self.service_response(result)

    @action(detail=False, methods=["post"], url_path="send-slack-reminders")
    def send_slack_reminders(self, request):
        live = request.data.get("live") in [True, "true", "True", "1", 1]
        result = SlackEODService(self.get_tenant_context(), live=live).send_missing_eod_reminders(
            status_date=request.data.get("status_date"),
            channel_name=request.data.get("channel_name", "daily-eod"),
            department_id=request.data.get("department"),
        )
        return self.service_response(result)

    @action(detail=False, methods=["get"], url_path="missing")
    def missing(self, request):
        result = EODService.missing_eod_report(self.get_tenant_context(), status_date=request.query_params.get("status_date"))
        return self.service_response(result)


class SlackDeliveryThreadViewSet(TenantScopedModelViewSet):
    queryset = SlackDeliveryThread.objects.select_related("tenant", "workspace").all()
    serializer_class = SlackDeliveryThreadSerializer


class SlackDeliveryMessageViewSet(TenantScopedModelViewSet):
    queryset = SlackDeliveryMessage.objects.select_related("tenant", "workspace", "thread", "daily_status", "employee").all()
    serializer_class = SlackDeliveryMessageSerializer


class ExternalWorkMappingViewSet(TenantScopedModelViewSet):
    queryset = ExternalWorkMapping.objects.select_related("tenant", "workspace", "work_item").all()
    serializer_class = ExternalWorkMappingSerializer

    @action(detail=False, methods=["post"], url_path="clear-synced")
    def clear_synced(self, request):
        result = ClickUpSyncService.clear_synced_tasks(self.get_tenant_context(), provider=request.data.get("provider", "ClickUp"))
        return self.service_response(result)


class ClickUpProjectMappingViewSet(TenantScopedModelViewSet):
    queryset = ClickUpProjectMapping.objects.select_related("tenant", "workspace", "project").all()
    serializer_class = ClickUpProjectMappingSerializer

    @action(detail=True, methods=["post"], url_path="sync-tasks")
    def sync_tasks(self, request, pk=None):
        result = ClickUpSyncService.sync_tasks(self.get_tenant_context(), request.data.get("tasks") or [], project_mapping_id=pk)
        return self.service_response(result)


class ManagerAbbreviationViewSet(TenantScopedModelViewSet):
    queryset = ManagerAbbreviation.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = ManagerAbbreviationSerializer

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        from Backend.Apps.Users.models import EmployeeProfile

        employee = EmployeeProfile.objects.filter(tenant=self.get_tenant_context().tenant, id=request.data.get("employee")).first()
        if not employee:
            return Response({"employee": "Employee Profile Not Found."}, status=404)
        result = ManagerAbbreviationService.generate(self.get_tenant_context(), employee)
        return self.service_response(result, ManagerAbbreviationSerializer)


class TasksDashboardLegacyMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return ServiceResult.success(TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="TasksDashboardLegacyAPI"))
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
            return ServiceResult.failure({"tenant": "Tenant Context Is Required For TasksDashboard Request."}, status_code=400)
        return ServiceResult.success(TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="TasksDashboardLegacyAPI"))

    def with_context(self, request):
        result = self.get_context(request)
        if not result.ok:
            return None, Response(result.errors, status=result.status_code)
        return result.data, None

    def get_list_param(self, request, *keys):
        data = request.query_params if request.method == "GET" else request.data
        if hasattr(data, "getlist"):
            for key in keys:
                values = data.getlist(key)
                if values:
                    return values
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, str) and "," in value:
                return [item.strip() for item in value.split(",") if item.strip()]
            if value not in [None, ""]:
                return [value]
        return []


class DashboardLegacyAPIView(TasksDashboardLegacyMixin, APIView):
    def get(self, request, type):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TasksDashboardLegacyService.build_dashboard(context, type)
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    def post(self, request, type):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TasksDashboardLegacyService.build_dashboard(
            context,
            type,
            manager_ids=self.get_list_param(request, "overdue_managers[]", "overdue_managers"),
            project_names=self.get_list_param(request, "projects[]", "projects"),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class CheckLogUpdateLegacyAPIView(TasksDashboardLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TasksDashboardLegacyService.check_log_update(context)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class InitializeSyncTimerLegacyAPIView(TasksDashboardLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TasksDashboardLegacyService.initialize_sync_timer(context)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class UpdateClickupLegacyAPIView(TasksDashboardLegacyMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TasksDashboardLegacyService.update_clickup(context, tasks=request.data.get("tasks") or [], project_mapping_id=request.data.get("project_mapping_id"))
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class CheckTaskStatusLegacyAPIView(TasksDashboardLegacyMixin, APIView):
    def get(self, request, task_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TasksDashboardLegacyService.check_task_status(task_id)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class ReorderTaskLegacyAPIView(TasksDashboardLegacyMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TasksDashboardLegacyService.reorder_all_tasks(context)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class CreateActivityLegacyAPIView(TasksDashboardLegacyMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TasksDashboardLegacyService.create_missing_activities(context)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class EODReportLegacyAPIView(TasksDashboardLegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TasksDashboardLegacyService.eod_report(context, employee_id=request.query_params.get("user"), filter_type=request.query_params.get("filter", ""))
        return Response(result.data if result.ok else result.errors, status=result.status_code)
