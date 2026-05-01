from django.db import models

from Backend.EnterpriseCore.models import ExternalReference, TenantScopedModel


class LeadTag(TenantScopedModel):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=40, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="banao_lead_tag_per_tenant")]

    def __str__(self):
        return self.name


class LeadAccount(TenantScopedModel, ExternalReference):
    company_name = models.CharField(max_length=220)
    source = models.CharField(max_length=120, blank=True, db_index=True)
    stage = models.CharField(max_length=100, default="New", db_index=True)
    priority = models.CharField(max_length=40, default="Normal", db_index=True)
    owner = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.PROTECT, related_name="owned_leads")
    estimated_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=12, default="INR")
    website_url = models.URLField(blank=True)
    industry = models.CharField(max_length=120, blank=True, db_index=True)
    connection_id = models.CharField(max_length=255, blank=True, db_index=True)
    source_page_name = models.CharField(max_length=255, blank=True)
    source_page_url = models.URLField(blank=True)
    latest_comment = models.TextField(blank=True)
    next_follow_up_at = models.DateTimeField(null=True, blank=True)
    action_item = models.TextField(blank=True)
    tags = models.ManyToManyField("Banao.LeadTag", blank=True, related_name="leads")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "company_name"]
        indexes = [models.Index(fields=["tenant", "stage", "owner"])]

    def __str__(self):
        return self.company_name


class LeadContact(TenantScopedModel):
    lead = models.ForeignKey("Banao.LeadAccount", on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=180)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=60, blank=True)
    role = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["tenant_id", "lead_id", "name"]


class LeadActivity(TenantScopedModel):
    lead = models.ForeignKey("Banao.LeadAccount", on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="lead_activities")
    activity_type = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=220)
    note = models.TextField(blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class LeadNote(TenantScopedModel):
    lead = models.ForeignKey("Banao.LeadAccount", on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="lead_notes")
    title = models.CharField(max_length=220, blank=True)
    body = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class LeadTest(TenantScopedModel):
    lead = models.ForeignKey("Banao.LeadAccount", on_delete=models.CASCADE, related_name="tests")
    title = models.CharField(max_length=220)
    status = models.CharField(max_length=80, default="Pending", db_index=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class ProposalArtifact(TenantScopedModel, ExternalReference):
    lead = models.ForeignKey("Banao.LeadAccount", on_delete=models.CASCADE, related_name="proposals")
    title = models.CharField(max_length=220)
    status = models.CharField(max_length=80, default="Draft", db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class AuditArtifact(TenantScopedModel, ExternalReference):
    lead = models.ForeignKey("Banao.LeadAccount", on_delete=models.CASCADE, related_name="audits")
    title = models.CharField(max_length=220)
    status = models.CharField(max_length=80, default="Open", db_index=True)
    findings = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class WorkflowTransition(TenantScopedModel):
    lead = models.ForeignKey("Banao.LeadAccount", on_delete=models.CASCADE, related_name="workflow_transitions")
    from_stage = models.CharField(max_length=100, blank=True)
    to_stage = models.CharField(max_length=100, db_index=True)
    changed_by = models.ForeignKey("Users.EmployeeProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="lead_stage_changes")
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]


class WorkflowStatusHistory(TenantScopedModel):
    lead = models.ForeignKey("Banao.LeadAccount", on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=100, db_index=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=120, default="Pending", db_index=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "-created_at"]
