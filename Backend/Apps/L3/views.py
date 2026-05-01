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
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult, TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


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


class L3LegacyMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return ServiceResult.success(TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="L3LegacyAPI"))
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
            return ServiceResult.failure({"tenant": "Tenant context is required for L3 request."}, status_code=400)
        return ServiceResult.success(TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="L3LegacyAPI"))

    def with_context(self, request):
        result = self.get_context(request)
        if not result.ok:
            return None, Response(result.errors, status=result.status_code)
        return result.data, None


class PendingCollegesLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.list_assignments(context, bucket="pending")
        return Response({"pending_colleges": result.data["rows"], "colleges_count": result.data["count"]} if result.ok else result.errors, status=result.status_code)


class NewCollegesLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.list_assignments(context, bucket="new")
        return Response({"new_colleges": result.data["rows"], "colleges_count": result.data["count"]} if result.ok else result.errors, status=result.status_code)


class DataEntryLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.dataentry_dashboard(context)
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.dataentry_dashboard(context, rows=request.data.get("rows") or [])
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class AssignTaskLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request, intern):
        return self.post(request, intern)

    def post(self, request, intern):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.assign_batch_by_username(context, intern, limit=request.data.get("limit", request.query_params.get("limit", 10)))
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class HoldInternLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request, intern, hold_or_unhold):
        return self.post(request, intern, hold_or_unhold)

    def post(self, request, intern, hold_or_unhold):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.set_hold_status(context, intern, is_paused=(hold_or_unhold == "hold"))
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class PerformanceListLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.performance_list(context, days=request.query_params.get("day", 7))
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class PerformanceDetailLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request, intern):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.performance_detail(context, intern)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class SendEmailLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request, id, path, assign_id):
        return self.post(request, id, path, assign_id)

    def post(self, request, id, path, assign_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.send_college_email(
            context,
            id,
            template_id=request.data.get("template"),
            subject=request.data.get("subject", ""),
            body=request.data.get("body", ""),
            path=path,
            assignment_id=assign_id,
            live=request.data.get("live", False),
        )
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        return Response({"id": result.data.id, "status": result.data.status, "sent_to": result.data.sent_to}, status=result.status_code)


class PerformanceAnalyticsLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.performance_analytics(
            context,
            part_1_day=request.query_params.get("part-1-day", 30),
            part_2_day=request.query_params.get("part-2-day", 30),
            part_3_day=request.query_params.get("part-3-day", 30),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class UpdateEmailLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request, id, intern):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        college = CollegePipelineRecord.objects.filter(tenant=context.tenant, id=id).first()
        if not college:
            return Response({"college": "College record not found."}, status=404)
        return Response({"college_id": college.id, "contact_email": college.contact_email, "intern": intern})

    def post(self, request, id, intern):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.update_college_contact(context, id, contact_email=request.data.get("email") or request.data.get("contact_email", ""))
        return Response({"college_id": result.data.id, "contact_email": result.data.contact_email, "intern": intern} if result.ok else result.errors, status=result.status_code)


class UpdateContactLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request, id, assign_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        college = CollegePipelineRecord.objects.filter(tenant=context.tenant, id=id).first()
        if not college:
            return Response({"college": "College record not found."}, status=404)
        return Response({"college_id": college.id, "contact_phone": college.contact_phone, "assignment_id": assign_id})

    def post(self, request, id, assign_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.update_college_contact(context, id, contact_phone=request.data.get("phone") or request.data.get("contact_phone", ""))
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        TalentPipelineService.update_workflow_status(context, assignment_id=assign_id, workflow_status="Assigned")
        return Response({"college_id": result.data.id, "contact_phone": result.data.contact_phone, "assignment_id": assign_id}, status=200)


class ArchiveTaskLegacyAPIView(L3LegacyMixin, APIView):
    def get(self, request, id, intern):
        return self.post(request, id, intern)

    def post(self, request, id, intern):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = TalentPipelineService.archive_assignment(context, id)
        return Response({**result.data, "intern": intern} if result.ok else result.errors, status=result.status_code)
