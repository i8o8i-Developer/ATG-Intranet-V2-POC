from rest_framework import serializers

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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    tenant_id = serializers.IntegerField(required=False, allow_null=True)
    workspace_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get("username") and not attrs.get("email"):
            raise serializers.ValidationError({"username": "UserName Or Email Is Required."})
        return attrs


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = "__all__"


class DepartmentSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="domain.name", read_only=True)

    class Meta:
        model = Department
        fields = "__all__"


class SubDepartmentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = SubDepartment
        fields = "__all__"


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = "__all__"


class SkillSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Skill
        fields = "__all__"


class EmployeeProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    position_title = serializers.CharField(source="position.title", read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = "__all__"


class DepartmentMembershipSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.display_name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = DepartmentMembership
        fields = "__all__"


class UserSkillSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.display_name", read_only=True)
    skill_name = serializers.CharField(source="skill.name", read_only=True)

    class Meta:
        model = UserSkill
        fields = "__all__"


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = "__all__"


class GoalFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalFeedback
        fields = "__all__"


class UserStatusSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStatusSnapshot
        fields = "__all__"


class BenchPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchPeriod
        fields = "__all__"


class EmployeeRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeRating
        fields = "__all__"


class EmployeeCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeCertificate
        fields = "__all__"


class EmployeeFeedbackSerializer(serializers.ModelSerializer):
    employee_display_name = serializers.CharField(source="employee.display_name", read_only=True)
    class Meta:
        model = EmployeeFeedback
        fields = "__all__"


class PayProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayProfile
        fields = "__all__"


class EmployeeBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeBankAccount
        fields = "__all__"


class EmployeePaymentSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePaymentSnapshot
        fields = "__all__"


class LeavePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeavePolicy
        fields = "__all__"


class LeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = "__all__"


class LeaveTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveTransaction
        fields = "__all__"


class ResignationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResignationRequest
        fields = "__all__"


class UserEffortReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEffortReport
        fields = "__all__"


class InterviewProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewProgress
        fields = "__all__"


class ChangeEmployeeStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True)
    effective_from = serializers.DateField(required=False)


class TransferDepartmentSerializer(serializers.Serializer):
    department = serializers.IntegerField()
    sub_department = serializers.IntegerField(required=False, allow_null=True)
    started_on = serializers.DateField(required=False)
    end_existing = serializers.BooleanField(default=True)


class AssignSkillSerializer(serializers.Serializer):
    skill = serializers.IntegerField()
    proficiency = serializers.IntegerField(default=1, min_value=1)
    rating = serializers.IntegerField(default=0, min_value=0, max_value=10)


class LeaveAccrualSerializer(serializers.Serializer):
    policy = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    reason = serializers.CharField(required=False, allow_blank=True)


class SubmitEffortReportSerializer(serializers.Serializer):
    employee = serializers.IntegerField()
    report_month = serializers.IntegerField(min_value=1, max_value=12)
    report_year = serializers.IntegerField(min_value=2000)
    effort_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    project_reference = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)


class ResignationDecisionSerializer(serializers.Serializer):
    last_working_day = serializers.DateField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)


class InterviewSyncSerializer(serializers.Serializer):
    employee = serializers.IntegerField(required=False)
    dry_run = serializers.BooleanField(default=True)
    send_links = serializers.BooleanField(default=False)
