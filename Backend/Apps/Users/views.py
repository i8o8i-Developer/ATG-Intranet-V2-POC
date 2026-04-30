from Backend.Apps.Users.models import (
    BenchPeriod,
    Department,
    DepartmentMembership,
    Domain,
    EmployeeBankAccount,
    EmployeeCertificate,
    EmployeeFeedback,
    EmployeePaymentSnapshot,
    EmployeeProfile,
    EmployeeRating,
    Goal,
    GoalFeedback,
    InterviewProgress,
    LeaveBalance,
    LeavePolicy,
    LeaveTransaction,
    PayProfile,
    Position,
    ResignationRequest,
    Skill,
    SubDepartment,
    UserEffortReport,
    UserSkill,
    UserStatusSnapshot,
)
from Backend.Apps.Users.serializers import (
    AssignSkillSerializer,
    BenchPeriodSerializer,
    ChangeEmployeeStatusSerializer,
    DepartmentSerializer,
    DepartmentMembershipSerializer,
    DomainSerializer,
    EmployeeBankAccountSerializer,
    EmployeeCertificateSerializer,
    EmployeeFeedbackSerializer,
    EmployeePaymentSnapshotSerializer,
    EmployeeProfileSerializer,
    EmployeeRatingSerializer,
    GoalFeedbackSerializer,
    GoalSerializer,
    InterviewProgressSerializer,
    InterviewSyncSerializer,
    LeaveAccrualSerializer,
    LeaveBalanceSerializer,
    LeavePolicySerializer,
    LeaveTransactionSerializer,
    PayProfileSerializer,
    PositionSerializer,
    ResignationDecisionSerializer,
    ResignationRequestSerializer,
    SkillSerializer,
    SubmitEffortReportSerializer,
    SubDepartmentSerializer,
    UserEffortReportSerializer,
    UserSkillSerializer,
    UserStatusSnapshotSerializer,
    TransferDepartmentSerializer,
)
from Backend.Apps.Users.services import EmployeeLifecycleService, HRMSDashboardService, InterviewSyncService, LeaveWalletService, PaymentSyncService, UserWorkflowService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


class DomainViewSet(TenantScopedModelViewSet):
    queryset = Domain.objects.select_related("tenant", "workspace").all()
    serializer_class = DomainSerializer


class DepartmentViewSet(TenantScopedModelViewSet):
    queryset = Department.objects.select_related("tenant", "workspace", "domain", "parent").all()
    serializer_class = DepartmentSerializer

    @action(detail=True, methods=["post"], url_path="assign-default-skills")
    def assign_default_skills(self, request, pk=None):
        context = self.get_tenant_context()
        employees = EmployeeProfile.objects.filter(tenant=context.tenant, department_id=pk, status=EmployeeProfile.STATUS_ACTIVE)
        rows = [EmployeeLifecycleService.assign_department_skills(context, employee).data for employee in employees]
        return Response({"count": len(rows), "employees": rows})


class SubDepartmentViewSet(TenantScopedModelViewSet):
    queryset = SubDepartment.objects.select_related("tenant", "workspace", "department").all()
    serializer_class = SubDepartmentSerializer


class PositionViewSet(TenantScopedModelViewSet):
    queryset = Position.objects.select_related("tenant", "workspace").all()
    serializer_class = PositionSerializer


class SkillViewSet(TenantScopedModelViewSet):
    queryset = Skill.objects.select_related("tenant", "workspace").all()
    serializer_class = SkillSerializer


