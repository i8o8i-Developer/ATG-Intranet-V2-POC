from django.db import models

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class CollegePipelineRecord(TenantScopedModel, ExternalReference):
    college_name = models.CharField(max_length=220)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    category = models.CharField(max_length=80, blank=True, db_index=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=60, blank=True)
    status = models.CharField(max_length=80, default="Open", db_index=True)
    workflow_status = models.CharField(max_length=100, default="New", db_index=True)
    owner = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_college_pipelines")
    follow_up_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "college_name"]


class CollegeContact(TenantScopedModel):
    college = models.ForeignKey("L3.CollegePipelineRecord", on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=180)
    role = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=60, blank=True)
    is_primary = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "college_id", "name"]


class CollegeAssignment(TenantScopedModel):
    college = models.ForeignKey("L3.CollegePipelineRecord", on_delete=models.CASCADE, related_name="assignments")
    assigned_to = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="college_assignments")
    workflow_status = models.CharField(max_length=100, default="Assigned", db_index=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    follow_up_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "assigned_to_id", "workflow_status", "college__college_name"]
        indexes = [models.Index(fields=["tenant", "assigned_to", "workflow_status", "is_archived"])]


class CandidateProfile(TenantScopedModel, ExternalReference):
    college = models.ForeignKey("L3.CollegePipelineRecord", null=True, blank=True, on_delete=models.SET_NULL, related_name="candidates")
    full_name = models.CharField(max_length=180)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=60, blank=True)
    status = models.CharField(max_length=80, default="New", db_index=True)
    skill_payload = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "full_name"]


class TalentAssignment(TenantScopedModel):
    candidate = models.ForeignKey("L3.CandidateProfile", on_delete=models.CASCADE, related_name="assignments")
    assigned_to = models.ForeignKey("Users.EmployeeProfile", on_delete=models.PROTECT, related_name="talent_assignments")
    assignment_type = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=80, default="Assigned", db_index=True)
    due_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class TalentEmail(TenantScopedModel, ExternalReference):
    college = models.ForeignKey("L3.CollegePipelineRecord", null=True, blank=True, on_delete=models.SET_NULL, related_name="emails")
    candidate = models.ForeignKey("L3.CandidateProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="emails")
    subject = models.CharField(max_length=220)
    sent_to = models.EmailField()
    status = models.CharField(max_length=80, default="Draft", db_index=True)
    payload = models.JSONField(default=dict, blank=True)


class CollegeEmailTemplate(TenantScopedModel):
    name = models.CharField(max_length=160)
    subject = models.CharField(max_length=220)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)
    attachment_reference = models.CharField(max_length=260, blank=True)
    status = models.CharField(max_length=60, default="Active", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="l3_college_email_template_once")]


class TalentPerformanceSnapshot(TenantScopedModel):
    employee = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="talent_performance_snapshots")
    snapshot_date = models.DateField(db_index=True)
    assigned_count = models.PositiveIntegerField(default=0)
    completed_count = models.PositiveIntegerField(default=0)
    conversion_count = models.PositiveIntegerField(default=0)
    metrics = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-snapshot_date"]
