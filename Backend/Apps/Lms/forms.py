from django import forms

from Backend.Apps.Lms.models import LeadQueueSnapshot, LearningAssignment, LearningModule, LearningPath, RevenuePerformanceSnapshot


class LearningPathForm(forms.ModelForm):
    class Meta:
        model = LearningPath
        fields = ["title", "audience", "status", "metadata"]


class LearningModuleForm(forms.ModelForm):
    class Meta:
        model = LearningModule
        fields = ["path", "title", "sequence", "content_reference", "metadata"]


class LearningAssignmentForm(forms.ModelForm):
    class Meta:
        model = LearningAssignment
        fields = ["path", "employee", "status", "due_on", "completed_at", "progress_payload"]


class RevenuePerformanceSnapshotForm(forms.ModelForm):
    class Meta:
        model = RevenuePerformanceSnapshot
        fields = ["employee", "snapshot_date", "lead_count", "converted_count", "proposal_count", "score", "metrics"]


class LeadQueueSnapshotForm(forms.ModelForm):
    class Meta:
        model = LeadQueueSnapshot
        fields = ["employee", "snapshot_date", "open_count", "stale_count", "follow_up_due_count", "proposal_count", "metrics"]