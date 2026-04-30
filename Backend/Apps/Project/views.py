from Backend.Apps.Project.models import (
    ComplianceAssignment,
    ComplianceCampaign,
    DefaultCheckpoint,
    DeliveryAlert,
    DeliveryDocument,
    DeliveryMilestone,
    MilestoneComponent,
    ProjectContact,
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
    ProjectWorkspaceSerializer,
    RepositoryLinkSerializer,
    TeamAssignmentSerializer,
)
from Backend.Apps.Project.services import ProjectDeliveryService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action


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