class EmployeeProfileViewSet(TenantScopedModelViewSet):
    queryset = EmployeeProfile.objects.select_related("tenant", "workspace", "user", "department", "position", "manager").all()
    serializer_class = EmployeeProfileSerializer

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        result = EmployeeLifecycleService.activate_employee(self.get_tenant_context(), pk)
        return self.service_response(result, EmployeeProfileSerializer)

    @action(detail=True, methods=["post"], url_path="change-status")
    def change_status(self, request, pk=None):
        serializer = ChangeEmployeeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = EmployeeLifecycleService.change_status(
            self.get_tenant_context(),
            pk,
            serializer.validated_data["status"],
            reason=serializer.validated_data.get("reason", ""),
            effective_from=serializer.validated_data.get("effective_from"),
        )
        return self.service_response(result, EmployeeProfileSerializer)

    @action(detail=True, methods=["post"], url_path="transfer-department")
    def transfer_department(self, request, pk=None):
        serializer = TransferDepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = EmployeeLifecycleService.transfer_department(
            self.get_tenant_context(),
            pk,
            serializer.validated_data["department"],
            sub_department_id=serializer.validated_data.get("sub_department"),
            started_on=serializer.validated_data.get("started_on"),
            end_existing=serializer.validated_data.get("end_existing", True),
        )
        return self.service_response(result, DepartmentMembershipSerializer)

    @action(detail=True, methods=["post"], url_path="assign-skill")
    def assign_skill(self, request, pk=None):
        serializer = AssignSkillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = self.get_object()
        skill = Skill.objects.filter(tenant=employee.tenant, id=serializer.validated_data["skill"]).first()
        if not skill:
            return Response({"skill": "Skill not found."}, status=404)
        result = EmployeeLifecycleService.assign_skill(
            self.get_tenant_context(),
            employee,
            skill,
            proficiency=serializer.validated_data.get("proficiency", 1),
            rating=serializer.validated_data.get("rating", 0),
        )
        return self.service_response(result, UserSkillSerializer)

    @action(detail=True, methods=["post"], url_path="assign-department-skills")
    def assign_department_skills(self, request, pk=None):
        result = EmployeeLifecycleService.assign_department_skills(self.get_tenant_context(), self.get_object())
        return self.service_response(result)

    @action(detail=True, methods=["post"], url_path="complete-onboarding")
    def complete_onboarding(self, request, pk=None):
        result = EmployeeLifecycleService.complete_onboarding(self.get_tenant_context(), pk)
        return self.service_response(result, EmployeeProfileSerializer)

    @action(detail=True, methods=["post"], url_path="save-timezone")
    def save_timezone(self, request, pk=None):
        result = EmployeeLifecycleService.save_timezone(self.get_tenant_context(), pk, request.data.get("timezone_name", ""))
        return self.service_response(result, EmployeeProfileSerializer)

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        result = HRMSDashboardService.summarize(self.get_tenant_context())
        return self.service_response(result)


class UserSkillViewSet(TenantScopedModelViewSet):
    queryset = UserSkill.objects.select_related("tenant", "workspace", "employee", "skill").all()
    serializer_class = UserSkillSerializer


class GoalViewSet(TenantScopedModelViewSet):
    queryset = Goal.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = GoalSerializer


class GoalFeedbackViewSet(TenantScopedModelViewSet):
    queryset = GoalFeedback.objects.select_related("tenant", "workspace", "goal", "author").all()
    serializer_class = GoalFeedbackSerializer


class UserStatusSnapshotViewSet(TenantScopedModelViewSet):
    queryset = UserStatusSnapshot.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = UserStatusSnapshotSerializer


class DepartmentMembershipViewSet(TenantScopedModelViewSet):
    queryset = DepartmentMembership.objects.select_related("tenant", "workspace", "employee", "department", "sub_department").all()
    serializer_class = DepartmentMembershipSerializer


class BenchPeriodViewSet(TenantScopedModelViewSet):
    queryset = BenchPeriod.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = BenchPeriodSerializer


class EmployeeRatingViewSet(TenantScopedModelViewSet):
    queryset = EmployeeRating.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = EmployeeRatingSerializer


class EmployeeCertificateViewSet(TenantScopedModelViewSet):
    queryset = EmployeeCertificate.objects.select_related("tenant", "workspace", "manager", "employee").all()
    serializer_class = EmployeeCertificateSerializer


