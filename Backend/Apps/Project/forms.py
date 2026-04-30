from django import forms

from Backend.Apps.Project.models import DeliveryDocument, DeliveryMilestone, ProjectWorkspace, RepositoryLink, TeamAssignment


class ProjectWorkspaceForm(forms.ModelForm):
    class Meta:
        model = ProjectWorkspace
        fields = ["name", "code", "client_name", "description", "project_type", "priority", "status", "starts_on", "ends_on", "health", "github_organization", "clickup_sync_enabled", "terms_required", "anti_phishing_enabled", "metadata"]


class DeliveryMilestoneForm(forms.ModelForm):
    class Meta:
        model = DeliveryMilestone
        fields = ["project", "component", "title", "sequence", "status", "due_on", "completed_on", "bounty", "delayed_days", "acceptance_criteria"]


class TeamAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeamAssignment
        fields = ["project", "employee", "role", "allocation_percent", "starts_on", "ends_on", "terms_accepted_at", "github_access_status", "is_absent", "absent_reason", "status"]


class RepositoryLinkForm(forms.ModelForm):
    class Meta:
        model = RepositoryLink
        fields = ["project", "name", "owner", "full_name", "provider", "default_branch", "access_status", "metadata"]


class DeliveryDocumentForm(forms.ModelForm):
    class Meta:
        model = DeliveryDocument
        fields = ["project", "title", "document_type", "storage_reference", "file_id", "is_pinned", "status", "metadata"]