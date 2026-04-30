from Backend.Apps.Banao.models import AuditArtifact, LeadAccount, LeadActivity, LeadContact, LeadNote, LeadTag, LeadTest, ProposalArtifact, WorkflowStatusHistory, WorkflowTransition
from Backend.Apps.Banao.serializers import (
    AuditArtifactSerializer,
    LeadCaptureSerializer,
    LeadAccountSerializer,
    LeadActivitySerializer,
    LeadContactSerializer,
    LeadNoteCreateSerializer,
    LeadNoteSerializer,
    LeadTagSerializer,
    LeadTestCreateSerializer,
    LeadTestSerializer,
    ProposalArtifactSerializer,
    WorkflowActionSerializer,
    WorkflowStatusHistorySerializer,
    WorkflowTransitionSerializer,
)
from Backend.Apps.Banao.services import LeadWorkflowService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


class LeadTagViewSet(TenantScopedModelViewSet):
    queryset = LeadTag.objects.select_related("tenant", "workspace").all()
    serializer_class = LeadTagSerializer


class LeadAccountViewSet(TenantScopedModelViewSet):
    queryset = LeadAccount.objects.select_related("tenant", "workspace", "owner").prefetch_related("tags").all()
    serializer_class = LeadAccountSerializer

    @action(detail=True, methods=["post"], url_path="move-stage")
    def move_stage(self, request, pk=None):
        result = LeadWorkflowService.move_stage(
            self.get_tenant_context(),
            pk,
            request.data.get("to_stage", "New"),
            reason=request.data.get("reason", ""),
        )
        return self.service_response(result, LeadAccountSerializer)

    @action(detail=False, methods=["post"], url_path="capture")
    def capture(self, request):
        serializer = LeadCaptureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = LeadWorkflowService.capture_lead(
            self.get_tenant_context(),
            data["company_name"],
            source=data.get("source", ""),
            priority=data.get("priority", "Normal"),
            owner_id=data.get("owner"),
            estimated_value=data.get("estimated_value", 0),
            currency=data.get("currency", "INR"),
            contact_name=data.get("contact_name", ""),
            contact_email=data.get("contact_email", ""),
            contact_phone=data.get("contact_phone", ""),
            metadata=data.get("metadata", {}),
        )
        return self.service_response(result, LeadAccountSerializer)

    @action(detail=True, methods=["post"], url_path="add-note")
    def add_note(self, request, pk=None):
        serializer = LeadNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = LeadWorkflowService.add_note(self.get_tenant_context(), pk, data["body"], title=data.get("title", ""), author_id=data.get("author"), metadata=data.get("metadata", {}))
        return self.service_response(result, LeadNoteSerializer)

    @action(detail=True, methods=["post"], url_path="add-test")
    def add_test(self, request, pk=None):
        serializer = LeadTestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = LeadWorkflowService.add_test(self.get_tenant_context(), pk, data["title"], status=data.get("status", "Pending"), score=data.get("score", 0), due_at=data.get("due_at"), metadata=data.get("metadata", {}))
        return self.service_response(result, LeadTestSerializer)

    @action(detail=True, methods=["post"], url_path="send-to-bbd")
    def send_to_bbd(self, request, pk=None):
        serializer = WorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = LeadWorkflowService.send_to_bbd(self.get_tenant_context(), pk, notes=serializer.validated_data.get("notes", {}))
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=True, methods=["post"], url_path="send-audit")
    def send_audit(self, request, pk=None):
        serializer = WorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = LeadWorkflowService.send_audit(self.get_tenant_context(), pk, notes=serializer.validated_data.get("notes", {}))
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=True, methods=["post"], url_path="offer-template")
    def offer_template(self, request, pk=None):
        result = LeadWorkflowService.create_offer_template(self.get_tenant_context(), pk, amount=request.data.get("amount"), notes=request.data.get("notes") or {})
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=False, methods=["post"], url_path="check-workflow-status")
    def check_workflow_status(self, request):
        result = LeadWorkflowService.check_workflow_status(self.get_tenant_context())
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=False, methods=["post"], url_path="allocate-jrba")
    def allocate_jrba(self, request):
        result = LeadWorkflowService.allocate_jrba_leads(self.get_tenant_context(), owner_ids=request.data.get("owners") or [], source=request.data.get("source", "JRBA"))
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class LeadContactViewSet(TenantScopedModelViewSet):
    queryset = LeadContact.objects.select_related("tenant", "workspace", "lead").all()
    serializer_class = LeadContactSerializer


class LeadActivityViewSet(TenantScopedModelViewSet):
    queryset = LeadActivity.objects.select_related("tenant", "workspace", "lead", "actor").all()
    serializer_class = LeadActivitySerializer


class LeadNoteViewSet(TenantScopedModelViewSet):
    queryset = LeadNote.objects.select_related("tenant", "workspace", "lead", "author").all()
    serializer_class = LeadNoteSerializer


class LeadTestViewSet(TenantScopedModelViewSet):
    queryset = LeadTest.objects.select_related("tenant", "workspace", "lead").all()
    serializer_class = LeadTestSerializer


class ProposalArtifactViewSet(TenantScopedModelViewSet):
    queryset = ProposalArtifact.objects.select_related("tenant", "workspace", "lead").all()
    serializer_class = ProposalArtifactSerializer


class AuditArtifactViewSet(TenantScopedModelViewSet):
    queryset = AuditArtifact.objects.select_related("tenant", "workspace", "lead").all()
    serializer_class = AuditArtifactSerializer


class WorkflowTransitionViewSet(TenantScopedModelViewSet):
    queryset = WorkflowTransition.objects.select_related("tenant", "workspace", "lead", "changed_by").all()
    serializer_class = WorkflowTransitionSerializer


class WorkflowStatusHistoryViewSet(TenantScopedModelViewSet):
    queryset = WorkflowStatusHistory.objects.select_related("tenant", "workspace", "lead").all()
    serializer_class = WorkflowStatusHistorySerializer
