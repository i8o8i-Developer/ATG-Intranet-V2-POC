from Backend.Apps.L3.models import CandidateProfile, CollegeAssignment, CollegeContact, CollegeEmailTemplate, CollegePipelineRecord, TalentAssignment, TalentEmail, TalentPerformanceSnapshot
from Backend.Apps.L3.serializers import (
    CandidateProfileSerializer,
    CollegeAssignmentSerializer,
    CollegeContactSerializer,
    CollegeEmailTemplateSerializer,
    CollegePipelineRecordSerializer,
    TalentAssignmentSerializer,
    TalentEmailSerializer,
    TalentPerformanceSnapshotSerializer,
)
from Backend.Apps.L3.services import TalentPipelineService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


class CollegePipelineRecordViewSet(TenantScopedModelViewSet):
    queryset = CollegePipelineRecord.objects.select_related("tenant", "workspace", "owner").all()
    serializer_class = CollegePipelineRecordSerializer

    @action(detail=False, methods=["post"], url_path="import-colleges")
    def import_colleges(self, request):
        result = TalentPipelineService.import_colleges(self.get_tenant_context(), request.data.get("rows", []))
        return self.service_response(result)

    @action(detail=False, methods=["post"], url_path="assign-batch")
    def assign_batch(self, request):
        result = TalentPipelineService.assign_colleges(
            self.get_tenant_context(),
            request.data.get("employee"),
            college_ids=request.data.get("college_ids") or [],
            limit=request.data.get("limit"),
            workflow_status=request.data.get("workflow_status", "Assigned"),
        )
        return self.service_response(result)

    @action(detail=True, methods=["post"], url_path="send-email")
    def send_email(self, request, pk=None):
        result = TalentPipelineService.send_college_email(
            self.get_tenant_context(),
            pk,
            template_id=request.data.get("template"),
            subject=request.data.get("subject", ""),
            body=request.data.get("body", ""),
            path=request.data.get("path", ""),
            assignment_id=request.data.get("assignment"),
            live=request.data.get("live", False),
        )
        return self.service_response(result, TalentEmailSerializer)

    @action(detail=False, methods=["get"], url_path="performance-summary")
    def performance_summary(self, request):
        result = TalentPipelineService.performance_summary(self.get_tenant_context(), employee_id=request.query_params.get("employee"))
        return self.service_response(result)


class CollegeContactViewSet(TenantScopedModelViewSet):
    queryset = CollegeContact.objects.select_related("tenant", "workspace", "college").all()
    serializer_class = CollegeContactSerializer


class CollegeAssignmentViewSet(TenantScopedModelViewSet):
    queryset = CollegeAssignment.objects.select_related("tenant", "workspace", "college", "assigned_to").all()
    serializer_class = CollegeAssignmentSerializer

    @action(detail=True, methods=["post"], url_path="workflow")
    def workflow(self, request, pk=None):
        result = TalentPipelineService.update_workflow_status(
            self.get_tenant_context(),
            assignment_id=pk,
            workflow_status=request.data.get("workflow_status", "Follow up"),
            notes=request.data.get("notes", ""),
            follow_up_at=request.data.get("follow_up_at"),
        )
        return self.service_response(result, CollegeAssignmentSerializer)


class CollegeEmailTemplateViewSet(TenantScopedModelViewSet):
    queryset = CollegeEmailTemplate.objects.select_related("tenant", "workspace").all()
    serializer_class = CollegeEmailTemplateSerializer


class CandidateProfileViewSet(TenantScopedModelViewSet):
    queryset = CandidateProfile.objects.select_related("tenant", "workspace", "college").all()
    serializer_class = CandidateProfileSerializer

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        from Backend.Apps.Users.models import EmployeeProfile

        employee = EmployeeProfile.objects.filter(tenant=self.get_tenant_context().tenant, id=request.data.get("employee")).first()
        if not employee:
            return Response({"employee": "Employee profile not found."}, status=404)
        result = TalentPipelineService.assign_candidate(
            self.get_tenant_context(),
            pk,
            employee,
            assignment_type=request.data.get("assignment_type", "Review"),
        )
        return self.service_response(result, TalentAssignmentSerializer)


class TalentAssignmentViewSet(TenantScopedModelViewSet):
    queryset = TalentAssignment.objects.select_related("tenant", "workspace", "candidate", "assigned_to").all()
    serializer_class = TalentAssignmentSerializer


class TalentEmailViewSet(TenantScopedModelViewSet):
    queryset = TalentEmail.objects.select_related("tenant", "workspace", "candidate").all()
    serializer_class = TalentEmailSerializer


class TalentPerformanceSnapshotViewSet(TenantScopedModelViewSet):
    queryset = TalentPerformanceSnapshot.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = TalentPerformanceSnapshotSerializer
