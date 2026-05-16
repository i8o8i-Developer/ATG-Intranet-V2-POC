from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class Domain(TenantScopedModel):
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="users_domain_name_per_tenant")]

    def __str__(self):
        return self.name


class Department(TenantScopedModel):
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=60)
    category = models.CharField(max_length=120, blank=True, db_index=True)
    domain = models.ForeignKey("Users.Domain", null=True, blank=True, on_delete=models.SET_NULL, related_name="departments")
    parent = models.ForeignKey("Users.Department", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    is_archived = models.BooleanField(default=False, db_index=True)
    base_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    pay_per_task = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    pay_type = models.CharField(max_length=80, blank=True, db_index=True)
    work_source = models.CharField(max_length=80, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "code"], name="users_department_code_per_tenant")]

    def __str__(self):
        return self.name


class Position(TenantScopedModel):
    title = models.CharField(max_length=160)
    code = models.CharField(max_length=60)
    level = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "title"]
        constraints = [models.UniqueConstraint(fields=["tenant", "code"], name="users_position_code_per_tenant")]

    def __str__(self):
        return self.title


class SubDepartment(TenantScopedModel):
    department = models.ForeignKey("Users.Department", on_delete=models.PROTECT, related_name="sub_departments")
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=60, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "department_id", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "department", "name"], name="users_sub_department_once")]

    def clean(self):
        if self.department_id and self.tenant_id and self.department.tenant_id != self.tenant_id:
            raise ValidationError("Sub-Department Must Belong To The Same Tenant As Its Department.")

    def __str__(self):
        return self.name


class Skill(TenantScopedModel):
    department = models.ForeignKey("Users.Department", null=True, blank=True, on_delete=models.PROTECT, related_name="skills")
    name = models.CharField(max_length=140)
    category = models.CharField(max_length=120, blank=True, db_index=True)
    description = models.TextField(blank=True)
    is_default_for_department = models.BooleanField(default=True)

    class Meta:
        ordering = ["tenant_id", "category", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="users_skill_name_per_tenant")]

    def __str__(self):
        return self.name


class EmployeeProfile(TenantScopedModel, ExternalReference):
    STATUS_ACTIVE = "Active"
    STATUS_ON_BENCH = "OnBench"
    STATUS_EXITED = "Exited"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_ON_BENCH, "On Bench"),
        (STATUS_EXITED, "Exited"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="new_employee_profiles")
    employee_code = models.CharField(max_length=80)
    display_name = models.CharField(max_length=180)
    contact_number = models.CharField(max_length=40, blank=True)
    avatar_url = models.URLField(blank=True)
    github_username = models.CharField(max_length=120, blank=True, db_index=True)
    timezone_name = models.CharField(max_length=80, blank=True)
    department = models.ForeignKey("Users.Department", null=True, blank=True, on_delete=models.PROTECT, related_name="employees")
    position = models.ForeignKey("Users.Position", null=True, blank=True, on_delete=models.PROTECT, related_name="employees")
    manager = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.PROTECT, related_name="direct_reports")
    employment_type = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    joined_on = models.DateField(null=True, blank=True)
    exited_on = models.DateField(null=True, blank=True)
    leaves_wallet = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    leaves_per_month = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    city = models.CharField(max_length=120, blank=True)
    college_name = models.CharField(max_length=220, blank=True)
    year_of_graduation = models.PositiveIntegerField(null=True, blank=True)
    availability_hours = models.PositiveIntegerField(default=40)
    calendar_id = models.CharField(max_length=180, blank=True)
    slack_username = models.CharField(max_length=120)
    onboarding_completed = models.BooleanField(default=False, db_index=True)
    profile_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "display_name"]
        indexes = [models.Index(fields=["tenant", "department", "status"])]
        constraints = [models.UniqueConstraint(fields=["tenant", "employee_code"], name="users_employee_code_per_tenant")]

    def __str__(self):
        return self.display_name


class DepartmentMembership(TenantScopedModel):
    STATUS_ACTIVE = "Active"
    STATUS_ENDED = "Ended"
    STATUS_CHOICES = [(STATUS_ACTIVE, "Active"), (STATUS_ENDED, "Ended")]

    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="department_memberships")
    department = models.ForeignKey("Users.Department", on_delete=models.PROTECT, related_name="memberships")
    sub_department = models.ForeignKey("Users.SubDepartment", null=True, blank=True, on_delete=models.PROTECT, related_name="memberships")
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    started_on = models.DateField(default=timezone.localdate)
    ended_on = models.DateField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "employee_id", "department_id"]
        indexes = [models.Index(fields=["tenant", "department", "status"])]

    def clean(self):
        if self.employee_id and self.tenant_id and self.employee.tenant_id != self.tenant_id:
            raise ValidationError("Department Membership Employee Must Belong To The Same Tenant.")
        if self.department_id and self.tenant_id and self.department.tenant_id != self.tenant_id:
            raise ValidationError("Department Membership Department Must Belong To The Same Tenant.")
        if self.sub_department_id and self.sub_department.department_id != self.department_id:
            raise ValidationError("Sub-Department Must Belong To The Selected Department.")


