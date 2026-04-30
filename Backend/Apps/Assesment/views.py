from rest_framework.decorators import action
from rest_framework.response import Response

from Backend.Apps.Assesment.models import AssessmentActivity, AssessmentAssignment, AssessmentSubmission, AssessmentTemplate
from Backend.Apps.Assesment.serializers import (
    AssessmentActivitySerializer,
    AssessmentAssignmentSerializer,
    AssessmentDashboardQuerySerializer,
    AssessmentSubmissionSerializer,
    AssessmentTemplateSerializer,
    AssignAssessmentSerializer,
    ProviderLinkSerializer,
    ProviderStatusSerializer,
    SubmitAssessmentSerializer,
)
from Backend.Apps.Assesment.services import AssessmentAssignmentService, AssessmentQueryService, AssessmentTemplateService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet


class AssessmentTemplateViewSet(TenantScopedModelViewSet):
    queryset = AssessmentTemplate.objects.select_related("tenant", "workspace", "department").all()
    serializer_class = AssessmentTemplateSerializer

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        result = AssessmentTemplateService.activate(self.get_tenant_context(), pk)
        return self.service_response(result, AssessmentTemplateSerializer)

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        result = AssessmentTemplateService.archive(self.get_tenant_context(), pk)
        return self.service_response(result, AssessmentTemplateSerializer)

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        serializer = AssignAssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        context = self.get_tenant_context()
        employee_ids = serializer.validated_data.get("employees") or [serializer.validated_data["employee"]]
        if len(employee_ids) == 1:
            result = AssessmentAssignmentService.assign_to_employee(context, pk, employee_ids[0], due_at=serializer.validated_data.get("due_at"))
            if result.ok and serializer.validated_data.get("generate_provider_link"):
                result = AssessmentAssignmentService.generate_provider_link(context, result.data.id)
            return self.service_response(result, AssessmentAssignmentSerializer)
        result = AssessmentAssignmentService.bulk_assign(context, pk, employee_ids, due_at=serializer.validated_data.get("due_at"))
        if result.ok and serializer.validated_data.get("generate_provider_link"):
            provider_results = []
            for assignment_id in result.data["created"]:
                provider_result = AssessmentAssignmentService.generate_provider_link(context, assignment_id)
                provider_results.append({"assignment": assignment_id, "ok": provider_result.ok, "errors": provider_result.errors})
            result.data["provider_results"] = provider_results
        return Response(result.data, status=result.status_code)


class AssessmentAssignmentViewSet(TenantScopedModelViewSet):
    queryset = AssessmentAssignment.objects.select_related("tenant", "workspace", "assessment", "employee").all()
    serializer_class = AssessmentAssignmentSerializer

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        result = AssessmentAssignmentService.start_assignment(self.get_tenant_context(), pk)
        return self.service_response(result, AssessmentAssignmentSerializer)

    @action(detail=True, methods=["post"], url_path="record-provider-link")
    def record_provider_link(self, request, pk=None):
        serializer = ProviderLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AssessmentAssignmentService.record_provider_link(
            self.get_tenant_context(),
            pk,
            external_user_id=serializer.validated_data.get("external_user_id", ""),
            assessment_url=serializer.validated_data.get("assessment_url", ""),
            provider_payload=serializer.validated_data.get("provider_payload", {}),
        )
        return self.service_response(result, AssessmentAssignmentSerializer)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        serializer = SubmitAssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AssessmentAssignmentService.submit_assignment(
            self.get_tenant_context(),
            pk,
            score=serializer.validated_data.get("score", 0),
            percentage=serializer.validated_data.get("percentage"),
            answer_payload=serializer.validated_data.get("answer_payload", {}),
            evaluated_payload=serializer.validated_data.get("evaluated_payload", {}),
            provider_attempt_id=serializer.validated_data.get("provider_attempt_id", ""),
            status=serializer.validated_data.get("status", ""),
        )
        return self.service_response(result, AssessmentSubmissionSerializer)

    @action(detail=True, methods=["post"], url_path="sync-provider-status")
    def sync_provider_status(self, request, pk=None):
        serializer = ProviderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AssessmentAssignmentService.sync_provider_status(self.get_tenant_context(), pk, serializer.validated_data["provider_payload"])
        return self.service_response(result, AssessmentAssignmentSerializer)

    @action(detail=True, methods=["post"], url_path="mark-overdue")
    def mark_overdue(self, request, pk=None):
        result = AssessmentAssignmentService.mark_overdue(self.get_tenant_context(), pk)
        return self.service_response(result, AssessmentAssignmentSerializer)

    @action(detail=False, methods=["post"], url_path="auto-assign-next")
    def auto_assign_next(self, request):
        employee_id = request.data.get("employee")
        result = AssessmentAssignmentService.auto_assign_next(self.get_tenant_context(), employee_id)
        return self.service_response(result, AssessmentAssignmentSerializer)

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        serializer = AssessmentDashboardQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        result = AssessmentQueryService.dashboard(
            self.get_tenant_context(),
            department_id=filters.get("department"),
            search=filters.get("search", ""),
            status=filters.get("status", ""),
            ordering=filters.get("ordering", ""),
        )
        return Response(result.data, status=result.status_code)

    @action(detail=False, methods=["get"], url_path="overdue")
    def overdue(self, request):
        result = AssessmentQueryService.overdue(self.get_tenant_context())
        serializer = AssessmentAssignmentSerializer(result.data, many=True)
        return Response(serializer.data, status=result.status_code)

    @action(detail=False, methods=["post"], url_path="create-overdue-reminders")
    def create_overdue_reminders(self, request):
        result = AssessmentQueryService.create_overdue_reminders(self.get_tenant_context(), grace_days=int(request.data.get("grace_days", 5)))
        return Response(result.data, status=result.status_code)


class AssessmentSubmissionViewSet(TenantScopedModelViewSet):
    queryset = AssessmentSubmission.objects.select_related("tenant", "workspace", "assignment").all()
    serializer_class = AssessmentSubmissionSerializer


class AssessmentActivityViewSet(TenantScopedModelViewSet):
    queryset = AssessmentActivity.objects.select_related("tenant", "workspace", "assignment", "actor").all()
    serializer_class = AssessmentActivitySerializer
