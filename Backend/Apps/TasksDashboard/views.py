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
from Backend.Apps.TasksDashboard.services import ClickUpSyncService, EODService, ManagerAbbreviationService, WorkManagementService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


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
        result = EODService.deliver_daily_summary(self.get_tenant_context(), status_date=request.data.get("status_date"), channel_name=request.data.get("channel_name", "daily-eod"), live=request.data.get("live", False))
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
            return Response({"employee": "Employee profile not found."}, status=404)
        result = ManagerAbbreviationService.generate(self.get_tenant_context(), employee)
        return self.service_response(result, ManagerAbbreviationSerializer)