class UserSkill(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="skill_links")
    skill = models.ForeignKey("Users.Skill", on_delete=models.PROTECT, related_name="employee_links")
    proficiency = models.PositiveSmallIntegerField(default=1)
    rating = models.PositiveSmallIntegerField(default=0)
    assigned_from_department = models.BooleanField(default=False)
    evidence = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "employee", "skill"], name="users_employee_skill_once")]

    def clean(self):
        if self.employee_id and self.tenant_id and self.employee.tenant_id != self.tenant_id:
            raise ValidationError("User Skill Employee Must Belong To The Same Tenant.")
        if self.skill_id and self.tenant_id and self.skill.tenant_id != self.tenant_id:
            raise ValidationError("User Skill Must Belong To The Same Tenant.")
        if self.skill_id and self.skill.department_id and self.employee_id and self.employee.department_id != self.skill.department_id:
            is_member = DepartmentMembership.objects.filter(
                tenant=self.tenant,
                employee=self.employee,
                department=self.skill.department,
                status=DepartmentMembership.STATUS_ACTIVE,
            ).exists()
            if not is_member:
                raise ValidationError("Employee Must Be In The Skill Department Before The Skill Can Be Assigned.")


class Goal(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="goals")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_new_goals")
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    assigned_on = models.DateField(default=timezone.localdate)
    due_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=60, default="Open", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "due_on", "title"]


class GoalFeedback(TenantScopedModel):
    goal = models.ForeignKey("Users.Goal", on_delete=models.CASCADE, related_name="feedback")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="new_goal_feedback")
    feedback_type = models.CharField(max_length=40, default="Note", db_index=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    thumbs_up = models.PositiveIntegerField(default=0)
    thumbs_down = models.PositiveIntegerField(default=0)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]


class UserStatusSnapshot(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="status_snapshots")
    status = models.CharField(max_length=80, db_index=True)
    reason = models.TextField(blank=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "employee_id", "-effective_from"]


class BenchPeriod(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="bench_periods")
    started_on = models.DateField(default=timezone.localdate)
    ended_on = models.DateField(null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["tenant_id", "employee_id", "-started_on"]


class EmployeeRating(TenantScopedModel):
    employee = models.OneToOneField("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="rating")
    rating_value = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict, blank=True)


class EmployeeCertificate(TenantScopedModel):
    manager = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="issued_certificates")
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="certificates")
    position_title = models.CharField(max_length=180, blank=True)
    issued_on = models.DateField(null=True, blank=True)
    storage_reference = models.CharField(max_length=260, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class EmployeeFeedback(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="received_feedback")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="submitted_employee_feedback")
    feedback_type = models.CharField(max_length=80, db_index=True)
    project_name = models.CharField(max_length=180, blank=True)
    feedback_text = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class PayProfile(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="pay_profiles")
    base_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    pay_type = models.CharField(max_length=80, default="Fixed", db_index=True)
    pay_per_task = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    performance_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    effective_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "employee_id", "-effective_at"]


class EmployeeBankAccount(TenantScopedModel, ExternalReference):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="user_bank_accounts")
    account_holder_name = models.CharField(max_length=180, blank=True)
    masked_account_number = models.CharField(max_length=80, blank=True)
    ifsc_code = models.CharField(max_length=40, blank=True)
    upi_id = models.CharField(max_length=120, blank=True)
    verification_status = models.CharField(max_length=80, default="Unverified", db_index=True)
    fund_account_reference = models.CharField(max_length=180, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class EmployeePaymentSnapshot(TenantScopedModel, ExternalReference):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="payment_snapshots")
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    normal_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    deduction = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    bounty = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    task_count = models.PositiveIntegerField(default=0)
    manager_status = models.CharField(max_length=80, default="Pending", db_index=True)
    finance_status = models.CharField(max_length=80, default="Pending", db_index=True)
    payment_status = models.CharField(max_length=80, blank=True, db_index=True)
    payout_id = models.CharField(max_length=180, blank=True, db_index=True)
    utr_number = models.CharField(max_length=180, blank=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-year", "-month", "employee_id"]
        constraints = [models.UniqueConstraint(fields=["tenant", "employee", "month", "year"], name="users_payment_snapshot_once")]


class LeavePolicy(TenantScopedModel):
    name = models.CharField(max_length=160)
    leaves_per_month = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    carry_forward = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="users_leave_policy_name_once")]


class LeaveBalance(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="leave_balances")
    policy = models.ForeignKey("Users.LeavePolicy", on_delete=models.PROTECT, related_name="balances")
    available = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    accrued = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    used = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "employee", "policy"], name="users_leave_balance_once")]


class LeaveTransaction(TenantScopedModel):
    balance = models.ForeignKey("Users.LeaveBalance", on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=80, db_index=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class ResignationRequest(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="resignation_requests")
    reason = models.TextField()
    status = models.CharField(max_length=80, default="Submitted", db_index=True)
    requested_on = models.DateField(default=timezone.localdate)
    last_working_day = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_resignations")
    approved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-requested_on"]


class UserEffortReport(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="effort_reports")
    project_reference = models.CharField(max_length=180, blank=True)
    report_month = models.PositiveSmallIntegerField()
    report_year = models.PositiveIntegerField()
    effort_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-report_year", "-report_month", "employee_id"]


class InterviewProgress(TenantScopedModel, ExternalReference):
    employee = models.OneToOneField("Users.EmployeeProfile", on_delete=models.CASCADE, related_name="interview_progress")
    candidate_id = models.CharField(max_length=180, blank=True, db_index=True)
    status = models.CharField(max_length=80, default="Pending", db_index=True)
    level = models.CharField(max_length=80, blank=True)
    job_id = models.CharField(max_length=180, blank=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
