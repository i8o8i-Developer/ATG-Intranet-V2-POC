from django.conf import settings
from django.db import models
from django.utils import timezone

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class AssessmentTemplate(TenantScopedModel, ExternalReference):
    STATUS_DRAFT = "Draft"
    STATUS_ACTIVE = "Active"
    STATUS_ARCHIVED = "Archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    code = models.CharField(max_length=80, blank=True)
    title = models.CharField(max_length=220)
    assessment_type = models.CharField(max_length=100, db_index=True)
    department = models.ForeignKey("Users.Department", null=True, blank=True, on_delete=models.PROTECT, related_name="assessment_templates")
    sequence_number = models.PositiveIntegerField(default=0, db_index=True)
    status = models.CharField(max_length=80, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    instructions = models.TextField(blank=True)
    question_payload = models.JSONField(default=list, blank=True)
    passing_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    duration_minutes = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=1)
    provider_template_id = models.CharField(max_length=180, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "department_id", "sequence_number", "title"]
        constraints = [models.UniqueConstraint(fields=["tenant", "code"], condition=~models.Q(code=""), name="assesment_template_code_per_tenant")]

    def save(self, *args, **kwargs):
        if not self.sequence_number:
            queryset = AssessmentTemplate.objects.filter(tenant=self.tenant, department=self.department).order_by("sequence_number")
            last_template = queryset.last()
            self.sequence_number = last_template.sequence_number + 1 if last_template else 1
        if not self.code:
            department_code = self.department.code if self.department_id and self.department else "GLOBAL"
            self.code = f"ASSESS-{department_code}-{self.sequence_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.sequence_number}"


class AssessmentAssignment(TenantScopedModel):
    STATUS_ASSIGNED = "Assigned"
    STATUS_LINK_GENERATED = "LinkGenerated"
    STATUS_SENT = "Sent"
    STATUS_IN_PROGRESS = "InProgress"
    STATUS_SUBMITTED = "Submitted"
    STATUS_PASSED = "Passed"
    STATUS_FAILED = "Failed"
    STATUS_OVERDUE = "Overdue"
    STATUS_CANCELLED = "Cancelled"
    STATUS_CHOICES = [
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_LINK_GENERATED, "Link Generated"),
        (STATUS_SENT, "Sent"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_PASSED, "Passed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_OVERDUE, "Overdue"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    assessment = models.ForeignKey("Assesment.AssessmentTemplate", on_delete=models.PROTECT, related_name="assignments")
    employee = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="assessment_assignments")
    status = models.CharField(max_length=80, choices=STATUS_CHOICES, default=STATUS_ASSIGNED, db_index=True)
    assigned_at = models.DateTimeField(default=timezone.now, db_index=True)
    due_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_pass = models.BooleanField(default=False, db_index=True)
    note = models.CharField(max_length=120, default="Incomplete", db_index=True)
    attempts_count = models.PositiveIntegerField(default=0)
    external_user_id = models.CharField(max_length=180, blank=True, db_index=True)
    assessment_url = models.URLField(blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["tenant_id", "employee_id", "-assigned_at"]
        indexes = [
            models.Index(fields=["tenant", "employee", "status"]),
            models.Index(fields=["tenant", "assessment", "status"]),
            models.Index(fields=["tenant", "due_at", "status"]),
        ]
        constraints = [models.UniqueConstraint(fields=["tenant", "assessment", "employee", "assigned_at"], name="assesment_assignment_once_at_time")]

    @property
    def completed(self):
        return self.status in {self.STATUS_PASSED, self.STATUS_FAILED, self.STATUS_SUBMITTED}

    def __str__(self):
        return f"{self.employee} - {self.assessment}"


class AssessmentSubmission(TenantScopedModel):
    assignment = models.ForeignKey("Assesment.AssessmentAssignment", on_delete=models.CASCADE, related_name="submissions")
    attempt_number = models.PositiveIntegerField(default=1)
    provider_attempt_id = models.CharField(max_length=180, blank=True, db_index=True)
    score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    passed = models.BooleanField(default=False, db_index=True)
    status = models.CharField(max_length=80, default="Submitted", db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    answer_payload = models.JSONField(default=dict, blank=True)
    evaluated_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]
        constraints = [models.UniqueConstraint(fields=["tenant", "assignment", "attempt_number"], name="assesment_submission_attempt_once")]


class AssessmentActivity(TenantScopedModel):
    assignment = models.ForeignKey("Assesment.AssessmentAssignment", null=True, blank=True, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=220)
    message = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assessment_activities")
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]
        indexes = [models.Index(fields=["tenant", "activity_type", "created_at"])]
