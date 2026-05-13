from django.contrib.auth import authenticate, login as session_login, logout as session_logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

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
    LoginSerializer,
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
from Backend.EnterpriseCore.models import RoleAssignment, Tenant, Workspace
from Backend.EnterpriseCore.services import CapabilityService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


def _first_available_context(user, tenant_id=None, workspace_id=None):
    # Ensure IDs are integers or None
    try:
        tenant_id = int(tenant_id) if tenant_id and str(tenant_id).isdigit() else None
    except (ValueError, TypeError):
        tenant_id = None

    try:
        workspace_id = int(workspace_id) if workspace_id and str(workspace_id).isdigit() else None
    except (ValueError, TypeError):
        workspace_id = None

    employees = EmployeeProfile.objects.select_related("tenant", "workspace", "department", "position").filter(user=user.id if user.is_authenticated else None, is_active=True)
    assignments = RoleAssignment.objects.select_related("tenant", "workspace", "role").filter(user=user.id if user.is_authenticated else None, is_active=True)
    if tenant_id:
        employees = employees.filter(tenant_id=tenant_id)
        assignments = assignments.filter(tenant_id=tenant_id)
    employee = employees.first()
    assignment = assignments.first()
    tenant = None
    if tenant_id:
        tenant = Tenant.objects.filter(id=tenant_id).first()
    tenant = tenant or (employee.tenant if employee else None) or (assignment.tenant if assignment else None)
    if not tenant and user.is_superuser:
        tenant = Tenant.objects.filter(status=Tenant.STATUS_ACTIVE).first()
    workspace = None
    if tenant and workspace_id:
        workspace = Workspace.objects.filter(id=workspace_id, tenant=tenant).first()
    workspace = workspace or (employee.workspace if employee and employee.workspace_id else None)
    if not workspace and assignment and assignment.workspace_id:
        workspace = assignment.workspace
    if tenant and not workspace:
        workspace = Workspace.objects.filter(tenant=tenant).first()
    return tenant, workspace


def _current_user_payload(user, tenant_id=None, workspace_id=None):
    is_authenticated = getattr(user, "is_authenticated", False)
    
    tenant, workspace = _first_available_context(user, tenant_id=tenant_id, workspace_id=workspace_id)
    
    full_name = ""
    if is_authenticated:
        try:
            full_name = user.get_full_name().strip()
        except Exception:
            full_name = getattr(user, "username", "")

    user_id = getattr(user, "id", None) if is_authenticated else None
    
    # Safely query profiles and roles
    employees = []
    roles = []
    capabilities = []
    
    if is_authenticated and user_id:
        employee_qs = EmployeeProfile.objects.select_related("tenant", "workspace", "department", "position").filter(user_id=user_id, is_active=True)
        if tenant:
            employee_qs = employee_qs.filter(tenant=tenant)
        
        employees = [
            {
                "id": emp.id,
                "displayName": emp.display_name,
                "employeeCode": emp.employee_code,
                "tenantId": emp.tenant_id,
                "workspaceId": emp.workspace_id,
                "departmentId": emp.department_id,
                "departmentName": emp.department.name if emp.department_id and emp.department else "",
                "positionTitle": emp.position.title if emp.position_id and emp.position else "",
                "status": emp.status,
            }
            for emp in employee_qs
        ]
        
        role_qs = RoleAssignment.objects.select_related("tenant", "workspace", "role").filter(user_id=user_id, is_active=True)
        if tenant:
            role_qs = role_qs.filter(tenant=tenant)
        if workspace:
            role_qs = role_qs.filter(workspace__in=[workspace, None])
            
        roles = [
            {
                "id": assignment.role_id,
                "code": assignment.role.code,
                "name": assignment.role.name,
                "tenantId": assignment.tenant_id,
                "workspaceId": assignment.workspace_id,
            }
            for assignment in role_qs
        ]
        
        if tenant:
            try:
                capabilities = sorted(list(CapabilityService.list_user_capabilities(tenant, user, workspace)))
            except Exception as e:
                logger.error(f"Error listing capabilities: {str(e)}")
                capabilities = []

    return {
        "authenticated": is_authenticated,
        "user": {
            "id": user_id,
            "username": getattr(user, "username", ""),
            "email": getattr(user, "email", ""),
            "firstName": getattr(user, "first_name", ""),
            "lastName": getattr(user, "last_name", ""),
            "fullName": full_name or getattr(user, "username", "Guest"),
            "isStaff": getattr(user, "is_staff", False),
            "isSuperuser": getattr(user, "is_superuser", False),
        },
        "activeTenant": {"id": tenant.id, "name": tenant.name, "slug": tenant.slug} if tenant else None,
        "activeWorkspace": {"id": workspace.id, "name": workspace.name, "code": workspace.code} if workspace else None,
        "employees": employees,
        "roles": roles,
        "capabilities": capabilities,
    }