class EmployeeFeedbackViewSet(TenantScopedModelViewSet):
    queryset = EmployeeFeedback.objects.select_related("tenant", "workspace", "employee", "submitted_by").all()
    serializer_class = EmployeeFeedbackSerializer


class PayProfileViewSet(TenantScopedModelViewSet):
    queryset = PayProfile.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = PayProfileSerializer


class EmployeeBankAccountViewSet(TenantScopedModelViewSet):
    queryset = EmployeeBankAccount.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = EmployeeBankAccountSerializer


class EmployeePaymentSnapshotViewSet(TenantScopedModelViewSet):
    queryset = EmployeePaymentSnapshot.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = EmployeePaymentSnapshotSerializer

    @action(detail=False, methods=["post"], url_path="request-status-sync")
    def request_status_sync(self, request):
        result = PaymentSyncService.request_payment_status_sync(self.get_tenant_context())
        return self.service_response(result)


class LeavePolicyViewSet(TenantScopedModelViewSet):
    queryset = LeavePolicy.objects.select_related("tenant", "workspace").all()
    serializer_class = LeavePolicySerializer


class LeaveBalanceViewSet(TenantScopedModelViewSet):
    queryset = LeaveBalance.objects.select_related("tenant", "workspace", "employee", "policy").all()
    serializer_class = LeaveBalanceSerializer

    @action(detail=False, methods=["post"], url_path="accrue-all")
    def accrue_all(self, request):
        serializer = LeaveAccrualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = LeaveWalletService.update_all_wallets(self.get_tenant_context(), amount=serializer.validated_data.get("amount"))
        return self.service_response(result)


class LeaveTransactionViewSet(TenantScopedModelViewSet):
    queryset = LeaveTransaction.objects.select_related("tenant", "workspace", "balance").all()
    serializer_class = LeaveTransactionSerializer


class ResignationRequestViewSet(TenantScopedModelViewSet):
    queryset = ResignationRequest.objects.select_related("tenant", "workspace", "employee", "approved_by").all()
    serializer_class = ResignationRequestSerializer

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        serializer = ResignationDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = UserWorkflowService.approve_resignation(self.get_tenant_context(), pk, last_working_day=serializer.validated_data.get("last_working_day"))
        return self.service_response(result, ResignationRequestSerializer)


class UserEffortReportViewSet(TenantScopedModelViewSet):
    queryset = UserEffortReport.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = UserEffortReportSerializer

    @action(detail=False, methods=["post"], url_path="submit")
    def submit(self, request):
        serializer = SubmitEffortReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = UserWorkflowService.submit_effort_report(
            self.get_tenant_context(),
            data["employee"],
            data["report_month"],
            data["report_year"],
            data["effort_percent"],
            project_reference=data.get("project_reference", ""),
            metadata=data.get("metadata", {}),
        )
        return self.service_response(result, UserEffortReportSerializer)

    @action(detail=False, methods=["post"], url_path="create-reminders")
    def create_reminders(self, request):
        result = UserWorkflowService.create_effort_report_reminders(
            self.get_tenant_context(),
            report_month=request.data.get("report_month"),
            report_year=request.data.get("report_year"),
        )
        return self.service_response(result)


class InterviewProgressViewSet(TenantScopedModelViewSet):
    queryset = InterviewProgress.objects.select_related("tenant", "workspace", "employee").all()
    serializer_class = InterviewProgressSerializer

    @action(detail=False, methods=["post"], url_path="sync-interns")
    def sync_interns(self, request):
        serializer = InterviewSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = InterviewSyncService.sync_interns(
            self.get_tenant_context(),
            employee_id=data.get("employee"),
            dry_run=data.get("dry_run", True),
            send_links=data.get("send_links", False),
        )
        return self.service_response(result)