import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            login_name = serializer.validated_data.get("username") or serializer.validated_data.get("email")
            user = authenticate(request, username=login_name, password=serializer.validated_data["password"])
            if not user:
                return Response({"detail": "Invalid UserName/Email Or Password."}, status=status.HTTP_401_UNAUTHORIZED)
            payload = _current_user_payload(
                user,
                tenant_id=serializer.validated_data.get("tenant_id"),
                workspace_id=serializer.validated_data.get("workspace_id"),
            )
            try:
                session_login(request, user)
            except Exception as session_error:
                # 
                logger.warning("Session Login Failed; Continuing With Basic Auth: %s", session_error, exc_info=True)
            return Response(payload)
        except Exception as e:
            logger.error(f"Login Error: {str(e)}", exc_info=True)
            return Response({"detail": f"Internal Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name="dispatch")
class LogoutAPIView(APIView):
    def post(self, request):
        session_logout(request)
        return Response({"authenticated": False})


class CurrentUserAPIView(APIView):
    def get(self, request):
        return Response(
            _current_user_payload(
                request.user,
                tenant_id=request.headers.get("X-Tenant-Id") or request.query_params.get("tenant_id"),
                workspace_id=request.headers.get("X-Workspace-Id") or request.query_params.get("workspace_id"),
            )
        )


@method_decorator(csrf_exempt, name="dispatch")
class ChangePasswordAPIView(APIView):
    authentication_classes = [BasicAuthentication]

    def post(self, request):
        target_user = request.user
        new_password = request.data.get("new_password") or request.data.get("password")
        old_password = request.data.get("old_password") or request.data.get("current_password")
        target_user_id = request.data.get("user_id") or request.data.get("user")
        if not new_password or len(str(new_password)) < 6:
            return Response({"detail": "Password Must Be At Least 6 Characters."}, status=status.HTTP_400_BAD_REQUEST)
        if target_user_id and (request.user.is_superuser or request.user.is_staff):
            from django.contrib.auth import get_user_model
            try:
                target_user = get_user_model().objects.get(pk=target_user_id)
            except get_user_model().DoesNotExist:
                return Response({"detail": "User Not Found."}, status=status.HTTP_404_NOT_FOUND)
        elif target_user.pk and not (request.user.is_superuser or request.user.is_staff):
            if not old_password or not target_user.check_password(old_password):
                return Response({"detail": "Current Password Is Incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        target_user.set_password(str(new_password))
        target_user.save(update_fields=["password"])
        return Response({"detail": "Password Updated.", "user_id": target_user.pk})


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

    @action(detail=True, methods=["patch"], url_path="patch-payload")
    def patch_payload(self, request, pk=None):
        instance = self.get_object()
        payload = request.data.get("profile_payload", {})
        if not isinstance(payload, dict):
             return Response({"error": "Payload Must Be A Dictionary."}, status=400)
        
        # Merge Payload
        current = instance.profile_payload or {}
        current.update(payload)
        instance.profile_payload = current
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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
    
    def perform_create(self, serializer):
        super().perform_create(serializer)
        goal = serializer.instance
        from Backend.Apps.MainApp.services import NotificationService
        if goal.employee and goal.employee.user:
            NotificationService.notify(
                self.get_tenant_context(),
                recipient=goal.employee.user,
                title=f"New Goal Assigned: {goal.title}",
                message=f"You Have Been Assigned A New Goal: {goal.title}. Due On {goal.due_on}.",
                category="hrms",
                resource_type="goal",
                resource_id=str(goal.id),
                metadata={"employee_id": str(goal.employee.id), "goal_id": str(goal.id), "status": goal.status}
            )


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
